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
from scenario import H,ACCELS
P=H.parents[1]/'output/latex/remotesensing_submission_en';
plt.rcParams.update({'font.family':['DejaVu Sans'],'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.unicode_minus':False,'pdf.fonttype':42,'legend.fontsize':9})
C='#177FA3';O='#DE9746';G='#548B6B';N='#8792A4';R='#BA5A53'
S=json.loads((H/'statistics/summary.json').read_text());F=json.loads((H/'frozen.json').read_text());detector=F['detector']['detector']
def save(fig,n):
 for ext in ['pdf','png']:fig.savefig(P/'figures'/f'{n}.{ext}',dpi=260,bbox_inches='tight',pad_inches=.08)
 plt.close(fig)
def legend(fig,ax,n=3):fig.legend(*ax.get_legend_handles_labels(),ncol=n,loc='upper center',bbox_to_anchor=(.5,1.025),frameon=False)
def grid(ax):ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
def get(name,req):return next(r for r in S['tracking'] if r['name']==name and r['req']==req)
fig,axes=plt.subplots(1,3,figsize=(10.5,3.25));dn=['SS2','SS8','SS30',detector]
for ax,key,lab in zip(axes,['recall','precision','f1'],['(a) Timely recall (60 s)','(b) Alert precision','(c) F1 (60 s)']):
 vals=[100*next(r[key] for r in S['detection'] if r['name']==n) for n in dn];bars=ax.bar(range(4),vals,color=[N,O,G,C],width=.62)
 for b,v in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,v+.8,f'{v:.2f}',ha='center',fontsize=8)
 ax.set_xticks(range(4),['SS2','SS8','SS30','MSC']);ax.set_ylim(0,min(105,max(vals)*1.2));ax.set_ylabel('%');ax.set_title(lab,loc='left',fontsize=10);grid(ax)
fig.tight_layout();save(fig,'detection')
dr=[]
for f in [5,10,15,20]:
 for seed in F['validation_seeds']:dr+=json.loads((H/'results'/f'detect_{f}_{seed}_0.json').read_text())['rows']
ds=list(csv.DictReader((H/'statistics/detection_strata.csv').open()));fig,axes=plt.subplots(1,2,figsize=(10.5,3.8))
for name,lab,col in [(detector,'MSC',C),('SS2','SS2',N),('SS8','SS8',O),('SS30','SS30',G)]:
 values=[d if d is not None else np.inf for r in dr if r['detector']==name for d in r['delays']];xx=np.arange(61);axes[0].plot(xx,[100*np.mean(np.array(values)<=t) for t in xx],label=lab,color=col,lw=1.7)
 vals=[100*float(next(r['recall'] for r in ds if r['name']==name and r['axis']=='level' and r['value']==str(i))) for i in range(8)];axes[1].plot(ACCELS,vals,'o-',color=col,lw=1.5,ms=4,label=lab)
axes[0].set(xlabel='Time since thrust onset (s)',ylabel='Cumulative timely recall (%)',xlim=(0,60),ylim=(0,100));axes[1].set(xlabel='Thrust acceleration (m/s²)',ylabel='Timely recall within 60 s (%)',ylim=(0,100));axes[1].set_xticks(ACCELS,[f'{v:.2f}' for v in ACCELS],rotation=35)
for ax in axes:grid(ax)
legend(fig,axes[0],4);fig.tight_layout();save(fig,'deadline')
x=np.arange(3)
fig,axes=plt.subplots(2,2,figsize=(10.3,6))
for row,src in enumerate(['MSC-GP','Periodic']):
 for col,key in enumerate(['position_rmse','event_position_rmse']):
  ax=axes[row,col]
  for j,(name,lab,color) in enumerate([('MSC-GP estimator','MSC-GP estimator',C),('EKF','EKF',O),('IMM-EKF','IMM-EKF',G)]):
   y=[next(r[key] for r in S['estimators'] if r['req']==req and r['source']==src and r['name']==name) for req in [500,1000,1500]];ax.bar(x+(j-1)*.25,y,width=.23,color=color,label=lab)
  ax.set_xticks(x,['500/50','1000/100','1500/150']);ax.set_ylabel('Position RMSE (m)');ax.set_title(('MSC-GP schedule' if row==0 else 'Periodic schedule')+': '+('Complete interval' if col==0 else '60 s thrust windows'),loc='left',fontsize=10);grid(ax)
legend(fig,axes[0,0]);fig.tight_layout(h_pad=2);save(fig,'estimators')
print('Base figures generated')
