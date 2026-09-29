"""Regenerate the 5 Hz middle-tier core comparison without using cached observations.
Run separately with --dataset original and --dataset unseen. No frozen files change.
"""
from pathlib import Path
import argparse, json, os, sys, tempfile, shutil, hashlib
import numpy as np

parser=argparse.ArgumentParser()
parser.add_argument('--dataset', choices=['original','unseen'], required=True)
parser.add_argument('--output',type=Path, required=True)
args=parser.parse_args()
os.environ['MSC_SET']=args.dataset
root=Path(__file__).resolve().parents[2]
source=root/'analysis/thrust_review_v12'
sys.path.insert(0,str(source))
import scenario, control, detect, configurations
freq=5;seed=260930401 if args.dataset=='original' else 261001401
frozen=json.loads((source/'review_frozen.json').read_text())
for name,digest in frozen['source_sha256'].items():
 assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest,name
cfg=[c for c in configurations.review_configs('review_main') if c['req']==1000 and c['name'] in ['MSC-GP','Periodic','RIT-fine','Constant']]
assert len(cfg)==4
expected=json.loads((source/'results'/f'track_{scenario.PREFIX}review_main_{freq}_{seed}.json').read_text())['rows']
expected={(r['name'],r['target']):r for r in expected if r['req']==1000}
thresholds=json.loads((source/'calibration/detect_5.json').read_text())['thresholds']
thresholds={name:thresholds[name] for name in sorted({c['detector'] for c in cfg})}
with tempfile.TemporaryDirectory(prefix='msc-s1-core-') as td:
 stage=Path(td)
 shutil.copytree(source/'data',stage/'data')
 for name in ['cache','results']: (stage/name).mkdir()
 scenario.H=stage;control.H=stage;detect.H=stage
 control.configs=lambda group:cfg
 detect.run(freq,seed,thresholds,save=True)
 control.run(freq,seed,'review_main')
 actual=json.loads((stage/'results'/f'track_{scenario.PREFIX}review_main_{freq}_{seed}.json').read_text())['rows']
 assert len(actual)==256
 metrics=['position_mse','velocity_mse','position_peak','velocity_peak']
 maxdiff={m:0.0 for m in metrics}
 for row in actual:
  ref=expected[row['name'],row['target']]
  for m in metrics:
   assert np.isclose(row[m],ref[m],rtol=1e-6,atol=1e-5),(row['name'],row['target'],m,row[m],ref[m])
   maxdiff[m]=max(maxdiff[m],abs(row[m]-ref[m]))
  for m in ['bad','laser_time','laser_all_time','request_windows','request_time','longest_bad']:
   assert row[m]==ref[m],(row['name'],row['target'],m,row[m],ref[m])
 summaries=[]
 for c in cfg:
  rows=[r for r in actual if r['name']==c['name']]
  summaries.append(dict(method=c['name'],trajectories=len(rows),position_rmse_m=float(np.sqrt(np.mean([r['position_mse'] for r in rows]))),velocity_rmse_m_s=float(np.sqrt(np.mean([r['velocity_mse'] for r in rows]))),position_peak_m=max(r['position_peak'] for r in rows),violating_trajectories=sum(r['bad']>0 for r in rows),mean_effective_ranging_s=float(np.mean([r['laser_time'] for r in rows]))))
report=dict(status='PASS',dataset=args.dataset,frequency_hz=freq,seed=seed,task=[1000,100],evaluation_interval_s=[30,700],fresh_truth_and_measurements=True,regenerated_detector=True,matched_records=256,continuous_metric_tolerance=dict(rtol=1e-6,atol=1e-5),discrete_and_occupancy_tolerance='exact',max_absolute_differences=maxdiff,results=summaries,scope='Local fresh simulation versus frozen per-trajectory records; not an independent external replication or onboard timing benchmark.')
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
