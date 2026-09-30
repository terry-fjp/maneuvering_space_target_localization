import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'thrust_review_v12'))
import json,csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager
from scenario import H
P=H.parents[1]/'output/latex/remotesensing_submission_en';
plt.rcParams.update({'font.family':['DejaVu Sans'],'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.unicode_minus':False,'pdf.fonttype':42,'legend.fontsize':8})
S=json.loads((H/'statistics/review_summary.json').read_text());F=json.loads((H/'review_frozen.json').read_text());old=json.loads((H/'frozen.json').read_text())
M=[('MSC-GP','MSC-GP','#177FA3'),('Periodic','Periodic','#DE9746'),('RIT-fine','Refined RIT','#548B6B'),('Constant','Constant','#926DB2')]
def get(ds,req,n):return next(r for r in S['tracking'] if r['dataset']==ds and r['req']==req and r['name']==n)
def save(fig,n):
 for ext in ['pdf','png']:fig.savefig(P/'figures'/f'{n}.{ext}',dpi=260,bbox_inches='tight',pad_inches=.08)
 plt.close(fig)
def grid(ax):ax.grid(alpha=.16);ax.set_axisbelow(True)
def legend(fig,ax,n=4):fig.legend(*ax.get_legend_handles_labels(),ncol=n,loc='upper center',bbox_to_anchor=(.5,1.025),frameon=False)
fig,axes=plt.subplots(2,3,figsize=(11,5.8))
for row,ds in enumerate(['original','unseen']):
 for col,req in enumerate([500,1000,1500]):
  ax=axes[row,col]
  for j,(name,lab,color) in enumerate(M):
   r=get(ds,req,name);ax.bar(j,r['laser_time'],color=color,label=lab,width=.62);ax.text(j,r['laser_time']+.7,f"{r['laser_time']:.2f}\n{r['bad_arcs']}/768",ha='center',fontsize=7,color='#BA5A53' if r['bad_arcs'] else '#344455')
  ax.set_xticks(range(4),['GP','Periodic','RIT','Const.']);ax.set_title(('Original' if row==0 else 'Held-out')+f': {req}/{req//10}',loc='left',fontsize=10);ax.set_ylabel('Effective ranging time (s)');ax.set_ylim(0,48);grid(ax)
legend(fig,axes[0,0]);fig.tight_layout(h_pad=2);save(fig,'complete')
# Fine development and frozen settings, not selected on validation.
olddev=json.loads((H/'statistics/original_development.json').read_text());dev=json.loads((H/'statistics/fine_development.json').read_text())
fig,axes=plt.subplots(1,3,figsize=(11,3.7))
for ax,req in zip(axes,[500,1000,1500]):
 for ctrl,lab,col,mark in [('gp','Prediction','#177FA3','o'),('period','Periodic','#DE9746','s'),('rit','Refined RIT','#548B6B','^'),('constant','Constant','#926DB2','D')]:
  rr=[r for r in (olddev if ctrl in ['gp','period'] else dev) if r['req']==req and r['control']==ctrl];ax.scatter([r['laser_time'] for r in rr],[r['position_peak']/req for r in rr],s=14,color=col,marker=mark,alpha=.45,label=lab)
  if ctrl in ['rit','constant']:pick=next(r for r in rr if r['name']==F[ctrl][str(req)]['name'])
  elif ctrl=='period':pick=next(r for r in rr if r['key']==str((old['period'][str(req)]['period'],old['period'][str(req)]['window'])))
  else:pick=next(r for r in rr if r['name']==old['gp'][str(req)]['name'])
  ax.scatter(pick['laser_time'],pick['position_peak']/req,s=150,marker='*',color=col,edgecolor='black',lw=.65,zorder=9)
 ax.axhline(1,color='#BA5A53',ls='--',lw=1);ax.axhline(.8,color='#8792A4',ls=':',lw=1);ax.set(xlabel='Ranging time (s)',ylabel='Position peak / task limit',title=f'{req}/{req//10}',ylim=(0,2.4));grid(ax)
