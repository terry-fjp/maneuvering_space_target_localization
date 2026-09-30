"""Audit all extension arrays, unchanged reference runs, disjoint geometry and replay."""
import json,csv,hashlib
import numpy as np
from scenario import H
frozen=json.loads((H/'review_frozen.json').read_text())
for name,digest in frozen['source_sha256'].items():assert hashlib.sha256((H/name).read_bytes()).hexdigest()==digest,name
old={int(r['norad']) for r in csv.DictReader((H/'data/targets.csv').open())};new={int(r['norad']) for r in csv.DictReader((H/'data/unseen_targets.csv').open())};assert len(old)==len(new)==64 and not old&new
counts={};regression=0
for kind,pattern in [('main','track_*review_main_*.json'),('service','track_review_service_*.json')]:
 total=0
 for path in sorted((H/'results').glob(pattern)):
  d=json.loads(path.read_text());z=np.load(path.with_suffix('.npz'));e=z['error'].astype(float);cfg=d['configs'];freq=d['rows'][0]['freq'];ms=(e**2).mean(0);peak=e.max(0);times=z['use'][30*freq:].sum(0)/freq
  for j,c in enumerate(cfg):
   bad=np.any(e[:,j]>[c['req'],c['req']/10],axis=2);running=np.zeros(64,int);maxrun=running.copy()
   for b in bad:running=np.where(b,running+1,0);maxrun=np.maximum(maxrun,running)
   for i in range(64):
    r=d['rows'][j*64+i];assert np.allclose(ms[j,i],[r['position_mse'],r['velocity_mse']],rtol=3e-7,atol=1e-5);assert np.allclose(peak[j,i],[r['position_peak'],r['velocity_peak']],rtol=2e-7,atol=2e-5);assert times[j,i]==r['laser_time'];assert bad[:,i].sum()==r['bad'];assert r['longest_bad']==maxrun[i]/freq;total+=1
  if kind=='main' and 'unseen' not in path.name:
   prior=json.loads((H/'results'/f"track_main_{freq}_{d['rows'][0]['seed']}.json").read_text())['rows'];by={(r['name'],r['req'],r['target']):r for r in prior}
   for r in d['rows']:
    if r['name'] in ['MSC-GP','Periodic']:
     p=by[r['name'],r['req'],r['target']]
     for k in ['position_mse','velocity_mse','laser_time','bad']:assert p[k]==r[k]
     regression+=1
  print('VERIFIED',path.name,flush=True)
 counts[kind]=total
assert counts=={'main':27648,'service':16128},counts
for prefix,seed in [('',260930401),('unseen_',261001401)]:
 a=json.loads((H/'results'/f'track_{prefix}review_diagnostic_10_{seed}.json').read_text())['rows'];b=json.loads((H/'results'/f'track_{prefix}review_main_10_{seed}.json').read_text())['rows'];by={(r['name'],r['req'],r['target']):r for r in b}
 for r in a:
  p=by[r['name'],r['req'],r['target']]
  for k in ['position_mse','velocity_mse','laser_time','bad']:assert p[k]==r[k]
report=dict(status='PASS',records=counts,reference_regression_records=regression,disjoint_targets=64,bypass_noninterference=True,frozen_sources=True)
(H/'statistics/verification_review.json').write_text(json.dumps(report,indent=2));print(report)
