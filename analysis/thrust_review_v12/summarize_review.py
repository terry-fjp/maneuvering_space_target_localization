import json,csv
import numpy as np
from scenario import H
from statistics_utils import agg,effect,detection_agg,dumpcsv,BOOT

def readrows(pattern):
 out=[]
 for p in sorted((H/'results').glob(pattern)):out+=json.loads(p.read_text())['rows']
 return out

def main():
 out={};allrows=[];mainstats=[];effects=[]
 for dataset,prefix in [('original',''),('unseen','unseen_')]:
  rows=readrows(f'track_{prefix}review_main_*.json');assert len(rows)==13824,(dataset,len(rows));allrows+=rows
  for req in [500,1000,1500]:
   get=lambda n:[r for r in rows if r['req']==req and r['name']==n]
   for name in ['MSC-GP','Periodic','RIT-fine','Constant','Constant50','NoAlarm']:
    a=agg(get(name));a.update(request_time=float(np.mean([r['request_time'] for r in get(name)])),request_windows=float(np.mean([r['request_windows'] for r in get(name)])));mainstats.append(dict(dataset=dataset,req=req,name=name,**a))
   for name in ['Periodic','RIT-fine','Constant','Constant50','NoAlarm']:effects.append(dict(dataset=dataset,req=req,a='MSC-GP',b=name,**effect(get('MSC-GP'),get(name))))
 out['tracking']=mainstats;out['effects']=effects;dumpcsv(H/'statistics/review_trajectories.csv',allrows)
 service=readrows('track_review_service_*.json');assert len(service)==16128,len(service);ss=[]
 for req in [500,1000,1500]:
  for name in sorted({r['name'] for r in service}):
   rr=[r for r in service if r['req']==req and r['name']==name];a=agg(rr);a.update(request_time=float(np.mean([r['request_time'] for r in rr])),request_windows=float(np.mean([r['request_windows'] for r in rr])));ss.append(dict(req=req,name=name,**a))
 out['service']=ss;dumpcsv(H/'statistics/service_trajectories.csv',service)
 bypass=[]
 for dataset,key in [('original','original'),('unseen','unseen_')]:
  z=np.load(H/'statistics'/f'bypass_{key}.npz')['rows']
  for req in [500,1000,1500]:
   rr=z[z[:,0]==req]
   for group,mask in [('all',np.ones(len(rr),bool)),('near',(rr[:,9]>=.8)&(rr[:,9]<=1.2)),('off',rr[:,9]<=1)]:
    d=rr[mask];a=dict(dataset=dataset,req=req,group=group,n=len(d))
    for j,dim in enumerate(['position','velocity']):
     actual=d[:,7+j];raw=d[:,3+j];protected=d[:,5+j];under=np.maximum(actual-protected,0)
     a.update({dim+'_raw_under_percent':float(100*np.mean(actual>raw)),dim+'_guard_under_percent':float(100*np.mean(actual>protected)),dim+'_guard_under_p95':float(np.percentile(under,95)),dim+'_guard_under_max':float(under.max()),dim+'_guard_under_conditional_p95':float(np.percentile(under[under>0],95)) if np.any(under>0) else None,dim+'_truth_over_percent':float(100*np.mean(actual>(req if j==0 else req/10)))})
    a['off_unsafe']=int(np.sum((d[:,9]<=1)&np.any(d[:,7:9]>[req,req/10],axis=1)));bypass.append(a)
 out['bypass']=bypass
 detold=readrows('detect_[0-9]*_2609304*_0.json');detunseen=readrows('detect_unseen_*_2610014*_0.json');dets=[];ds=[]
 geometry=list(csv.DictReader((H/'data/targets.csv').open()));rates=np.array([float(r['los_rate_deg_s']) for r in geometry]);edges=np.quantile(rates,[.25,.5,.75]);geo=np.searchsorted(edges,rates)
 for dataset,rows in [('original',detold),('unseen',detunseen)]:
  for name in ['MSC16','SS2','SS8','SS30']:dets.append(dict(dataset=dataset,name=name,**detection_agg([r for r in rows if r['detector']==name])))
  for baseline in ['SS2','SS8','SS30']:
   a=[r for r in rows if r['detector']=='MSC16'];b={(r['target'],r['freq'],r['seed']):r for r in rows if r['detector']==baseline};diffs=[[] for _ in range(64)]
   for r in a:
    q=b[(r['target'],r['freq'],r['seed'])]
    for x,y in zip(r['delays'],q['delays']):
     if x is not None and y is not None:diffs[r['target']].append(x-y)
   sums=np.array([sum(x) for x in diffs]);count=np.array([len(x) for x in diffs]);sample=sums[BOOT].sum(1)/np.maximum(1,count[BOOT].sum(1));ds.append(dict(dataset=dataset,baseline=baseline,common=int(count.sum()),difference=float(sums.sum()/count.sum()),ci=np.percentile(sample,[2.5,97.5]).tolist()))
 out['detection']=dets;out['delay_differences']=ds
 budget=json.loads((H/'statistics/budget_records.json').read_text());curve=[];strata=[];exp=3*64*640/3600
 for name in sorted({r['detector'] for r in budget}):
  null=[r for r in budget if r['detector']==name and not r['delays']];rr=[r for r in budget if r['detector']==name and r['delays']];counts=np.array([sum(r['fp'] for r in null if r['target']==t) for t in range(64)]);rates_ci=np.percentile(counts[BOOT].sum(1)/exp,[2.5,97.5]);curve.append(dict(name=name,exposure=exp,null_count=int(counts.sum()),rate=float(counts.sum()/exp),rate_ci=rates_ci.tolist(),**detection_agg(rr)))
  events=[]
  for r in rr:
   for j,delay in enumerate(r['delays']):events.append(dict(target=r['target'],axis=(r['target']//4+j)%3,range=r['range_bin_km'],geometry=int(geo[r['target']]),delay=delay))
  for axis,values in [('axis',[0,1,2]),('range',[500,1000,1500,2000]),('geometry',[0,1,2,3])]:
   for v in values:
    ee=[e for e in events if e[axis]==v];ok=[e['delay'] for e in ee if e['delay'] is not None];strata.append(dict(name=name,axis=axis,value=v,n=len(ee),tp=len(ok),recall=len(ok)/len(ee),delay_median=float(np.median(ok)) if ok else None))
 out['budget_curves']=curve;out['budget_strata']=strata;out['geometry_rate_edges']=edges.tolist()
 (H/'statistics/review_summary.json').write_text(json.dumps(out,indent=2));dumpcsv(H/'statistics/review_summary.csv',mainstats);dumpcsv(H/'statistics/service_summary.csv',ss);dumpcsv(H/'statistics/bypass_summary.csv',bypass);dumpcsv(H/'statistics/budget_strata.csv',strata)
 print('SUMMARIZED',len(allrows),len(service),flush=True)
if __name__=='__main__':main()
