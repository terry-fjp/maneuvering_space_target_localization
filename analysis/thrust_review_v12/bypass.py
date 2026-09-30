"""Counterfactual no-range next-second replay; main decisions never changed."""
import json
import numpy as np
import control
from core import Tracker,rk4
from scenario import H,base,PREFIX,SET

def main():
 seed=260930401 if SET=='original' else 261001401;freq=10;z=base(freq,seed);cfg=control.configs('review_diagnostic');original=control.forecast;observe=Tracker.observe;clock=[0];last=np.zeros(192);records=[]
 guards=np.repeat([c['guard'] for c in cfg],64);req=np.repeat([c['req'] for c in cfg],64);margin=np.repeat([c['margin'] for c in cfg],64);indices=np.tile(np.arange(64),3)
 def hook_observe(self,u,r,o,use,*a,**kw):
  ret=observe(self,u,r,o,use,*a,**kw);last[use]=clock[0]/freq;clock[0]+=1;return ret
 def hook_forecast(f,o,ff):
  raw=original(f,o,ff);tick=clock[0];t=tick/freq
  if t<30 or t>=699:return raw
  branch=Tracker(f.x[:,:6].copy(),f.p[:,:6,:6].copy(),9);branch.x=f.x.copy();branch.p=f.p.copy();truth=z['states'][int(t),:,:6].copy();observer=z['states'][int(t),:,6:].copy();peak=np.zeros((192,2));active=f.forecast_q>1e-5
  for j in range(freq):
   if j:
    truth=rk4(truth,1/freq,z['forces'][int(t)]);observer=rk4(observer,1/freq);branch.predict(1/freq,active)
   observe(branch,z['um'][tick+j,indices],z['rm'][tick+j,indices],observer[indices],np.zeros(192,bool))
   er=np.linalg.norm(branch.x[:,:3]-truth[indices,:3],axis=1);ev=np.linalg.norm(branch.x[:,3:6]-truth[indices,3:6],axis=1);peak=np.maximum(peak,np.column_stack([er,ev]))
  protected=raw+np.column_stack([guards*(t+1-last),guards]);ratio=np.max(protected/np.column_stack([req,req/10])/margin[:,None],axis=1)
  records.append(np.column_stack([req,indices,np.full(192,t),raw,protected,peak,ratio]))
  return raw
 control.forecast=hook_forecast;Tracker.observe=hook_observe
 try:control.run(10,seed,'review_diagnostic')
 finally:control.forecast=original;Tracker.observe=observe
 data=np.concatenate(records);np.savez_compressed(H/'statistics'/f'bypass_{PREFIX or "original"}.npz',rows=data,columns=np.array(['req','target','time','raw_r','raw_v','guard_r','guard_v','true_max_r','true_max_v','decision_ratio']))
 # Main errors, resource and violations must be identical to the uninstrumented GP.
 a=json.loads((H/'results'/f'track_{PREFIX}review_diagnostic_10_{seed}.json').read_text())['rows'];p=H/'results'/f'track_{PREFIX}review_main_10_{seed}.json'
 if p.exists():
  b=json.loads(p.read_text())['rows']
  for r in a:
   rr=next(v for v in b if v['name']=='MSC-GP' and v['req']==r['req'] and v['target']==r['target'])
   for k in ['position_mse','velocity_mse','laser_time','bad']:assert r[k]==rr[k]
 print('BYPASS',SET,data.shape,flush=True)
if __name__=='__main__':main()
