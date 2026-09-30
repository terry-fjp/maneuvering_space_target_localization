import csv,json
from pathlib import Path
import numpy as np
from scenario import H,ACCELS
RNG=np.random.default_rng(260930999);BOOT=RNG.integers(0,64,(4000,64))
def dumpcsv(path,rows):
 if not rows:return
 with path.open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
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
