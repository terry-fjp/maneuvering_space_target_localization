from pathlib import Path
import csv,json,os
import numpy as np
from core import observations,rk4,basis
H=Path(__file__).resolve().parent
SET=os.environ.get("MSC_SET","original")
PREFIX="" if SET=="original" else "unseen_"
EVENTS=[100,300,500]
ACCELS=[.01,.03,.06,.09,.12,.15,.18,.2]
DURATION=60
def initial(seed):
 rows=list(csv.DictReader((H/'data'/('targets.csv' if SET=='original' else 'unseen_targets.csv')).open()))
 meta=[dict(target=int(r['target']),norad=r['norad'],range_bin_km=int(r['range_bin_km']),level=int(r['target'])%8 if SET=='original' else -1,kind='thrust') for r in rows]
 truth=np.array([[float(r[f'x{j}']) for j in range(6)] for r in rows]);obs=np.array([[float(r[f'o{j}']) for j in range(6)] for r in rows])
 rng=np.random.default_rng(seed);x=truth+rng.normal(size=truth.shape)*np.r_[np.ones(3)*1000/np.sqrt(3),np.ones(3)*100/np.sqrt(3)]
 p=np.tile(np.diag(np.r_[np.ones(3)*1e6/3,np.ones(3)*1e4/3]),(len(x),1,1))
 return meta,truth,obs,x,p
def event_plan():
 if SET=='unseen':
  p=json.loads((H/'data/unseen_plan.json').read_text());return np.array(p['times']),np.array(p['levels']),np.array(p['axes'])
 return np.tile(EVENTS,(64,1)),np.tile((np.arange(64)%8)[:,None],(1,3)),(np.arange(64)[:,None]//4+np.arange(3)[None,:])%3

def base(freq,seed,null=False):
 path=H/'cache'/f'base_{PREFIX}{freq}_{seed}_{int(null)}.npz'
 if path.exists():return dict(np.load(path))
 meta,truth,obs,x,p=initial(seed);n=len(x);rng=np.random.default_rng(seed+10000);times,levels,axes=event_plan()
 states=np.zeros((700,n,12));forces=np.zeros((700,n,3));um=np.zeros((700*freq,n,3));rm=np.zeros((700*freq,n));force=np.zeros((n,3));events=[]
 for tick in range(700*freq):
  if tick:truth=rk4(truth,1/freq,force);obs=rk4(obs,1/freq)
  sec=tick//freq
  if tick%freq==0:
   if not null:
    force[np.any(sec==times+DURATION,axis=1)]=0
    for i,j in np.argwhere(times==sec):
     d=truth[i:i+1,:3]-obs[i:i+1,:3];u=d/np.linalg.norm(d,axis=1)[:,None];b=basis(u);direction=[u[0],b[0,0],b[0,1]][axes[i,j]];force[i]=direction*ACCELS[levels[i,j]]
     events.append(dict(meta[i],event=int(j),time=sec,duration=DURATION,acceleration=ACCELS[levels[i,j]],event_level=int(levels[i,j]),direction=direction.tolist(),direction_axis=int(axes[i,j])))
   states[sec]=np.concatenate([truth,obs],axis=1);forces[sec]=force
  um[tick],rm[tick]=observations(truth,obs,rng)
 z=dict(x0=x,p0=p,states=states,forces=forces,um=um,rm=rm)
 np.savez_compressed(path,**z);path.with_suffix('.json').write_text(json.dumps(dict(meta=meta,events=events,freq=freq,seed=seed,null=null,dataset=SET)))
 return z