legend(fig,axes[0]);fig.tight_layout();save(fig,'tradeoff')
fig,axes=plt.subplots(1,2,figsize=(10.5,3.7))
for method,lab,col in [('MSC16','MSC','#177FA3'),('SS8','SS8','#DE9746')]:
 rr=[r for r in S['budget_curves'] if r['name'].startswith(method+'@')];xx=[r['rate'] for r in rr]
 for ax,key in zip(axes,['recall','f1']):
  ax.errorbar(xx,[100*r[key] for r in rr],xerr=np.array([[r['rate']-r['rate_ci'][0],r['rate_ci'][1]-r['rate']] for r in rr]).T,color=col,marker='o',capsize=3,label=lab,lw=1.3)
  for r in rr:ax.annotate(r['name'].split('@')[1],(r['rate'],100*r[key]),xytext=(3,7),textcoords='offset points',fontsize=7,color=col)
axes[0].set_ylabel('Timely recall within 60 s (%)');axes[1].set_ylabel('F1 within 60 s (%)')
for ax in axes:ax.set_xlabel('Independent no-maneuver alerts / target-hour');grid(ax)
legend(fig,axes[0],2);fig.tight_layout();save(fig,'budget_curves')
fig,axes=plt.subplots(1,3,figsize=(10.5,3.6))
for ax,axis,vals,labels in zip(axes,['axis','range','geometry'],[[0,1,2],[500,1000,1500,2000],[0,1,2,3]],[['LOS','Transverse 1','Transverse 2'],['500','1000','1500','2000'],['Q1','Q2','Q3','Q4']]):
 for method,lab,col in [('MSC16@0.5','MSC','#177FA3'),('SS8@0.5','SS8','#DE9746')]:
  rr=[next(r for r in S['budget_strata'] if r['name']==method and r['axis']==axis and r['value']==v) for v in vals];ax.plot(range(len(vals)),[100*r['recall'] for r in rr],'o-',color=col,label=lab,lw=1.5)
 ax.set_xticks(range(len(vals)),labels);ax.set_ylabel('Timely recall (%)');grid(ax)
axes[0].set_xlabel('Thrust direction at onset');axes[1].set_xlabel('Initial slant range (km)');axes[2].set_xlabel('Initial LOS-rate quartile')
legend(fig,axes[0],2);fig.tight_layout();save(fig,'detection_strata')
fig,axes=plt.subplots(1,3,figsize=(10.8,3.6))
for ax,req in zip(axes,[500,1000,1500]):
 for ds,marker,alpha in [('original','o',.6),('unseen','^',1)]:
  for name,label,col in M:
   r=get(ds,req,name);ax.scatter(r['laser_time'],r['position_peak']/req,color=col,marker=marker,s=65,alpha=alpha,label=label if ds=='unseen' else None)
 ax.axhline(1,color='#BA5A53',ls='--');ax.set(xlabel='Ranging time (s)',ylabel='Position peak / task limit',title=f'{req}/{req//10}');grid(ax)
legend(fig,axes[0]);fig.tight_layout();save(fig,'generalization')
fig,axes=plt.subplots(2,3,figsize=(10.5,5.8))
for row,ds in enumerate(['original','unseen']):
 z=np.load(H/'statistics'/('bypass_original.npz' if row==0 else 'bypass_unseen_.npz'))['rows']
 for col,req in enumerate([500,1000,1500]):
  d=z[z[:,0]==req];ax=axes[row,col];# All points, rasterized to keep PDF small.
  ax.scatter(d[:,9],d[:,7]/req,s=1,color='#177FA3',alpha=.07,rasterized=True);ax.axvspan(.8,1.2,color='#DE9746',alpha=.12);ax.axvline(1,color='#BA5A53',ls='--');ax.axhline(1,color='#BA5A53',ls='--');ax.set(xlabel='Guarded quantity / control threshold',ylabel='Replay position error / task limit',title=('Original' if row==0 else 'Held-out')+f' {req}/{req//10}',xlim=(0,1.8),ylim=(0,1.1));grid(ax)
