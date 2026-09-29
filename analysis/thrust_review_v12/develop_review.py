import json,hashlib,concurrent.futures,subprocess,os
import numpy as np
from scenario import H

def job(chunk):
 from configurations import review_configs
 path=H/'results'/f'track_review_development_10_260930101_{chunk}.json'
 expected=review_configs('review_development')[chunk*12:(chunk+1)*12]
 if path.exists() and json.loads(path.read_text())['configs']==expected:
  print('chunk',chunk,'REUSED',flush=True);return
 with (H/'logs'/f'fine_develop_{chunk}.log').open('w') as f:subprocess.run(['python3',str(H/'control.py'),'--freq','10','--seed','260930101','--group','review_development','--chunk',str(chunk)],stdout=f,stderr=f,check=True)
 print('chunk',chunk,'DONE',flush=True)
def main():
 z=np.load(H/'results/track_main_10_260930101.npz' if (H/'results/track_main_10_260930101.npz').exists() else H/'statistics/development_trace.npz');d=json.loads((H/'results/track_main_10_260930101.json').read_text());constants={}
 for req in [500,1000,1500]:
  j=next(i for i,c in enumerate(d['configs']) if c['name']=='MSC-GP' and c['req']==req);values=z['trace'][30:,j,:,2:4].reshape(-1,2);constants[str(req)]={str(q):np.percentile(values,q,axis=0).tolist() for q in [10,25,50,75,90,95,97.5,99,99.5,100]}
 (H/'constant_candidates.json').write_text(json.dumps(constants,indent=2))
 from configurations import review_configs
 cfg=review_configs('review_development')
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(job,range((len(cfg)+11)//12)))
 rows=[]
 for p in sorted((H/'results').glob('track_review_development_10_260930101_*.json')):rows+=json.loads(p.read_text())['rows']
 summaries=[];frozen={'rit':{},'constant':{}}
 for req in [500,1000,1500]:
  for ctrl in ['rit','constant']:
   candidates=[]
   for c in cfg:
    if c['control']!=ctrl:continue
    rr=[r for r in rows if r['evaluation_req']==req and r['name']==c['name']]
    if not rr:continue
    r=dict(req=req,name=c['name'],control=ctrl,gap=c.get('gap'),constant=c.get('constant'),position_peak=max(r['position_peak'] for r in rr),velocity_peak=max(r['velocity_peak'] for r in rr),laser_time=float(np.mean([r['laser_time'] for r in rr])))
    r['feasible']=r['position_peak']<=.8*req and r['velocity_peak']<=.08*req;candidates.append(r);summaries.append(r)
   valid=[r for r in candidates if r['feasible']];assert valid,(req,ctrl)
   pick=min(valid,key=lambda r:r['laser_time']);c=next(c for c in cfg if c['name']==pick['name']).copy();c['req']=req;frozen[ctrl][str(req)]=c
 frozen.update(development_seed=260930101,unseen_validation_seeds=[261001401,261001402,261001403],selection_rule='same 80% peak criterion and minimum mean work time',source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [H/'control.py',H/'scenario.py',H/'detect.py',H/'core.py',H/'engine.py',H/'numerics.py',H/'configurations.py']})
 (H/'review_frozen.json').write_text(json.dumps(frozen,indent=2));(H/'statistics/fine_development.json').write_text(json.dumps(summaries,indent=2));print(frozen,flush=True)
if __name__=='__main__':main()
