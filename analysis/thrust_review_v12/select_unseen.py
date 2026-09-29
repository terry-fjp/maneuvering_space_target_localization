"""Freeze unseen NORAD targets using geometry only, never tracking errors."""
from pathlib import Path
import csv,json,hashlib
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
from sgp4.api import Satrec,SatrecArray,jday
from engine import rk4
from numerics import acceleration
H=Path(__file__).resolve().parent
MU=3.986004418e14;RE=6378137.
def main():
 old=list(csv.DictReader((H/'data/targets.csv').open()));excluded={int(r['norad']) for r in old};lines=(H/'data/starlink_catalogue.tle').read_text().splitlines();sats=[];records=[]
 for j in range(0,len(lines),3):
  sat=Satrec.twoline2rv(lines[j+1],lines[j+2])
  if sat.satnum not in excluded and 300<((MU/(sat.no_kozai/60)**2)**(1/3)-RE)/1000<650:sats.append(sat);records.append(lines[j:j+3])
 inc=np.deg2rad(60);rad=RE+800e3;x=np.array([rad,0,0,0,np.sqrt(MU/rad)*np.cos(inc),np.sqrt(MU/rad)*np.sin(inc)])
 def rhs(t,x):return np.r_[x[3:],acceleration(x[None,:3])[0]]
 sol=solve_ivp(rhs,[0,21600],x,method='DOP853',rtol=1e-11,atol=1e-8,dense_output=True)
 observer=lambda t:sol.sol(t)
 ts=np.arange(0,21601,60.);jd,fr=jday(2026,8,23,0,0,0);err,rs,vs=SatrecArray(sats).sgp4(np.full(ts.size,jd),fr+ts/86400);ranges=np.linalg.norm(rs*1000-observer(ts).T[None,:,:3],axis=2)
 chosen=[];used=set();tle=[]
 for km in [500,1000,1500,2000]:
  cand=[]
  for idx in range(len(sats)):
   crosses=np.flatnonzero((ranges[idx,:-1]-km*1000)*(ranges[idx,1:]-km*1000)<=0)
   for k in crosses:
    if k+12<len(ts) and err[idx,k]==0 and np.max(ranges[idx,k+1:k+12])<=1995e3:cand.append((sats[idx].satnum,k,idx))
  for _,k,idx in sorted(cand):
   if sats[idx].satnum in used:continue
   def state(t):
    e,r,v=sats[idx].sgp4(jd,fr+t/86400);assert e==0;return np.r_[r,v]*1000
   t0=brentq(lambda t:np.linalg.norm(state(t)[:3]-observer(t)[:3])-km*1000,ts[k],ts[k+1],xtol=1e-6);x0=state(t0);o0=observer(t0);xx=x0[None].copy();oo=o0[None].copy();dist=[]
   for _ in range(701):dist.append(float(np.linalg.norm(xx[:,:3]-oo[:,:3])));xx=rk4(xx,1);oo=rk4(oo,1)
   if max(dist)>2000e3+1:continue
   d=x0[:3]-o0[:3];v=x0[3:]-o0[3:];los=d/np.linalg.norm(d)
   chosen.append(dict(target=len(chosen),name=records[idx][0].removeprefix('0 '),norad=sats[idx].satnum,range_bin_km=km,epoch_offset_s=t0,range_min_km=min(dist)/1000,range_max_km=max(dist)/1000,los_rate_deg_s=np.rad2deg(np.linalg.norm(v-los*(v@los))/np.linalg.norm(d)),radial_rate_m_s=float(v@los),inclination_deg=np.rad2deg(sats[idx].inclo),**{f'x{j}':x0[j] for j in range(6)},**{f'o{j}':o0[j] for j in range(6)}));used.add(sats[idx].satnum);tle+=records[idx]
   if sum(r['range_bin_km']==km for r in chosen)==16:break
  assert sum(r['range_bin_km']==km for r in chosen)==16;print(km,len(chosen),flush=True)
 with (H/'data/unseen_targets.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=chosen[0]);w.writeheader();w.writerows(chosen)
 (H/'data/unseen_selected.tle').write_text('\n'.join(tle)+'\n')
 rng=np.random.default_rng(261001002);event_times=np.stack([rng.integers(a,b+1,64) for a,b in [(80,120),(265,335),(465,535)]],axis=1);levels=np.stack([rng.permutation(np.tile(np.arange(8),8)) for _ in range(3)],axis=1);axes=np.stack([rng.permutation(np.arange(64)%3) for _ in range(3)],axis=1)
 plan=dict(seed=261001002,times=event_times.tolist(),levels=levels.tolist(),axes=axes.tolist(),duration=60,excluded_norad=sorted(excluded),selected_norad=sorted(used),selection='geometric screening only; disjoint NORAD identifiers');(H/'data/unseen_plan.json').write_text(json.dumps(plan,indent=2));assert not excluded&used
 (H/'data/unseen_input_hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [H/'data/unseen_targets.csv',H/'data/unseen_plan.json',H/'data/starlink_catalogue.tle']},indent=2))
if __name__=='__main__':main()
