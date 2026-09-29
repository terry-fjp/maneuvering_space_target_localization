import json
import numpy as np
from scenario import H
from statistics_utils import agg,effect
rr=[]
for p in sorted((H/'results').glob('period_validate_*.json')):rr+=json.loads(p.read_text())['rows']
# The simulator emits all three evaluation thresholds for each periodic stream.
# Keep the declared task only; do not count extra threshold rows as trajectories.
rr=[r for r in rr if r['evaluation_req']==r['req']];assert len(rr)==5760,len(rr)
base=[]
for p in (H/'results').glob('track_*review_main_10_*.json'):base+=json.loads(p.read_text())['rows']
out=[]
for ds in ['original','unseen_']:
 for req in [500,1000,1500]:
  gp=[r for r in base if r['dataset']==ds and r['req']==req and r['name']=='MSC-GP'];assert len(gp)==192
  for n in sorted({r['name'] for r in rr if r['req']==req}):
   x=[r for r in rr if r['dataset']==ds and r['req']==req and r['name']==n];assert len(x)==192
   out.append(dict(dataset=ds,req=req,name=n,period=x[0]['period'],phase=x[0]['phase']/x[0]['period'],**agg(x),**effect(gp,x)))
(H/'statistics/period_validation.json').write_text(json.dumps(out,indent=2))
for r in out:print(r['dataset'],r['req'],r['name'],r['period'],round(r['laser_time'],3),r['bad_arcs'],round(r['saving'],3),r['saving_ci'])
