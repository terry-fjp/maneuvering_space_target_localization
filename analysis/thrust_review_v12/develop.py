from pathlib import Path
import concurrent.futures,subprocess,json,hashlib
import numpy as np
from scenario import H,ACCELS,DURATION
def job(args,label):
 with (H/'logs'/f'{label}.log').open('w') as w:subprocess.run(['python3',*args],stdout=w,stderr=w,check=True)
 print(label,'DONE',flush=True)
def select_detector():
 rows=json.loads((H/'results/detect_10_260930101_0.json').read_text())['rows'];out=[]
 for name in sorted({r['detector'] for r in rows}):
  rr=[r for r in rows if r['detector']==name];tp=sum(r['tp'] for r in rr);fp=sum(r['fp'] for r in rr);fn=sum(r['fn'] for r in rr)
  out.append(dict(detector=name,tp=tp,fp=fp,fn=fn,f1=2*tp/(2*tp+fp+fn)))
 selected=max([r for r in out if r['detector'].startswith('MSC')],key=lambda r:r['f1'])
 (H/'detector_choice.json').write_text(json.dumps(dict(detector=selected['detector'],candidates=out,rule='Maximum 60-second event F1 on development seed only; same 2/3 vote and 90-second cooldown for all'),indent=2))
 print('DETECTOR',selected,flush=True)
def main():
 job([str(H/'detect.py'),'--freq','10','--seed','260930101'],'new_development_detect')
 select_detector()
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(lambda k:job([str(H/'control.py'),'--freq','10','--seed','260930101','--group','development','--chunk',str(k)],f'dev_{k}'),range(8)))
 rows=[];cfg={}
 for p in sorted((H/'results').glob('track_development_10_260930101_*.json')):
  d=json.loads(p.read_text());rows+=d['rows'];cfg.update({r['name']:r for r in d['configs']})
 summaries=[];freeze={m:{} for m in ['gp','period','rit']}
 for req in [500,1000,1500]:
  rr=[r for r in rows if r['evaluation_req']==req]
  for method in ['gp','period','rit']:
   groups={}
   for r in rr:
    if r['control']!=method:continue
    if method=='gp' and r['guard']==0:continue
    key=(r['period'],r['window']) if method=='period' else r['name'];groups.setdefault(str(key),[]).append(r)
   candidates=[]
   for key,x in groups.items():
    a=dict(req=req,control=method,key=key,name=x[0]['name'],n=len(x),position_peak=max(r['position_peak'] for r in x),velocity_peak=max(r['velocity_peak'] for r in x),laser_time=float(np.mean([r['laser_time'] for r in x])),bad_arcs=sum(r['bad']>0 for r in x))
    a['feasible']=a['position_peak']<=.8*req and a['velocity_peak']<=.8*req/10;candidates.append(a);summaries.append(a)
   valid=[a for a in candidates if a['feasible']]
   if not valid:raise RuntimeError(('No feasible development configuration',req,method))
   pick=min(valid,key=lambda a:a['laser_time']);c=cfg[pick['name']].copy();c.update(req=req,phase=0);freeze[method][str(req)]=c
 freeze.update(detector=json.loads((H/'detector_choice.json').read_text()),development_seed=260930101,validation_seeds=[260930401,260930402,260930403],frequencies=[5,10,15,20],acceleration_levels=ACCELS,deadline_seconds=DURATION,duration_seconds=DURATION)
 freeze['source_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [H/'scenario.py',H/'detect.py',H/'control.py',H/'core.py',H/'engine.py',H/'numerics.py']}
 (H/'frozen.json').write_text(json.dumps(freeze,indent=2));(H/'statistics/development.json').write_text(json.dumps(summaries,indent=2));print('FROZEN',freeze,flush=True)
if __name__=='__main__':main()
