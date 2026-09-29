import csv,json
from pathlib import Path
import numpy as np
from scenario import H,ACCELS
RNG=np.random.default_rng(260930999);BOOT=RNG.integers(0,64,(4000,64))
def dumpcsv(path,rows):
 if not rows:return
 with path.open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def agg(rr):
 return dict(n=len(rr),position_rmse=float(np.sqrt(np.mean([r['position_mse'] for r in rr]))),velocity_rmse=float(np.sqrt(np.mean([r['velocity_mse'] for r in rr]))),position_peak=max(r['position_peak'] for r in rr),velocity_peak=max(r['velocity_peak'] for r in rr),bad_arcs=sum(r['bad']>0 for r in rr),bad_fraction=float(np.mean([r['bad']/r['samples'] for r in rr])),longest_bad=max(r['longest_bad'] for r in rr),laser_time=float(np.mean([r['laser_time'] for r in rr])),laser_all_time=float(np.mean([r['laser_all_time'] for r in rr])),position_coverage=float(np.mean([r['position_coverage'] for r in rr])),velocity_coverage=float(np.mean([r['velocity_coverage'] for r in rr])),event_position_rmse=float(np.sqrt(np.mean([np.array(r['event_mse'])[:,0] for r in rr]))),event_velocity_rmse=float(np.sqrt(np.mean([np.array(r['event_mse'])[:,1] for r in rr]))),event_position_peak_mean=float(np.mean([np.array(r['event_peak'])[:,0] for r in rr])))
def effect(a,b):
 key=lambda r:(r['target'],r['freq'],r['seed'])
 a=sorted(a,key=key);b=sorted(b,key=key);assert [key(r) for r in a]==[key(r) for r in b]
 arrays=[]
 for rr in [a,b]:arrays.append(np.array([[np.mean([r[k] for r in rr if r['target']==t]) for k in ['position_mse','velocity_mse','laser_time']] for t in range(64)]))
 x,y=[v[BOOT].mean(1) for v in arrays];u,v=[v.mean(0) for v in arrays]
 ci=lambda a:np.percentile(a,[2.5,97.5]).tolist()
 return dict(position_difference=float(np.sqrt(u[0])-np.sqrt(v[0])),position_ci=ci(np.sqrt(x[:,0])-np.sqrt(y[:,0])),velocity_difference=float(np.sqrt(u[1])-np.sqrt(v[1])),velocity_ci=ci(np.sqrt(x[:,1])-np.sqrt(y[:,1])),time_difference=float(u[2]-v[2]),time_ci=ci(x[:,2]-y[:,2]),saving=float(100*(1-u[2]/v[2])),saving_ci=ci(100*(1-x[:,2]/y[:,2])))
def detection_agg(rr):
 tp=sum(r['tp'] for r in rr);fp=sum(r['fp'] for r in rr);fn=sum(r['fn'] for r in rr);ds=[d for r in rr for d in r['delays'] if d is not None]
 return dict(n_events=tp+fn,tp=tp,fp=fp,fn=fn,precision=tp/max(1,tp+fp),recall=tp/max(1,tp+fn),f1=2*tp/max(1,2*tp+fp+fn),delay_median=float(np.median(ds)) if ds else None,delay_p95=float(np.percentile(ds,95)) if ds else None,late=sum(r['late'] for r in rr),repeat=sum(r['repeat'] for r in rr),unassociated=sum(r['unassociated'] for r in rr))