fig.tight_layout();save(fig,'bypass')
conditions=['ideal','delay0.5','delay1','delay2','gap10','gap30','delay1-gap10'];short=['Ideal','D0.5','D1','D2','G10','G30','D1+G10']
fig,axes=plt.subplots(2,3,figsize=(11.5,6))
for col,req in enumerate([500,1000,1500]):
 for name,lab,color in M:
  rr=[next(r for r in S['service'] if r['req']==req and r['name']==name+'|'+condition) for condition in conditions]
  axes[0,col].plot(range(7),[r['bad_arcs'] for r in rr],'o-',color=color,label=lab,ms=3,lw=1.3)
  axes[1,col].plot(range(7),[r['laser_time'] for r in rr],'o-',color=color,label=lab,ms=3,lw=1.3)
 for ax in axes[:,col]:ax.set_xticks(range(7),short,rotation=40,ha='right');grid(ax)
 axes[0,col].set_title(f'{req}/{req//10}');axes[0,col].set_ylabel('Violating trajectories / 192');axes[1,col].set_ylabel('Effective ranging time (s)')
legend(fig,axes[0,0]);fig.tight_layout(h_pad=2);save(fig,'service')
# Fresh fine-RIT timeline on the same strict-GP worst-case trajectory.
f=10;seed=260930403;target=39;d=json.loads((H/'results'/f'track_review_main_{f}_{seed}.json').read_text());z=np.load(H/'results'/f'track_review_main_{f}_{seed}.npz' if (H/'results'/f'track_review_main_{f}_{seed}.npz').exists() else H/'statistics/timeline_source.npz');a=np.load(H/'results'/f'detect_{f}_{seed}_0.npz');idx=a['names'].tolist().index('MSC16');alarms=np.flatnonzero(a['flags'][:,idx,target]);j=next(i for i,c in enumerate(d['configs']) if c['name']=='MSC-GP' and c['req']==500);t=np.arange(700)
fig,axes=plt.subplots(4,1,figsize=(10,7),sharex=True,gridspec_kw={'height_ratios':[2,1.5,1,1]})
for name,label,color in M:
 k=next(i for i,c in enumerate(d['configs']) if c['name']==name and c['req']==500);axes[0].plot(t,z['trace'][:,k,target,0],color=color,lw=1,label=label)
axes[0].axhline(500,color='#BA5A53',ls='--');axes[0].set_ylabel('Position error (m)');axes[0].legend(ncol=4,frameon=False,loc='lower center',bbox_to_anchor=(.5,1.02))
tr=z['trace'][:,j,target];axes[1].plot(t,np.max(tr[:,2:4]/[500,50],axis=1),color='#8792A4',label='Raw forecast');axes[1].plot(t,np.max(tr[:,4:6]/[500,50],axis=1),color='#177FA3',label='Guarded forecast');axes[1].axhline(1,color='#BA5A53',ls='--');axes[1].set_ylabel('Decision quantity / threshold');axes[1].legend(ncol=2,frameon=False)
axes[2].fill_between(np.arange(7000)/10,0,z['use'][:,j,target],step='post',color='#177FA3');axes[2].set(yticks=[0,1],yticklabels=['Off','On'],ylabel='Valid ranging')
for tau in [100,300,500]:
 for ax in axes[:3]:ax.axvspan(tau,tau+60,color='#DE9746',alpha=.1)
 axes[3].broken_barh([(tau,60)],(.6,.25),facecolors='#DE9746')
axes[3].vlines(alarms,0,.45,color='#BA5A53');axes[3].set(yticks=[.2,.72],yticklabels=['Alert','True thrust'],xlabel='Time (s)',xlim=(30,700),ylim=(-.1,1))
for ax in axes:grid(ax)
fig.tight_layout();save(fig,'timeline')
print('Review plots generated')
