"""Dependency and algorithm smoke check, no existing caches or result files."""
import json
import numpy as np
from scenario import initial,ACCELS,DURATION
from core import Tracker,IMM,rk4,observations
from detect import white
meta,x,o,x0,p=initial(77);x=x[:8];o=o[:8];x0=x0[:8];p=p[:8];f=Tracker(x0.copy(),p.copy(),9);g=IMM(x0.copy(),p.copy());rng=np.random.default_rng(987)
for k in range(20):
 x=rk4(x,.1,np.tile([.01,0,0],(8,1)));o=rk4(o,.1);u,r=observations(x,o,rng);f.predict(.1,np.zeros(8,bool));g.predict(.1);use=np.full(8,k%3==0);f.observe(u,r,o,use);g.observe(u,r,o,use)
 assert np.isfinite(f.x).all() and np.isfinite(g.x).all()
 assert np.linalg.eigvalsh(f.p).min()>-1e-9 and np.linalg.eigvalsh(g.p).min()>-1e-9
 assert np.allclose(g.w.sum(1),1)
b=np.array([[[1.,0,0],[0,1,0]]]);S=np.array([[[2.,.2],[.2,1.]]]);y=np.array([[1.,2.]]);U=np.array([[0.,-1.],[1.,0.]])
assert np.allclose(white(y,S,b),white(y@U.T,U@S@U.T,U@b))
assert DURATION==60 and len(ACCELS)==8
print(json.dumps(dict(status='PASS',targets=8,steps=20,duration=DURATION,acceleration_levels=ACCELS,position_checksum=float(f.x[:,:3].sum()),imm_checksum=float(g.x[:,:3].sum())),indent=2))
