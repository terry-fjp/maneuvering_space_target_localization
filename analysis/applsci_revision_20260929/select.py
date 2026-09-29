from pathlib import Path
import json,hashlib
import numpy as np
D=Path(__file__).resolve().parent;rows=[]
files=sorted((D/'results').glob('track_development*.json'))
for p in files:rows+=json.loads(p.read_text())['rows']
assert len(rows)==27*64,len(rows)
candidates=[];selected=[]
for name in sorted({r['name'] for r in rows}):
 rr=[r for r in rows if r['name']==name];r=rr[0];pp=max(x['position_peak'] for x in rr);vp=max(x['velocity_peak'] for x in rr)
 candidates.append(dict(name=name,position_peak=pp,velocity_peak=vp,feasible=pp<=800 and vp<=80,time=float(np.mean([x['laser_time'] for x in rr])),parameter=r.get('add_fraction',r.get('cov_scale'))))
for family,key in [('Add','add_fraction'),('Scale','cov_scale')]:
 viable=[r for r in candidates if r['name'].startswith(family) and r['feasible']]
 if not viable:raise RuntimeError(f'No feasible {family}; report search failure, do not select on validation')
 best=min(viable,key=lambda r:(r['time'],r['parameter']));base=json.loads((D.parent/'thrust_review_v12/frozen.json').read_text())['gp']['1000'];selected.append(dict(base,name='FixedAdd' if family=='Add' else 'CovScale',guard=0,**{key:best['parameter']}))
# Retain unrestricted minima and additionally freeze the least-occupancy strictly positive alternatives.
for family,key,lower in [('Add','add_fraction',0),('Scale','cov_scale',1)]:
 viable=[r for r in candidates if r['name'].startswith(family) and r['feasible'] and r['parameter']>lower]
 best=min(viable,key=lambda r:(r['time'],r['parameter']));base=json.loads((D.parent/'thrust_review_v12/frozen.json').read_text())['gp']['1000'];selected.append(dict(base,name='PositiveAdd' if family=='Add' else 'PositiveScale',guard=0,**{key:best['parameter']}))
(D/'frozen.json').write_text(json.dumps(dict(selected=selected,candidates=candidates,protocol_sha256=hashlib.sha256((D/'protocol.json').read_bytes()).hexdigest(),development_records={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}),indent=2))
print(json.dumps(dict(selected=selected,candidates=candidates),indent=2))
