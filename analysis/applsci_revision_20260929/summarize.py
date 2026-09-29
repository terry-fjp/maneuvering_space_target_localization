from pathlib import Path
import json,sys,csv
import numpy as np
D=Path(__file__).resolve().parent;H=D.parent/'thrust_review_v12';sys.path.insert(0,str(H))
from statistics_utils import agg
BOOT=np.random.default_rng(260929).integers(0,64,(4000,64))
def rows(pattern):
 out=[]
 for p in sorted((D/'results').glob(pattern)):out+=json.loads(p.read_text())['rows']
 return out
def stats(rr):
 a=agg(rr);a.update(targets=len({r['target'] for r in rr}),bad_targets=len({r['target'] for r in rr if r['bad']}),request_time=float(np.mean([r['request_time'] for r in rr])),request_windows=float(np.mean([r['request_windows'] for r in rr])),max_gap=max(r['max_gap'] for r in rr),position_peak_quantiles=np.percentile([r['position_peak'] for r in rr],[0,25,50,75,95,99,100]).tolist(),velocity_peak_quantiles=np.percentile([r['velocity_peak'] for r in rr],[0,25,50,75,95,99,100]).tolist(),failed_records=[{k:r[k] for k in ['target','freq','seed','position_peak','velocity_peak','longest_bad']} for r in rr if r['bad']]);return a
def paired(a,b):
 key=lambda r:(r['target'],r['freq'],r['seed']);a=sorted(a,key=key);b=sorted(b,key=key);assert [key(r) for r in a]==[key(r) for r in b]
 aa=[]
 for rr in [a,b]:aa.append(np.array([[np.mean([r['laser_time'] for r in rr if r['target']==i]),max(r['position_peak'] for r in rr if r['target']==i),np.mean([r['bad']>0 for r in rr if r['target']==i]),np.mean([r['position_mse'] for r in rr if r['target']==i])] for i in range(64)]))
 diff=aa[0]-aa[1];out={}
 for i,k in enumerate(['time','target_peak','bad_fraction']):out[k]=dict(difference=float(diff[:,i].mean()),ci=np.percentile(diff[BOOT,i].mean(1),[2.5,97.5]).tolist())
 out['rmse']=dict(difference=float(np.sqrt(aa[0][:,3].mean())-np.sqrt(aa[1][:,3].mean())),ci=np.percentile(np.sqrt(aa[0][BOOT,3].mean(1))-np.sqrt(aa[1][BOOT,3].mean(1)),[2.5,97.5]).tolist());return out
out={'validation':[],'paired':[],'outages':[],'checks':{}}
allrows=rows('track_*validation*.json');assert len(allrows)==6*19*64
for ds in ['original','unseen_']:
 rr=[r for r in allrows if r['dataset']==ds]
 for req in [500,1000,1500]:
  for name in sorted({r['name'] for r in rr if r['req']==req}):
   vv=[r for r in rr if r['req']==req and r['name']==name];assert len(vv)==192
   out['validation'].append(dict(dataset=ds,req=req,name=name,**stats(vv)))
   if name!='MSC-GP':out['paired'].append(dict(dataset=ds,req=req,baseline=name,**paired([r for r in rr if r['req']==req and r['name']=='MSC-GP'],vv)))
 # Frozen full configuration must be unchanged, all metrics.
 old=[]
 for seed in ([260930401,260930402,260930403] if ds=='original' else [261001401,261001402,261001403]):
  prefix='' if ds=='original' else ds
  old+=json.loads((H/'results'/f'track_{prefix}review_main_10_{seed}.json').read_text())['rows']
 for r in rr:
  if r['name'] not in ['MSC-GP','Neither']:continue
  q=next(v for v in old if v['name']==('MSC-GP' if r['name']=='MSC-GP' else 'NoAlarm') and all(v[k]==r[k] for k in ['target','seed','req']))
  for k in ['position_mse','velocity_mse','position_peak','velocity_peak','bad','laser_time','request_time']:assert r[k]==q[k],(ds,r['name'],k,r[k],q[k])
replay_files=list((D/'results').glob('track_*validation*.npz'))
assert replay_files, 'Restore the optional ValidationSamples archive or run frozen validation before checking replay masks.'
for p in replay_files:
 z=np.load(p);cfg=json.loads(p.with_suffix('.json').read_text())['configs']
 for req in [500,1000,1500]:
  a=next(i for i,c in enumerate(cfg) if c['req']==req and c['name']=='MSC-GP');b=next(i for i,c in enumerate(cfg) if c['req']==req and c['name']=='ReplayNoAdapt');assert np.array_equal(z['use'][:,a],z['use'][:,b])
out['checks']['full_and_neither_match_frozen_exactly']=True;out['checks']['replay_effective_sequences_identical']=True
orows=rows('track_outages*.json');assert len(orows)==30*6*64
for req in [500,1000]:
 for method in ['MSC-GP','Periodic','Constant']:
  for length in [10,30]:
   for offset in [-20,0,20,30,50]:
    rr=[r for r in orows if r['req']==req and r['method']==method and r['outage']==length and r['offset']==offset];assert len(rr)==192
    out['outages'].append(dict(req=req,method=method,length=length,offset=offset,**stats(rr)))
old=[]
for p in (H/'results').glob('track_review_service_10_*.json'):old+=json.loads(p.read_text())['rows']
for r in orows:
 if r['offset']!=-20:continue
 q=next(x for x in old if x['name']==r['method']+'|gap'+str(r['outage']) and all(x[k]==r[k] for k in ['target','seed','req']))
 for k in ['position_mse','velocity_mse','position_peak','laser_time','bad','request_time','max_gap']:assert r[k]==q[k]
out['checks']['minus20_outage_reproduces_original_case']=True
out['forecast']=sum([json.loads(p.read_text()) for p in sorted((D/'results').glob('forecast_signed_*.json'))],[]);assert len(out['forecast'])==12
(D/'summary.json').write_text(json.dumps(out,indent=2))
for k in ['validation','outages','paired']:
 print('\n',k)
 for r in out[k]:
  if k=='validation':print(r['dataset'],r['req'],r['name'],*[round(r[x],3) for x in ['position_rmse','velocity_rmse','position_peak','velocity_peak','laser_time']],r['bad_arcs'],r['bad_targets'])
  if k=='outages' and r['method']=='MSC-GP':print(r['req'],r['length'],r['offset'],r['bad_arcs'],r['bad_targets'],round(r['position_peak'],1),r['longest_bad'],round(r['request_time'],2),round(r['laser_time'],2),r['max_gap'])
  if k=='paired' and r['req']==1000 and r['baseline'] in ['PositiveAdd','PositiveScale','ReplayNoAdapt']:print(r)
print('FORECAST',out['forecast'])
