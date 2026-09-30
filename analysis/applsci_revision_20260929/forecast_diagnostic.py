import sys,json
from pathlib import Path
import numpy as np
D=Path(__file__).resolve().parent;H=D.parent/'thrust_review_v12';sys.path.insert(0,str(H))
import extended_control as c
from forecast_check import sequential
from core import Tracker
freq=int(sys.argv[1]);cfg=[q for q in c.configs('main') if q['name']=='MSC-GP'];c.configs=lambda _:cfg;c.H=D
original_forecast=c.forecast;observe=Tracker.observe;clock=[0];last=np.zeros(192);records=[]
g=np.repeat([q['guard'] for q in cfg],64);limits=np.repeat(np.array([[q['req'],q['req']/10] for q in cfg])*np.array([q['margin'] for q in cfg])[:,None],64,axis=0)
def track(self,um,rho,o,use,*args,**kwargs):
 r=observe(self,um,rho,o,use,*args,**kwargs);last[use]=clock[0]/freq;clock[0]+=1;return r
def forecast(f,o,ff):
 bb=original_forecast(f,o,ff);t=clock[0]/freq
 if t>=30 and int(t)%10==0:
  end,mx=sequential(f,o,ff);guard=np.column_stack([g*(t+1-last),g]);a=np.any(bb+guard>limits,axis=1);b=np.any(mx+guard>limits,axis=1)
  records.append(np.column_stack([np.repeat([500,1000,1500],64),np.full(192,t),np.tile(np.arange(64),3),(end-bb)/np.maximum(end,1e-12)*100,(~a)&b,a&(~b)]))
 return bb
Tracker.observe=track;c.forecast=forecast;c.run(freq,260930401,'forecast')
a=json.loads((D/'results'/f'track_forecast_{freq}_260930401.json').read_text())['rows'];b=json.loads((H/'results'/f'track_main_{freq}_260930401.json').read_text())['rows']
for r in a:
 q=next(x for x in b if x['name']=='MSC-GP' and x['req']==r['req'] and x['target']==r['target'])
 for k in ['position_mse','velocity_mse','position_peak','laser_time','bad']:assert r[k]==q[k],(k,r[k],q[k])
d=np.concatenate(records);np.savez_compressed(D/'results'/f'forecast_signed_{freq}.npz',rows=d)
out=[]
for req in [500,1000,1500]:
 v=d[d[:,0]==req];out.append(dict(freq=freq,req=req,n=len(v),position_under_max=float(max(0,v[:,3].max())),velocity_under_max=float(max(0,v[:,4].max())),position_under_p99=float(np.percentile(np.maximum(v[:,3],0),99)),velocity_under_p99=float(np.percentile(np.maximum(v[:,4],0),99)),off_on=int(v[:,5].sum()),on_off=int(v[:,6].sum()),mismatched_starts=v[(v[:,5]+v[:,6])>0].tolist()))
(D/'results'/f'forecast_signed_{freq}.json').write_text(json.dumps(out,indent=2));print(out)
