from pathlib import Path
import os,sys,json,argparse
D=Path(__file__).resolve().parent;H=D.parent/'thrust_review_v12';sys.path.insert(0,str(H))
import extended_control as c
F=json.loads((H/'frozen.json').read_text());R=json.loads((H/'review_frozen.json').read_text());P=json.loads((D/'protocol.json').read_text())
def configurations(group):
 def gp(req=1000,**kw):return dict(F['gp'][str(req)],**kw)
 if group=='development':
  return [gp(name=f'Add-{v}',guard=0,add_fraction=v) for v in P['add_fraction']]+[gp(name=f'Scale-{v}',guard=0,cov_scale=v) for v in P['cov_scale']]
 if group=='validation':
  out=[]
  for r in P['factorial_tiers']:
   out.extend([gp(r,name='MSC-GP'),gp(r,name='NoiseOnly',burst=False),gp(r,name='RangeOnly',adapt=False),gp(r,name='Neither',adapt=False,burst=False),gp(r,name='ReplayNoAdapt',adapt=False,replay_source='MSC-GP')])
  out.extend(json.loads((D/'frozen.json').read_text())['selected']);return out
 if group=='outages':
  out=[]
  for offset in P['outage_offsets']:
   for length in P['outage_lengths']:
    for r in P['outage_tiers']:
     for q in [gp(r,name='MSC-GP'),dict(F['period'][str(r)],name='Periodic'),dict(R['constant'][str(r)],name='Constant')]:
      out.append(dict(q,name=q['name']+f'|{offset}|{length}',method=q['name'],outage_start=100+offset,outage=length,offset=offset))
  return out
 raise ValueError(group)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('group');p.add_argument('--seed',type=int,required=True);p.add_argument('--chunk',type=int);a=p.parse_args()
 cfg=configurations(a.group);cfg=cfg if a.chunk is None else cfg[a.chunk*6:(a.chunk+1)*6]
 c.configs=lambda _:cfg;c.H=D
 # Put each external chunk in a distinct result stem without invoking the frozen 12-config slice.
 group=a.group if a.chunk is None else a.group+f'-chunk{a.chunk}'
 c.run(10,a.seed,group)
