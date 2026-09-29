import argparse,json
import numpy as np
from scipy.linalg import expm
from core import Tracker,IMM,rk4,RISK_CHI2
from scenario import H,base,initial,DURATION
class EKF(Tracker):
 def __init__(self,x,p,q):super().__init__(x,p,6);self.qv=np.asarray(q)
 def predict(self,dt):
  super().predict(dt)
  self.p+=(self.qv-1e-6)[:,None,None]*np.kron(np.array([[dt**3/3,dt**2/2],[dt**2/2,dt]]),np.eye(3))
def run(freq,seed,development=False):
 z=base(freq,seed);meta=initial(seed)[0];main=json.loads((H/'results'/f'track_main_{freq}_{seed}.json').read_text());data=np.load(H/'results'/f'track_main_{freq}_{seed}.npz');sources=[i for i,c in enumerate(main['configs']) if c['name'] in ['MSC-GP','Periodic']]
 n=64;s=len(sources);idx=np.tile(np.arange(n),s);x=np.tile(z['x0'],(s,1));p=np.tile(z['p0'],(s,1,1))
 if development:settings=[('EKF',q) for q in [1e-6,1e-4,1e-2,1]]+[('IMM-EKF',q) for q in [.25,1,4]]
 else:
  sel=json.loads((H/'estimator_choice.json').read_text());settings=[(name,sel[name]) for name in ['EKF','IMM-EKF']]
 filters=[]
 for name,q in settings:
  if name=='EKF':filters.append(EKF(x.copy(),p.copy(),np.full(s*n,q)))
  else:
   imm=IMM(x.copy(),p.copy())
   for f in imm.filters:f.q*=q
   filters.append(imm)
 c=len(settings);sum2=np.zeros((c,s*n,2));peaks=sum2.copy();bad=np.zeros((c,s*n),int);runbad=bad.copy();maxrun=bad.copy();coverage=np.zeros((c,s*n,2),int)
 req=np.repeat([main['configs'][j]['req'] for j in sources],n);truth=z['states'][0,:,:6].copy();obs=z['states'][0,:,6:].copy()
 events=np.zeros((c,s*n,3,2));eventpeak=events.copy();raw=np.zeros((670*freq,c,s*n,2),np.float32) if not development else None
 for tick in range(700*freq):
  t=tick/freq;sec=tick//freq
  if tick:
   truth=rk4(truth,1/freq,z['forces'][(tick-1)//freq]);obs=rk4(obs,1/freq)
   for f in filters:f.predict(1/freq)
  if tick%freq==0:truth=z['states'][sec,:,:6].copy();obs=z['states'][sec,:,6:].copy()
  use=data['use'][tick,sources].reshape(-1)
  for j,f in enumerate(filters):
   f.observe(z['um'][tick,idx],z['rm'][tick,idx],obs[idx],use)
   delta=np.stack([f.x[:,:3]-truth[idx,:3],f.x[:,3:6]-truth[idx,3:]],axis=1);e=np.linalg.norm(delta,axis=2)
   if t>=30:
    sum2[j]+=e**2;peaks[j]=np.maximum(peaks[j],e);bb=np.any(e>np.column_stack([req,req/10]),axis=1);bad[j]+=bb;runbad[j]=np.where(bb,runbad[j]+1,0);maxrun[j]=np.maximum(maxrun[j],runbad[j])
    if raw is not None:raw[tick-30*freq,j]=e
    for k in range(2):
     pp=f.p[:,3*k:3*k+3,3*k:3*k+3];quad=np.einsum('ni,ni->n',delta[:,k],np.linalg.solve(pp,delta[:,k,:,None])[:,:,0]);coverage[j,:,k]+=quad<=RISK_CHI2
   for k,tau in enumerate([100,300,500]):
    if tau<=t<tau+DURATION:events[j,:,k]+=e**2;eventpeak[j,:,k]=np.maximum(eventpeak[j,:,k],e)
 rows=[]
 for j,(name,q) in enumerate(settings):
  for k,src in enumerate(sources):
   conf=main['configs'][src]
   for i,m in enumerate(meta):
    a=k*n+i;rr=next(r for r in main['rows'] if r['name']==conf['name'] and r['req']==conf['req'] and r['target']==i)
    rows.append(dict(m,name=name,q=q,source=conf['name'],req=conf['req'],freq=freq,seed=seed,samples=670*freq,position_mse=float(sum2[j,a,0]/(670*freq)),velocity_mse=float(sum2[j,a,1]/(670*freq)),position_peak=float(peaks[j,a,0]),velocity_peak=float(peaks[j,a,1]),bad=int(bad[j,a]),longest_bad=float(maxrun[j,a]/freq),laser_time=rr['laser_time'],laser_all_time=rr['laser_all_time'],position_coverage=float(coverage[j,a,0]/(670*freq)),velocity_coverage=float(coverage[j,a,1]/(670*freq)),event_mse=(events[j,a]/(DURATION*freq)).tolist(),event_peak=eventpeak[j,a].tolist()))
 stem=H/'results'/f'estimators_{freq}_{seed}';stem.with_suffix('.json').write_text(json.dumps(dict(rows=rows,settings=settings,sources=sources),indent=2))
 if raw is not None:np.savez_compressed(stem.with_suffix('.npz'),error=raw)
 if development:
  selected={};candidates=[]
  for name,q in settings:
   rr=[r for r in rows if r['name']==name and r['q']==q];candidates.append(dict(name=name,q=q,rmse=float(np.sqrt(np.mean([r['position_mse'] for r in rr])))))
  for name in ['EKF','IMM-EKF']:selected[name]=min([c for c in candidates if c['name']==name],key=lambda c:c['rmse'])['q']
  (H/'estimator_choice.json').write_text(json.dumps(dict(selected,candidates=candidates,rule='minimum pooled development position RMSE over three tasks and both fixed measurement sequences'),indent=2))
 print('ESTIMATORS',freq,seed,len(rows),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--freq',type=int,required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--development',action='store_true');a=p.parse_args();run(a.freq,a.seed,a.development)
