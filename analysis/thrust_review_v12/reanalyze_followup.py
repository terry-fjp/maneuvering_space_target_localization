"""Cluster failures and actual decision-source counts from frozen outputs."""
import json,csv
from pathlib import Path
import numpy as np
from scipy.stats import binomtest
from scenario import H
from statistics_utils import BOOT,dumpcsv,effect

def main():
 rows=[]
 for p in sorted((H/'results').glob('track_*review_main_*.json')):rows+=json.loads(p.read_text())['rows']
 summary={};failures=[];strata=[];cluster=[];peakdist=[]
 for ds in ['original','unseen_']:
  for req in [500,1000,1500]:
   a=[r for r in rows if r['dataset']==ds and r['req']==req and r['name']=='MSC-GP'];assert len(a)==768
   for method in ['Periodic','RIT-fine','Constant']:
    b=[r for r in rows if r['dataset']==ds and r['req']==req and r['name']==method];assert len(b)==768
    for r in b:
     if r['bad']:
      failures.append({k:r[k] for k in ['dataset','req','name','target','norad','freq','seed','position_peak','velocity_peak','bad','samples','longest_bad','laser_time']})
    aa=np.array([sum(r['bad']>0 for r in a if r['target']==i)/12 for i in range(64)]);bb=np.array([sum(r['bad']>0 for r in b if r['target']==i)/12 for i in range(64)]);d=(aa-bb)*100
    ar=np.array([max(r['position_peak'] for r in a if r['target']==i) for i in range(64)]);br=np.array([max(r['position_peak'] for r in b if r['target']==i) for i in range(64)])
    badtargets=np.flatnonzero(bb>0);rates=[float(np.delete(d,i).mean()) for i in range(64)];rr=dict(dataset=ds,req=req,method=method,failed_tracks=int(sum(r['bad']>0 for r in b)),failed_targets=len(badtargets),target_ids=badtargets.tolist(),paired_failure_pp=float(d.mean()),failure_ci=np.percentile(d[BOOT].mean(1),[2.5,97.5]).tolist(),leave_one_target_range=[min(rates),max(rates)],target_peak_difference=float(np.mean(ar-br)),target_peak_difference_ci=np.percentile((ar-br)[BOOT].mean(1),[2.5,97.5]).tolist())
    n01=int(np.sum((aa==0)&(bb>0)));n10=int(np.sum((aa>0)&(bb==0)));rr['target_discordant_gp_only']=n10;rr['target_discordant_baseline_only']=n01;rr['target_exact_p']=float(binomtest(n01,n01+n10,.5).pvalue) if n01+n10 else 1.0
    if len(badtargets):
     x=[r for r in a if r['target'] not in badtargets];y=[r for r in b if r['target'] not in badtargets];rr['unaffected_peak_rmse_gp']=float(np.sqrt(np.mean([r['position_mse'] for r in x])));rr['unaffected_peak_rmse_baseline']=float(np.sqrt(np.mean([r['position_mse'] for r in y])))
    cluster.append(rr)
   for method in ['MSC-GP','Periodic','RIT-fine','Constant']:
    rr=[r for r in rows if r['dataset']==ds and r['req']==req and r['name']==method];pos=np.array([r['position_peak'] for r in rr]);vel=np.array([r['velocity_peak'] for r in rr]);peakdist.append(dict(dataset=ds,req=req,method=method,n=len(rr),position_quantiles=np.percentile(pos,[0,25,50,75,95,99,100]).tolist(),velocity_quantiles=np.percentile(vel,[0,25,50,75,95,99,100]).tolist()))
    for axis,vals in [('freq',[5,10,15,20]),('seed',sorted({r['seed'] for r in rr}))]:
     for val in vals:
      xx=[r for r in rr if r[axis]==val];strata.append(dict(dataset=ds,req=req,method=method,axis=axis,value=val,n=len(xx),failed_tracks=sum(r['bad']>0 for r in xx),failed_targets=len({r['target'] for r in xx if r['bad']>0})))
 summary.update(cluster=cluster,peak_distribution=peakdist,failure_strata=strata,failures=failures)
 # Trace columns gg are the pre-update protection values; cmd is OR of branches.
 triggers=[];pertrack=[]
 for p in sorted((H/'results').glob('track_*review_main_*.json')):
  doc=json.loads(p.read_text());rr=doc['rows'];ds=rr[0]['dataset'];freq=rr[0]['freq'];seed=rr[0]['seed'];ids=[j for j,c in enumerate(doc['configs']) if c['name']=='MSC-GP']
  compact=H/'statistics'/('trigger_source_'+p.stem+'.npz')
  if p.with_suffix('.npz').exists():
   z=np.load(p.with_suffix('.npz'));trace=z['trace'];selected=trace[30:][:,ids];guards=selected[...,4:6];commands=selected[...,6].astype(bool)
   np.savez_compressed(compact,guard=guards,cmd=commands,indices=np.array(ids))
  else:
   z=np.load(compact);assert z['indices'].tolist()==ids;guards=z['guard'];commands=z['cmd']
  for j,c in enumerate(doc['configs']):
   if c['name']!='MSC-GP':continue
   gg=guards[:,ids.index(j)];cmd=commands[:,ids.index(j)];limits=np.array([c['req'],c['req']/10])*c['margin'];test=gg>limits
   near=np.abs(gg-limits)<np.maximum(1e-4,np.abs(limits)*2e-7)
   assert not near[:,:,1].any(),('Ambiguous velocity threshold',p,c)
   # When velocity is safely below its threshold, saved cmd resolves any
   # float32 ambiguity in the position quantity without rerunning the filter.
   ambiguous=near[:,:,0];assert not np.any(ambiguous & test[:,:,1])
   test[:,:,0][ambiguous]=cmd[ambiguous]
   assert np.array_equal(test.any(2),cmd)
   for target in range(64):
    tt=test[:,target];active=np.r_[False,tt.any(1)[:-1]];new=tt.any(1)&(~active)
    record=dict(dataset=ds,req=c['req'],freq=freq,seed=seed,target=target,seconds=670,position_only=int(np.sum(tt[:,0]&~tt[:,1])),velocity_only=int(np.sum(tt[:,1]&~tt[:,0])),both=int(np.sum(tt.all(1))),neither=int(np.sum(~tt.any(1))),trigger_starts=int(new.sum()),max_position_ratio=float((gg[:,target,0]/limits[0]).max()),max_velocity_ratio=float((gg[:,target,1]/limits[1]).max()));pertrack.append(record)
 for ds in ['original','unseen_']:
  for req in [500,1000,1500]:
   rr=[r for r in pertrack if r['dataset']==ds and r['req']==req];triggers.append(dict(dataset=ds,req=req,trajectories=len(rr),**{key:sum(r[key] for r in rr) for key in ['seconds','position_only','velocity_only','both','neither','trigger_starts']},max_velocity_ratio=max(r['max_velocity_ratio'] for r in rr)))
 summary['triggers']=triggers
 # Actual full arc savings, not derived from rounded table cells.
 S=json.loads((H/'statistics/review_summary.json').read_text());savings=[]
 for ds in ['original','unseen']:
  for req in [500,1000,1500]:
   a=next(r for r in S['tracking'] if r['dataset']==ds and r['req']==req and r['name']=='MSC-GP');b=next(r for r in S['tracking'] if r['dataset']==ds and r['req']==req and r['name']=='Periodic');savings.append(dict(dataset=ds,req=req,postinit=100*(1-a['laser_time']/b['laser_time']),whole_arc=100*(1-a['laser_all_time']/b['laser_all_time'])))
 summary['savings']=savings
 (H/'statistics/followup_summary.json').write_text(json.dumps(summary,indent=2));dumpcsv(H/'statistics/failure_tracks.csv',failures);dumpcsv(H/'statistics/trigger_tracks.csv',pertrack);dumpcsv(H/'statistics/failure_strata.csv',strata)
 print('FOLLOWUP',json.dumps(dict(focal=next(r for r in cluster if r['dataset']=='unseen_' and r['req']==1000 and r['method']=='Constant'),triggers=triggers,savings=savings),indent=2),flush=True)
if __name__=='__main__':main()
