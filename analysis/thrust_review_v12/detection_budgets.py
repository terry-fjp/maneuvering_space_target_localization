"""Calibrate all budgets under actual reset/voting logic, then freeze before checks."""
import json
import numpy as np
import detect
from scenario import H
BUDGETS=[.25,.5,1.,2.];NAMES={f'{method}@{budget:g}':(method,budget) for method in ['MSC16','SS8'] for budget in BUDGETS}
for k,(m,b) in NAMES.items():detect.SPECS[k]=detect.SPECS[m]
def main():
 lo={k:2. for k in NAMES};hi={k:256. for k in NAMES};history=[];exp=64*640/3600
 if (H/'calibration/budgets_frozen.json').exists():
  hi=json.loads((H/'calibration/budgets_frozen.json').read_text())['thresholds']
 else:
  for it in range(8):
   th={k:np.sqrt(lo[k]*hi[k]) for k in NAMES};rr=detect.run(10,261001101,th,True);counts={k:sum(r['fp'] for r in rr if r['detector']==k) for k in NAMES}
   for k,(_,budget) in NAMES.items():
    if counts[k]/exp<=budget:hi[k]=th[k]
    else:lo[k]=th[k]
   history.append(dict(thresholds=th,counts=counts));print('calibration',it,flush=True)
  (H/'calibration/budgets_frozen.json').write_text(json.dumps(dict(thresholds=hi,budgets=BUDGETS,history=history,seed=261001101,exposure=exp),indent=2))
 records=[]
 for null,seeds in [(True,[261001201,261001202,261001203]),(False,[261001301,261001302,261001303])]:
  for seed in seeds:
   rr=detect.run(10,seed,hi,null,save=True);records+=rr;print('check',null,seed,flush=True)
 (H/'statistics/budget_records.json').write_text(json.dumps(records,indent=2))
if __name__=='__main__':main()
