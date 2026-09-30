"""Check the packaged 5 Hz sample against its high-rate arrays."""
import json, hashlib
import numpy as np
from scenario import H
frozen=json.loads((H/'review_frozen.json').read_text())
for n,h in frozen['source_sha256'].items():
 assert hashlib.sha256((H/n).read_bytes()).hexdigest()==h,n
count=0
for filename in ['track_review_main_5_260930401.json','track_unseen_review_main_5_261001401.json']:
 p=H/'results'/filename;d=json.loads(p.read_text());z=np.load(p.with_suffix('.npz'));e=z['error'].astype(float)
 mse=np.mean(e**2,axis=0);peak=e.max(0);times=z['use'][150:].sum(0)/5
 for j,c in enumerate(d['configs']):
  for i in range(64):
   r=d['rows'][64*j+i]
   assert np.allclose(mse[j,i],[r['position_mse'],r['velocity_mse']],rtol=3e-7,atol=1e-5)
   assert np.allclose(peak[j,i],[r['position_peak'],r['velocity_peak']],rtol=2e-7,atol=2e-5)
   assert times[j,i]==r['laser_time']
   assert np.any(e[:,j,i]>[r['req'],r['req']/10],axis=1).sum()==r['bad'];count+=1
print(json.dumps({'status':'PASS','sample_records':count,'full_population_check':'statistics/verification_review.json; rerun verify_review.py after all arrays are regenerated'}))
