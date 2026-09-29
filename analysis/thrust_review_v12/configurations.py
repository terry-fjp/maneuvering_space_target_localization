import json
import numpy as np
from scenario import H
F=json.loads((H/'frozen.json').read_text())
def review_configs(group):
 out=[]
 if group=='review_development':
  ref=F['rit']['500'].copy()
  for gap in sorted(set(range(20,121))|{5,10,15,150,200}):out.append(dict(ref,name=f'RIT-{gap}',control='rit',gap=gap))
  const=json.loads((H/'constant_candidates.json').read_text())
  for quantiles in [[10,25,50,75,90],[95,97.5,99,99.5,100]]:
   for req in [500,1000,1500]:
    for q in quantiles:out.append(dict(F['gp'][str(req)],name=f'Const-{req}-{q}',control='constant',constant=const[str(req)][str(q)],quantile=float(q)))
  return out
 frozen=json.loads((H/'review_frozen.json').read_text())
 for req in [500,1000,1500]:
  main=[dict(F['gp'][str(req)],name='MSC-GP'),dict(F['period'][str(req)],name='Periodic'),dict(frozen['rit'][str(req)],name='RIT-fine'),dict(frozen['constant'][str(req)],name='Constant')]
  if group=='review_main':
   out+=main
   out.append(dict(main[0],name='NoAlarm',noalarm=True))
   out.append(dict(F['gp'][str(req)],name='Constant50',control='constant',constant=json.loads((H/'constant_candidates.json').read_text())[str(req)]['50']))
  elif group=='review_service':
   for condition,delay,outage in [('ideal',0,0),('delay0.5',.5,0),('delay1',1,0),('delay2',2,0),('gap10',0,10),('gap30',0,30),('delay1-gap10',1,10)]:
    out += [dict(c,name=c['name']+'|'+condition,delay=delay,outage=outage,service=condition) for c in main]
  elif group=='review_diagnostic':out.append(main[0])
  else:raise ValueError(group)
 return out
