"""Recompute aggregate metrics from every packaged trajectory JSON record.
This checks stored records, not fresh simulation or omitted high-rate arrays.
"""
from pathlib import Path
import json,math,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];H=ROOT/'analysis/thrust_review_v12';D=ROOT/'analysis/applsci_revision_20260929'
checked=0

def readrows(folder,pattern):
 return [r for p in sorted(folder.glob(pattern)) for r in json.loads(p.read_text())['rows']]

def check(rr,s):
 global checked
 assert rr
 values={'position_rmse':math.sqrt(sum(r['position_mse'] for r in rr)/len(rr)),
 'velocity_rmse':math.sqrt(sum(r['velocity_mse'] for r in rr)/len(rr)),
 'position_peak':max(r['position_peak'] for r in rr),
 'velocity_peak':max(r['velocity_peak'] for r in rr),
 'laser_time':sum(r['laser_time'] for r in rr)/len(rr),
 'bad_arcs':sum(r['bad']>0 for r in rr),
 'longest_bad':max(r['longest_bad'] for r in rr)}
 for k,v in values.items():
  if k in s:assert np.isclose(v,s[k],rtol=1e-10,atol=1e-8),(k,v,s[k])
 if 'bad_targets' in s:assert len({r['target'] for r in rr if r['bad']})==s['bad_targets']
 checked+=len(rr)

f=json.loads((H/'review_frozen.json').read_text())
for name,h in f['source_sha256'].items():assert hashlib.sha256((H/name).read_bytes()).hexdigest()==h,name
summary=json.loads((H/'statistics/review_summary.json').read_text())
for ds,prefix in [('original',''),('unseen','unseen_')]:
 rows=readrows(H/'results',f'track_{prefix}review_main_*.json');assert len(rows)==13824
 for s in summary['tracking']:
  if s['dataset']==ds:check([r for r in rows if r['name']==s['name'] and r['req']==s['req']],s)
new=json.loads((D/'summary.json').read_text());rows=readrows(D/'results','track_*validation*.json');assert len(rows)==7296
for s in new['validation']:check([r for r in rows if (r['dataset'],r['req'],r['name'])==(s['dataset'],s['req'],s['name'])],s)
rows=readrows(D/'results','track_outages*.json');assert len(rows)==11520
for s in new['outages']:check([r for r in rows if (r['req'],r['method'],r['outage'],r['offset'])==(s['req'],s['method'],s['length'],s['offset'])],s)
# Confirm the original/held-out target identifiers do not overlap.
import csv
ids=lambda n:{r['norad'] for r in csv.DictReader((H/'data'/n).open())}
a,b=ids('targets.csv'),ids('unseen_targets.csv');assert len(a)==len(b)==64 and not a&b
print(json.dumps(dict(status='PASS',aggregate_groups=36+38+60,trajectory_record_checks=checked,
 disjoint_target_ids=[len(a),len(b)],core_hashes_match=True,
 scope='Stored per-trajectory records and aggregate summaries. No claim of fresh simulation or high-rate/replay-mask validation.'),indent=2))
