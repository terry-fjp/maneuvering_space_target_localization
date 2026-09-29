import argparse,json,time
import numpy as np
from core import Tracker,rk4,basis,SIGMA_ANGLE
from scenario import H,base,initial,EVENTS,DURATION,PREFIX,event_plan
SPECS={'SS2':[2],'SS8':[8],'SS30':[30],'MSC16':[2,8,16],'MSC30':[2,8,30],'MSC10':[2,5,10]}
def white(y,S,b):
 val,vec=np.linalg.eigh(S);e=np.einsum('nij,nj->ni',vec,np.einsum('nji,nj->ni',vec,y)/np.sqrt(np.maximum(val,1e-20)))
 return np.einsum('nji,nj->ni',b,e)
def run(freq,seed,thresholds,null=False,save=False):
 z=base(freq,seed,null);meta=initial(seed)[0];n=len(meta);names=list(thresholds);c=len(names);idx=np.tile(np.arange(n),c)
 f=Tracker(np.tile(z['x0'],(c,1)),np.tile(z['p0'],(c,1,1)),6)
 hist=np.zeros((30,c*n,3));block=np.zeros((c*n,3));age=np.zeros(c*n,int);votes=np.zeros((3,c*n),bool);last=np.full(c*n,-999)
 th=np.repeat(list(thresholds.values()),n);flags=np.zeros((700,c,n),bool);scores=np.zeros((700,c,n),np.float32);alarms=[[] for _ in idx];obs=z['states'][0,:,6:].copy()
 for tick in range(700*freq):
  sec=tick//freq
  if tick:f.predict(1/freq);obs=rk4(obs,1/freq)
  if tick%freq==0:obs=z['states'][sec,:,6:].copy()
  d=f.x[:,:3]-obs[idx,:3];rr=np.linalg.norm(d,axis=1);u=d/rr[:,None];b=basis(z['um'][tick,idx]);y=np.einsum('nij,nj->ni',b,z['um'][tick,idx]-u)
  h=np.zeros((c*n,2,6));h[:,:,:3]=(b-np.einsum('nij,nj->ni',b,u)[:,:,None]*u[:,None,:])/rr[:,None,None]
  R=np.broadcast_to(np.eye(2)*SIGMA_ANGLE**2,(c*n,2,2));S=h@f.p@h.transpose(0,2,1)+R
  e=white(y,S,b);e*=np.minimum(1,3/np.maximum(1e-12,np.linalg.norm(e,axis=1)))[:,None]
  f.linear_update(y,h,R,np.arange(c*n))
  if tick:block+=e/np.sqrt(freq)
  if tick%freq or tick==0:continue
  hist[sec%30]=block;block[:]=0;age+=1;score=np.zeros(c*n)
  for j,name in enumerate(names):
   sl=slice(j*n,(j+1)*n);ss=[]
   for w in SPECS[name]:
    v=hist[(sec-np.arange(w))%30,sl].sum(0);s=np.sum(v*v,axis=1)/w;s[age[sl]<w]=0;ss.append(s)
   score[sl]=np.max(ss,axis=0)
  votes[sec%3]=score>th;flag=(votes.sum(0)>=2)&(sec>=60)&(sec-last>=90)
  flags[sec]=flag.reshape(c,n);scores[sec]=score.reshape(c,n)
  for i in np.flatnonzero(flag):alarms[i].append(sec)
  f.reset(flag);last[flag]=sec;hist[:,flag]=0;votes[:,flag]=False;age[flag]=0
 rows=[]
 for j,name in enumerate(names):
  for i,m in enumerate(meta):
   aa=alarms[j*n+i];delays=[];late=0;repeat=0;matched=[]
   for tau in ([] if null else event_plan()[0][i].tolist()):
    hits=[a for a in aa if tau<a<=tau+DURATION];delays.append(hits[0]-tau if hits else None)
    if hits:matched.append(hits[0]);repeat+=len(hits)-1
    late+=len([a for a in aa if tau+DURATION<a<tau+150])
   rows.append(dict(m,detector=name,freq=freq,seed=seed,alarms=aa,delays=delays,tp=len(matched),fn=0 if null else 3-len(matched),fp=len(aa)-len(matched),late=late,repeat=repeat,unassociated=len(aa)-len(matched)-late-repeat))
 if save:
  stem=H/'results'/f'detect_{PREFIX}{freq}_{seed}_{int(null)}';stem.with_suffix('.json').write_text(json.dumps(dict(rows=rows,thresholds=thresholds,null=null),indent=2))
  np.savez_compressed(stem.with_suffix('.npz'),flags=flags,scores=scores,names=np.array(names))
 return rows
def calibrate(freq):
 lo={k:2. for k in SPECS};hi={k:256. for k in SPECS};history=[];exposure=64*640/3600
 for it in range(8):
  th={k:np.sqrt(lo[k]*hi[k]) for k in SPECS};r=run(freq,260930001,th,True)
  rates={k:sum(x['fp'] for x in r if x['detector']==k)/exposure for k in SPECS};history.append(dict(thresholds=th,rates=rates))
  for k in SPECS:
   if rates[k]<=.5:hi[k]=th[k]
   else:lo[k]=th[k]
  print('CAL',freq,it,rates,flush=True)
 cr=run(freq,260930001,hi,True,True);nr=run(freq,260930002,hi,True,True)
 out=dict(freq=freq,thresholds=hi,exposure_hours=exposure,history=history,calibration_counts={k:sum(r['fp'] for r in cr if r['detector']==k) for k in hi},check_counts={k:sum(r['fp'] for r in nr if r['detector']==k) for k in hi})
 (H/'calibration'/f'detect_{freq}.json').write_text(json.dumps(out,indent=2))
 if freq==10:run(freq,260930101,hi,save=True)
 print('DONE',freq,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--freq',type=int,required=True);p.add_argument('--calibrate',action='store_true');p.add_argument('--seed',type=int);a=p.parse_args()
 if a.calibrate:calibrate(a.freq)
 else:run(a.freq,a.seed,json.loads((H/'calibration'/f'detect_{a.freq}.json').read_text())['thresholds'],save=True)
