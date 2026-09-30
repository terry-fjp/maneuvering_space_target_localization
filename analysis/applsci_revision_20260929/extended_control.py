"""Derived frozen controller; explicit review-only switches. See prepare.py."""
import argparse,json
import numpy as np
from core import Tracker,rk4,gravity_jacobian,confidence_bounds,RISK_CHI2,basis,SIGMA_ANGLE
from scenario import H,base,initial,DURATION,PREFIX,event_plan
def forecast(f,o,freq):
 x=rk4(f.x[:,:6],1,f.x[:,6:]);oo=rk4(o,1);F=np.zeros_like(f.p);F[:,:3,3:6]=np.eye(3);F[:,3:6,:3]=gravity_jacobian(f.x[:,:3]);F[:,3:6,6:]=np.eye(3)
 phi=np.eye(9)+F+F@F/2;p=phi@f.p@phi.transpose(0,2,1)
 p+=f.forecast_q[:,None,None]*np.kron(np.array([[1/20,1/8,1/6],[1/8,1/3,1/2],[1/6,1/2,1]]),np.eye(3))
 d=x[:,:3]-oo[:,:3];r=np.linalg.norm(d,axis=1);b=basis(d/r[:,None]);h=np.zeros((len(x),2,9));h[:,:,:3]=b/r[:,None,None]
 hp=h@p;K=np.linalg.solve(hp@h.transpose(0,2,1)+np.eye(2)*SIGMA_ANGLE**2/freq,hp).transpose(0,2,1);p-=K@hp;p=(p+p.transpose(0,2,1))/2
 return confidence_bounds(p)
def configs(group):
 if group.startswith("review"):
  from configurations import review_configs
  return review_configs(group)
 chosen=json.loads((H/'detector_choice.json').read_text());det=chosen['detector'];out=[]
 def cfg(name,ctrl,req=500,**kw):
  d=dict(name=name,control=ctrl,req=req,detector=det,margin=.75,guard=5,period=30,window=1,phase=0,gap=30);d.update(kw);return d
 if group=='development':
  for req in [500,1000,1500]:
   for g in [0,2,5,10]:
    for margin in [.5,.75,1]:out.append(cfg(f'gp_{req}_{g}_{margin}','gp',req,guard=g,margin=margin))
  for T,D in [(10,1),(20,1),(30,1),(40,1),(60,1),(80,1),(100,1),(100,10),(150,10),(200,10),(100,20),(200,20)]:
   for ph in [0,.25,.5,.75]:out.append(cfg(f'period_{T}_{D}_{ph}','period',period=T,window=D,phase=ph*T))
  for gap in [5,10,15,20,25,30,40,60,80,100,150,200]:out.append(cfg(f'rit_{gap}','rit',gap=gap))
 elif group in ['main','phases']:
  f=json.loads((H/'frozen.json').read_text())
  for req in [500,1000,1500]:
   for method in ['gp','period','rit']:
    d=f[method][str(req)].copy();d.update(name={'gp':'MSC-GP','period':'Periodic','rit':'RIT'}[method],req=req);out.append(d)
   if group=='main':
    d=out[-3].copy();d.update(name='NoGuard',guard=0);out.append(d)
    d=out[-4].copy();d.update(name='SS8-GP',detector='SS8');out.append(d)
   else:
    for ph in [.25,.5,.75]:
     d=f['period'][str(req)].copy();d.update(name=f'Periodic-{ph}',req=req,phase=ph*d['period']);out.append(d)
 elif group=='reference':out=[cfg('Continuous','continuous')]
 else:raise ValueError(group)
 return out
