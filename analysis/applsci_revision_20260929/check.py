from pathlib import Path
import json,hashlib,sys
import numpy as np
D=Path(__file__).resolve().parent;H=D.parent/'thrust_review_v12';P=D.parents[1]/'output/latex/applsci_submission_en';S=json.loads((D/'summary.json').read_text());F=json.loads((D/'frozen.json').read_text())
assert F['protocol_sha256']==hashlib.sha256((D/'protocol.json').read_bytes()).hexdigest()
for n,h in F['development_records'].items():assert hashlib.sha256((D/'results'/n).read_bytes()).hexdigest()==h
for n,h in json.loads((H/'review_frozen.json').read_text())['source_sha256'].items():assert hashlib.sha256((H/n).read_bytes()).hexdigest()==h
checks=0
for stem in ['track_validation_10_260930401','track_unseen_validation_10_261001401']:
 z=np.load(D/'results'/f'{stem}.npz');data=json.loads((D/'results'/f'{stem}.json').read_text());e=z['error'].astype(float);c=data['configs'];mse=np.mean(e**2,axis=0);peaks=np.max(e,axis=0);use=z['use'];count=use[300:].sum(0)/10
 for j,cfg in enumerate(c):
  bad=np.any(e[:,j]>[cfg['req'],cfg['req']/10],axis=-1).sum(0)
  for i in range(64):
   r=next(r for r in data['rows'] if r['name']==cfg['name'] and r['req']==cfg['req'] and r['target']==i)
   np.testing.assert_allclose(mse[j,i],[r['position_mse'],r['velocity_mse']],rtol=2e-7,atol=1e-6);np.testing.assert_allclose(peaks[j,i],[r['position_peak'],r['velocity_peak']],rtol=2e-7,atol=1e-6)
   assert count[j,i]==r['laser_time'] and bad[i]==r['bad'];checks+=1
 # All three same-sequence replays match exactly.
 for req in [500,1000,1500]:
  a=next(j for j,v in enumerate(c) if v['req']==req and v['name']=='MSC-GP');b=next(j for j,v in enumerate(c) if v['req']==req and v['name']=='ReplayNoAdapt');assert np.array_equal(use[:,a],use[:,b])
assert len(S['validation'])==38 and len(S['outages'])==60
assert all(v for v in S['checks'].values())
# New manuscript tables: independently check the most load-bearing printed rows.
t=(P/'tables/guard_alternatives.tex').read_text();u=(P/'tables/intervention_cells.tex').read_text();count=0
for r in S['validation']:
 label='Original' if r['dataset']=='original' else 'Held-out'
 if r['req']!=1000:continue
 if r['name'] in ['MSC-GP','FixedAdd','PositiveAdd','PositiveScale']:
  for value in [f"{r['position_rmse']:.2f}",f"{r['velocity_peak']:.2f}",f"{r['laser_time']:.2f}"]:assert value in t;count+=1
 if r['name'] in ['MSC-GP','NoiseOnly','RangeOnly','Neither','ReplayNoAdapt']:
  for value in [f"{r['position_rmse']:.2f}",f"{r['velocity_rmse']:.3f}",f"{r['position_peak']:.2f}",f"{r['velocity_peak']:.2f}",f"{r['laser_time']:.2f}"]:assert value in u;count+=1
report=dict(status='PASS',release='AS-MSCGP-20260929-R2',raw_high_rate_trajectory_records_checked=checks,raw_metrics=['position/velocity MSE','position/velocity peaks','violating epochs','effective time','identical replay mask'],new_core_table_numeric_checks=count,validation_cells=38,outage_phase_conditions=60,forecast_cells=12,source_core_unchanged=True,selection_hashes_match=True,regression_checks=S['checks'],scope='Local numerical and packaging checks, not external replication or hardware validation.')
(D/'check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