def main():
 chosen=json.loads((H/'detector_choice.json').read_text())['detector'];rows=[];est=[];det=[]
 for freq in [5,10,15,20]:
  for seed in [260930401,260930402,260930403]:
   rows+=json.loads((H/'results'/f'track_main_{freq}_{seed}.json').read_text())['rows'];est+=json.loads((H/'results'/f'estimators_{freq}_{seed}.json').read_text())['rows'];det+=json.loads((H/'results'/f'detect_{freq}_{seed}_0.json').read_text())['rows']
 summary=[];effects=[];strata=[];estim=[];esteffects=[]
 for req in [500,1000,1500]:
  get=lambda name:[r for r in rows if r['req']==req and r['name']==name]
  for name in ['MSC-GP','Periodic','RIT','NoGuard','SS8-GP']:
   rr=get(name);summary.append(dict(req=req,name=name,**agg(rr)))
   for axis,vals in [('freq',[5,10,15,20]),('level',range(8)),('range_bin_km',[500,1000,1500,2000])]:
    for v in vals:strata.append(dict(req=req,name=name,axis=axis,value=v,**agg([r for r in rr if r[axis]==v])))
  for b in ['Periodic','RIT','NoGuard','SS8-GP']:effects.append(dict(req=req,a='MSC-GP',b=b,**effect(get('MSC-GP'),get(b))))
  for source in ['MSC-GP','Periodic']:
   estim.append(dict(req=req,source=source,name='MSC-GP estimator',**agg(get(source))))
   for name in ['EKF','IMM-EKF']:
    rr=[r for r in est if r['req']==req and r['source']==source and r['name']==name];estim.append(dict(req=req,source=source,name=name,**agg(rr)));esteffects.append(dict(req=req,source=source,a='MSC-GP estimator',b=name,**effect(get(source),rr)))
 detections=[dict(name=name,**detection_agg([r for r in det if r['detector']==name])) for name in [chosen,'SS2','SS8','SS30']];dstrata=[];deffects=[]
 for name in [chosen,'SS2','SS8','SS30']:
  for axis,vals in [('freq',[5,10,15,20]),('level',range(8)),('range_bin_km',[500,1000,1500,2000])]:
   for v in vals:dstrata.append(dict(name=name,axis=axis,value=v,**detection_agg([r for r in det if r['detector']==name and r[axis]==v])))
 for name in ['SS2','SS8','SS30']:
  aa=[r for r in det if r['detector']==chosen];bb=[r for r in det if r['detector']==name];blocks=[]
  for rr in [aa,bb]:blocks.append(np.array([[sum(r[k] for r in rr if r['target']==t) for k in ['tp','fp','fn']] for t in range(64)]))
  f1=lambda v:2*v[...,0]/np.maximum(1,2*v[...,0]+v[...,1]+v[...,2]);rec=lambda v:v[...,0]/np.maximum(1,v[...,0]+v[...,2])
  xx,yy=[v[BOOT].sum(1) for v in blocks];a,b=[v.sum(0) for v in blocks];by={ (r['target'],r['freq'],r['seed']):r for r in bb};deltas=[]
  for r in aa:
   q=by[(r['target'],r['freq'],r['seed'])]
   for x,y in zip(r['delays'],q['delays']):
    if x is not None and y is not None:deltas.append(x-y)
  deffects.append(dict(a=chosen,b=name,f1_difference=float(100*(f1(a)-f1(b))),f1_ci=np.percentile(100*(f1(xx)-f1(yy)),[2.5,97.5]).tolist(),recall_difference=float(100*(rec(a)-rec(b))),recall_ci=np.percentile(100*(rec(xx)-rec(yy)),[2.5,97.5]).tolist(),common=len(deltas),delay_difference=float(np.mean(deltas))))
 null=[]
 for freq in [5,10,15,20]:
  cal=json.loads((H/'calibration'/f'detect_{freq}.json').read_text());nr=json.loads((H/'results'/f'detect_{freq}_260930002_1.json').read_text())['rows'];exp=cal['exposure_hours']
  for name in [chosen,'SS2','SS8','SS30']:
   counts=np.array([next(r['fp'] for r in nr if r['detector']==name and r['target']==t) for t in range(64)]);ci=np.percentile(counts[BOOT].sum(1)/exp,[2.5,97.5]).tolist()
   null.append(dict(freq=freq,name=name,threshold=cal['thresholds'][name],calibration_count=cal['calibration_counts'][name],check_count=int(counts.sum()),exposure=exp,rate=float(counts.sum()/exp),ci=ci))
 out=dict(tracking=summary,effects=effects,estimators=estim,estimator_effects=esteffects,detection=detections,detection_effects=deffects,null=null)
 (H/'statistics/summary.json').write_text(json.dumps(out,indent=2));dumpcsv(H/'statistics/tracking_summary.csv',summary);dumpcsv(H/'statistics/estimator_summary.csv',estim);dumpcsv(H/'statistics/tracking_strata.csv',strata);dumpcsv(H/'statistics/detection_strata.csv',dstrata);dumpcsv(H/'statistics/trajectories.csv',rows);dumpcsv(H/'statistics/estimator_trajectories.csv',est);dumpcsv(H/'statistics/detection_records.csv',det)
 print('Base statistics summarized')
if __name__=='__main__':main()
