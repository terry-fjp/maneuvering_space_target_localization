"""Read-only instrumentation: same-state sequential forecast, unchanged decisions."""
import argparse,json
import numpy as np
import control
from core import Tracker,rk4,basis,gravity_jacobian,SIGMA_ANGLE,confidence_bounds
from scenario import H
def sequential(f,o,freq):
 x=f.x.copy();p=f.p.copy();oo=o.copy();dt=1/freq;mx=np.zeros((len(x),2))
 for j in range(freq):
  d=x[:,:3]-oo[:,:3];rr=np.linalg.norm(d,axis=1);b=basis(d/rr[:,None]);h=np.zeros((len(x),2,9));h[:,:,:3]=b/rr[:,None,None]
  hp=h@p;K=np.linalg.solve(hp@h.transpose(0,2,1)+np.eye(2)*SIGMA_ANGLE**2,hp).transpose(0,2,1);p-=K@hp;p=(p+p.transpose(0,2,1))/2;mx=np.maximum(mx,confidence_bounds(p))
  F=np.zeros_like(p);F[:,:3,3:6]=np.eye(3);F[:,3:6,:3]=gravity_jacobian(x[:,:3]);F[:,3:6,6:]=np.eye(3);phi=np.eye(9)+F*dt+F@F*dt**2/2
  small=np.array([[dt**5/20,dt**4/8,dt**3/6],[dt**4/8,dt**3/3,dt**2/2],[dt**3/6,dt**2/2,dt]])
  p=phi@p@phi.transpose(0,2,1)+f.forecast_q[:,None,None]*np.kron(small,np.eye(3));x[:,:6]=rk4(x[:,:6],dt,x[:,6:]);oo=rk4(oo,dt)
 end=confidence_bounds(p);return end,np.maximum(mx,end)
def run(freq):
 configs=[c for c in control.configs('main') if c['name']=='MSC-GP'];original_configs=control.configs;control.configs=lambda group:configs
 original_forecast=control.forecast;original_observe=Tracker.observe;clock=[0];last=np.zeros(192);records=[]
 guard=np.repeat([c['guard'] for c in configs],64);limits=np.repeat(np.array([[c['req'],c['req']/10] for c in configs])*np.array([c['margin'] for c in configs])[:,None],64,axis=0)
 def observe(self,um,rho,o,use_range,*args,**kw):
  result=original_observe(self,um,rho,o,use_range,*args,**kw)
  last[use_range]=clock[0]/freq;clock[0]+=1;return result
 def forecast(f,o,ff):
  bb=original_forecast(f,o,ff);t=clock[0]/freq
  if t>=30 and int(t)%10==0:
   end,mx=sequential(f,o,ff);g=np.column_stack([guard*(t+1-last),guard]);a=np.any(bb+g>limits,axis=1);b=np.any(mx+g>limits,axis=1)
   records.append(np.column_stack([np.repeat([500,1000,1500],64),np.abs(bb-end)/np.maximum(end,1e-12)*100,a!=b,(~a)&b]))
  return bb
 Tracker.observe=observe;control.forecast=forecast
 try:control.run(freq,260930401,'diagnostic')
 finally:Tracker.observe=original_observe;control.forecast=original_forecast;control.configs=original_configs
 a=json.loads((H/'results'/f'track_diagnostic_{freq}_260930401.json').read_text())['rows'];b=json.loads((H/'results'/f'track_main_{freq}_260930401.json').read_text())['rows']
 for r in a:
  q=next(x for x in b if x['name']=='MSC-GP' and x['req']==r['req'] and x['target']==r['target'])
  for k in ['position_mse','velocity_mse','laser_time','bad']:assert r[k]==q[k],(k,r[k],q[k])
 d=np.concatenate(records);out=[]
 for req in [500,1000,1500]:
  v=d[d[:,0]==req];out.append(dict(freq=freq,req=req,n=len(v),position_relative_p95=float(np.percentile(v[:,1],95)),velocity_relative_p95=float(np.percentile(v[:,2],95)),decision_mismatch_percent=float(100*v[:,3].mean()),compact_off_reference_on_percent=float(100*v[:,4].mean())))
 (H/'statistics'/f'forecast_{freq}.json').write_text(json.dumps(out,indent=2));print(out,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--freq',type=int,required=True);a=p.parse_args();run(a.freq)