def run(freq,seed,group,chunk=None):
 cfg=configs(group)
 if chunk is not None:cfg=cfg[chunk*12:(chunk+1)*12]
 if not cfg:return
 z=base(freq,seed);meta=initial(seed)[0];dt=1/freq;n=len(meta);c=len(cfg);N=n*c;idx=np.tile(np.arange(n),c)
 d=np.load(__import__('scenario').H/'results'/f'detect_{PREFIX}{freq}_{seed}_0.npz');dn=d['names'].tolist();flags=d['flags'];di=np.repeat([dn.index(q['detector']) for q in cfg],n)
 f=Tracker(np.tile(z['x0'],(c,1)),np.tile(z['p0'],(c,1,1)),9);ctrl=np.repeat([q['control'] for q in cfg],n)
 req=np.repeat([q['req'] for q in cfg],n);margin=np.repeat([q['margin'] for q in cfg],n);guard=np.repeat([q['guard'] for q in cfg],n)
 period=np.repeat([q['period'] for q in cfg],n);window=np.repeat([q['window'] for q in cfg],n);phase=np.repeat([q['phase'] for q in cfg],n);gap=np.repeat([q['gap'] for q in cfg],n)
 times,levels,axes=event_plan();et=np.tile(times,(c,1))
 adapt_enabled=np.repeat([q.get("adapt",True) for q in cfg],n);burst_enabled=np.repeat([q.get("burst",True) for q in cfg],n)
 outage_start=np.repeat([q.get("outage_start",80) for q in cfg],n)
 noalarm=np.repeat([q.get("noalarm",False) for q in cfg],n);delays=np.repeat([q.get("delay",0) for q in cfg],n);outage=np.repeat([q.get("outage",0) for q in cfg],n)
 requested=np.zeros(N,int);windows=np.zeros(N,int);prev_request=np.zeros(N,bool);request_history=[]
 last=np.full(N,-999.);until=np.full(N,30.);last_range=np.zeros(N);cmd=np.zeros(N,bool)
 sum2=np.zeros((N,2));peak=np.zeros((N,2));bad=np.zeros((N,3),int);runbad=bad.copy();maxrun=bad.copy();count=np.zeros(N,int);countall=count.copy();coverage=np.zeros((N,2),int);maxgap=np.zeros(N)
 trace=np.zeros((700,c,n,8),np.float32);usehist=np.zeros((700*freq,c,n),bool);error=np.zeros((670*freq,c,n,2),np.float32) if group=='validation' else None
 truth=z['states'][0,:,:6].copy();obs=z['states'][0,:,6:].copy()
 event_sums=np.zeros((N,3,2));event_peak=event_sums.copy();event_count=np.zeros(3,int)
 for tick in range(700*freq):
  sec=tick//freq;t=tick/freq
  if tick:truth=rk4(truth,dt,z['forces'][(tick-1)//freq]);obs=rk4(obs,dt);f.predict(dt,(t-last<DURATION)&adapt_enabled)
  if tick%freq==0:
   truth=z['states'][sec,:,:6].copy();obs=z['states'][sec,:,6:].copy();cmd[:]=False;bb=np.zeros((N,2));gg=bb.copy()
   ids=np.flatnonzero((ctrl=='gp')|(ctrl=='constant'))
   if len(ids):
    v=Tracker(f.x[ids,:6],f.p[ids,:6,:6],9);v.x=f.x[ids];v.p=f.p[ids];v.forecast_q=np.where((t-last[ids]<DURATION)&adapt_enabled[ids],3e-4,1e-7)
    bb[ids]=forecast(v,obs[idx[ids]],freq)
    for a in ids[ctrl[ids]=='constant']:
     bb[a]=cfg[a//n]['constant']
    gg[ids]=bb[ids]+np.column_stack([guard[ids]*(t+1-last_range[ids]),guard[ids]])
    for a in ids:
     q=cfg[a//n]
     if "add_fraction" in q:gg[a]=bb[a]+q["add_fraction"]*np.array([req[a],req[a]/10])
     if "cov_scale" in q:gg[a]=bb[a]*np.sqrt(q["cov_scale"])
    cmd[ids]=np.any(gg[ids]>np.stack([req[ids],req[ids]/10],axis=1)*margin[ids,None],axis=1)
   cmd[ctrl=='rit']=t+1-last_range[ctrl=='rit']>gap[ctrl=='rit']+1e-9
  per=(ctrl=='period')&(np.mod(t-phase,period)<window-1e-9)&(t>=30)
  request=cmd|per|(ctrl=='continuous')|(t<until);available=np.linalg.norm(truth[idx,:3]-obs[idx,:3],axis=1)<=2e6+1e-6;request_history.append(request.copy())
  delivered=request.copy()
  for lag in np.unique(delays):
   ii=(delays==lag)&(t>=30);oldtick=tick-int(round(lag*freq));delivered[ii]=request_history[max(0,oldtick)][ii] if oldtick>=0 else False
  blocked=(t>=30)&(np.mod(t-outage_start,200)<outage)&(t>=outage_start)
  use=delivered&available&(~blocked)
  for j,q in enumerate(cfg):
   if "replay_source" in q:
    src=next(k for k,v in enumerate(cfg) if v["name"]==q["replay_source"] and v["req"]==q["req"])
    use[j*n:(j+1)*n]=use[src*n:(src+1)*n]
  if t>=30:requested+=request;windows+=request&(~prev_request)
  prev_request=request.copy()
  usehist[tick]=use.reshape(c,n);f.observe(z['um'][tick,idx],z['rm'][tick,idx],obs[idx],use);countall+=use
  if t>=30:maxgap=np.maximum(maxgap,t-last_range)
  last_range[use]=t
  delta=np.stack([f.x[:,:3]-truth[idx,:3],f.x[:,3:6]-truth[idx,3:]],axis=1);e=np.linalg.norm(delta,axis=2)
  if t>=30:
   sum2+=e**2;peak=np.maximum(peak,e);count+=use
   for j,r in enumerate([500,1000,1500]):
    b=np.any(e>[r,r/10],axis=1);bad[:,j]+=b;runbad[:,j]=np.where(b,runbad[:,j]+1,0);maxrun[:,j]=np.maximum(maxrun[:,j],runbad[:,j])
   for j in range(2):
    pp=f.p[:,j*3:j*3+3,j*3:j*3+3];quad=np.einsum('ni,ni->n',delta[:,j],np.linalg.solve(pp,delta[:,j,:,None])[:,:,0]);coverage[:,j]+=quad<=RISK_CHI2
   if error is not None:error[tick-30*freq]=e.reshape(c,n,2)
  for j in range(3):
   on=(et[:,j]<=t)&(t<et[:,j]+DURATION);event_sums[on,j]+=e[on]**2;event_peak[on,j]=np.maximum(event_peak[on,j],e[on])
  event_count[:]=DURATION*freq
  if tick%freq==0:
   trace[sec]=np.column_stack([e,bb,gg,cmd,request]).reshape(c,n,8)
   alarm=flags[sec,di,idx]&(~noalarm);last[alarm]=t;until[alarm&burst_enabled]=t+5+dt
 rows=[]
 for j,q in enumerate(cfg):
  for i,m in enumerate(meta):
   k=j*n+i
   for r in ([500,1000,1500] if group in ['development','review_development'] and q['control'] in ['period','rit'] else [q['req']]):
    jj=[500,1000,1500].index(r);row=dict(m,**q,freq=freq,seed=seed,evaluation_req=r,samples=670*freq,dataset=PREFIX or "original",request_time=float(requested[k]/freq),request_windows=int(windows[k]),position_mse=float(sum2[k,0]/(670*freq)),velocity_mse=float(sum2[k,1]/(670*freq)),position_peak=float(peak[k,0]),velocity_peak=float(peak[k,1]),bad=int(bad[k,jj]),longest_bad=float(maxrun[k,jj]/freq),laser_time=float(count[k]/freq),laser_all_time=float(countall[k]/freq),position_coverage=float(coverage[k,0]/(670*freq)),velocity_coverage=float(coverage[k,1]/(670*freq)),max_gap=float(maxgap[k]),event_mse=(event_sums[k]/event_count[:,None]).tolist(),event_peak=event_peak[k].tolist());rows.append(row)
 stem=H/'results'/f'track_{PREFIX}{group}_{freq}_{seed}{"_"+str(chunk) if chunk is not None else ""}'
 stem.with_suffix('.json').write_text(json.dumps(dict(rows=rows,configs=cfg),indent=2))
 if error is not None:np.savez_compressed(stem.with_suffix('.npz'),error=error,use=usehist,trace=trace)
 print('TRACK',group,freq,seed,chunk,len(rows),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--freq',type=int,required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--group',required=True);p.add_argument('--chunk',type=int);a=p.parse_args();run(a.freq,a.seed,a.group,a.chunk)
