from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent; H=D.parent/'thrust_review_v12'
s=(H/'control.py').read_text()
changes={
"d=np.load(H/'results'/": "d=np.load(__import__('scenario').H/'results'/",
'noalarm=np.repeat(': 'adapt_enabled=np.repeat([q.get("adapt",True) for q in cfg],n);burst_enabled=np.repeat([q.get("burst",True) for q in cfg],n)\n outage_start=np.repeat([q.get("outage_start",80) for q in cfg],n)\n noalarm=np.repeat(',
'f.predict(dt,t-last<DURATION)':'f.predict(dt,(t-last<DURATION)&adapt_enabled)',
'np.where(t-last[ids]<DURATION,3e-4,1e-7)':'np.where((t-last[ids]<DURATION)&adapt_enabled[ids],3e-4,1e-7)',
'cmd[ids]=np.any(gg[ids]>':'for a in ids:\n     q=cfg[a//n]\n     if "add_fraction" in q:gg[a]=bb[a]+q["add_fraction"]*np.array([req[a],req[a]/10])\n     if "cov_scale" in q:gg[a]=bb[a]*np.sqrt(q["cov_scale"])\n    cmd[ids]=np.any(gg[ids]>',
'(np.mod(t-80,200)<outage)&(t>=80)':'(np.mod(t-outage_start,200)<outage)&(t>=outage_start)',
'use=delivered&available&(~blocked)':'use=delivered&available&(~blocked)\n  for j,q in enumerate(cfg):\n   if "replay_source" in q:\n    src=next(k for k,v in enumerate(cfg) if v["name"]==q["replay_source"] and v["req"]==q["req"])\n    use[j*n:(j+1)*n]=use[src*n:(src+1)*n]',
'until[alarm]=t+5+dt':'until[alarm&burst_enabled]=t+5+dt',
"if group not in ['development','review_development'] else None":"if group=='validation' else None",
"if error is not None:np.savez_compressed(stem.with_suffix('.npz'),error=error,use=usehist,trace=trace)":"if error is not None:np.savez_compressed(stem.with_suffix('.npz'),error=error,use=usehist,trace=trace)",
}
for old,new in changes.items():
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
(D/'extended_control.py').write_text('"""Derived frozen controller; explicit review-only switches. See prepare.py."""\n'+s)
protocol=dict(release='AS-MSCGP-20260929-R2',source_sha256=hashlib.sha256((H/'control.py').read_bytes()).hexdigest(),development_seed=260930101,frequency=10,add_fraction=[i/20 for i in range(15)],cov_scale=[1,1.5,2,3,4,6,9,16,25,36,64,100],guard_tier=1000,rule='Both full-arc peaks <=0.8 task limits on original 64 development targets; minimum mean post-initialization effective ranging time; ties use smaller parameter.',validation_seeds={'original':[260930401,260930402,260930403],'unseen':[261001401,261001402,261001403]},factorial_tiers=[500,1000,1500],outage_offsets=[-20,0,20,30,50],outage_lengths=[10,30],outage_tiers=[500,1000],outage_seed_rule='All three original validation seeds; start at 100+offset+200j, clipped to [30,700); laser only; identical exogenous mask for all controllers',bootstrap='4000 ordinary paired target resamples, seed 260929; equal target and seed weights, unstratified')
(D/'protocol.json').write_text(json.dumps(protocol,indent=2))
