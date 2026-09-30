"""Development-only local period refinement; frozen phase sensitivity validation."""
import json,subprocess,concurrent.futures,argparse,os
from scenario import H
PHASES=[0,.25,.5,.75]
def candidates():
 periods=[T for T in range(31,111) if T not in [40,60,80,100]]
 return [dict(name=f'fineperiod_{T}_1_{ph}',control='period',req=500,detector='MSC16',margin=.75,guard=5,period=T,window=1,phase=ph*T,gap=30) for T in periods for ph in PHASES]
def run_one(mode,chunk,seed,dataset):
 import period_control as c
 configs=candidates() if mode=='develop' else json.loads((H/'period_frozen.json').read_text())['configs']
 c.configs=lambda group:configs
 c.run(10,seed,'period_followup',chunk)
 prefix='' if dataset=='original' else 'unseen_'
 for ext in ['json']:
  p=H/'results'/f'track_{prefix}period_followup_10_{seed}_{chunk}.{ext}'
  p.rename(H/'results'/f'period_{mode}_{dataset}_10_{seed}_{chunk}.{ext}')
def worker(args):
 mode,chunk,seed,dataset=args;env=os.environ.copy();env['MSC_SET']=dataset
 with (H/'logs'/f'period_{mode}_{dataset}_{seed}_{chunk}.log').open('w') as log:
  subprocess.run(['python3',str(H/'period_sensitivity.py'),'--one','--mode',mode,'--chunk',str(chunk),'--seed',str(seed),'--dataset',dataset],env=env,stdout=log,stderr=log,check=True)
 print('PERIOD',mode,dataset,seed,chunk,'DONE',flush=True)
def select():
 rows=[]
 for pattern in ['track_development_10_260930101_*.json','period_develop_original_*.json']:
  for p in sorted((H/'results').glob(pattern)):rows+=json.loads(p.read_text())['rows']
 cfg={}
 for r in rows:
  if r['control']=='period':cfg[(r['period'],r['window'],r['phase']/r['period'])]=r
 stats=[]
 for req in [500,1000,1500]:
  for (T,D,ph),c in cfg.items():
   rr=[r for r in rows if r['control']=='period' and r['period']==T and r['window']==D and r['phase']==ph*T and r['evaluation_req']==req]
   assert len(rr)==64,(T,D,ph,req,len(rr))
   stats.append(dict(req=req,period=T,window=D,phase_fraction=ph,position_peak=max(r['position_peak'] for r in rr),velocity_peak=max(r['velocity_peak'] for r in rr),laser_time=sum(r['laser_time'] for r in rr)/64,feasible=max(r['position_peak'] for r in rr)<=.8*req and max(r['velocity_peak'] for r in rr)<=.08*req))
 selection=[];configs=[]
 for scope in ['coarse','refined']:
  for req in [500,1000,1500]:
   ss=[r for r in stats if r['req']==req and (scope=='refined' or (r['period'],r['window']) in [(10,1),(20,1),(30,1),(40,1),(60,1),(80,1),(100,1),(100,10),(150,10),(200,10),(100,20),(200,20)])]
   joint=[]
   for T,D in sorted({(r['period'],r['window']) for r in ss}):
    rr=[r for r in ss if r['period']==T and r['window']==D]
    if len(rr)==4 and all(r['feasible'] for r in rr):joint.append(dict(req=req,period=T,window=D,phase_fraction=0,laser_time=sum(r['laser_time'] for r in rr)/4,position_peak=max(r['position_peak'] for r in rr),velocity_peak=max(r['velocity_peak'] for r in rr),feasible=True))
   chosen=min(joint,key=lambda r:r['laser_time']);selection.append(dict(scope=scope,rule='joint',**chosen))
   for ph in PHASES:
    rr=[r for r in ss if r['phase_fraction']==ph and r['feasible']];pick=min(rr,key=lambda r:r['laser_time']);selection.append(dict(scope=scope,rule='individual',**pick))
 for r in selection:
  if r['scope']!='refined':continue
  name=f"{r['rule']}-{r['req']}-{r['phase_fraction']}";configs.append(dict(name=name,control='period',req=r['req'],detector='MSC16',margin=.75,guard=5,period=r['period'],window=r['window'],phase=r['period']*r['phase_fraction'],gap=30))
 (H/'statistics/period_development.json').write_text(json.dumps(dict(candidates=stats,selection=selection),indent=2));(H/'period_frozen.json').write_text(json.dumps(dict(development_seed=260930101,frequency=10,validation='Frozen before supplementary validation',configs=configs),indent=2));print(json.dumps(selection,indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['develop','validate','select'],default='develop');p.add_argument('--one',action='store_true');p.add_argument('--chunk',type=int);p.add_argument('--seed',type=int);p.add_argument('--dataset',default='original');a=p.parse_args()
 if a.one:run_one(a.mode,a.chunk,a.seed,a.dataset)
 elif a.mode=='select':select()
 else:
  if a.mode=='develop':jobs=[('develop',i,260930101,'original') for i in range((len(candidates())+11)//12)]
  else:jobs=[('validate',i,seed,ds) for ds,seeds in [('original',[260930401,260930402,260930403]),('unseen',[261001401,261001402,261001403])] for seed in seeds for i in range(2)]
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:list(ex.map(worker,jobs))
  if a.mode=='develop':select()
