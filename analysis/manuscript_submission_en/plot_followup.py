import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'thrust_review_v12'))
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager
from scenario import H
P=H.parents[1]/'output/latex/remotesensing_submission_en';plt.rcParams.update({'font.family':['DejaVu Sans'],'font.size':9,'pdf.fonttype':42,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False})
def save(fig,n):
 fig.savefig(P/'figures'/f'{n}.pdf',bbox_inches='tight',pad_inches=.08);fig.savefig(P/'figures'/f'{n}.png',dpi=230,bbox_inches='tight',pad_inches=.08);plt.close(fig)
rows=[]
for p in (H/'results').glob('track_unseen_review_main_*.json'):rows+=json.loads(p.read_text())['rows']
a=[r for r in rows if r['req']==1000 and r['name']=='MSC-GP'];b=[r for r in rows if r['req']==1000 and r['name']=='Constant'];fig,axs=plt.subplots(1,3,figsize=(11,3.65))
for rr,label,col in [(a,'MSC-GP','#177FA3'),(b,'Constant','#926DB2')]:
 x=np.sort([r['position_peak'] for r in rr]);axs[0].plot(x,np.arange(1,len(x)+1)/len(x),label=label,color=col)
axs[0].axvline(1000,ls='--',color='#BA5A53');axs[0].set(xlabel='Trajectory position peak (m)',ylabel='Cumulative fraction',title='(a) Peaks over 768 trajectories');axs[0].legend(frameon=False,loc='lower right')
x=np.array([max(r['position_peak'] for r in b if r['target']==t) for t in range(64)]);y=np.array([max(r['position_peak'] for r in a if r['target']==t) for t in range(64)]);axs[1].scatter(x,y,c=np.where(x>1000,'#BA5A53','#177FA3'),s=23,alpha=.8);axs[1].plot([0,1300],[0,1300],ls=':',color='#8996A2');axs[1].axvline(1000,color='#BA5A53',ls='--');axs[1].axhline(1000,color='#BA5A53',ls='--');axs[1].set(xlabel='Constant: target maximum peak (m)',ylabel='MSC-GP: target maximum peak (m)',title='(b) Paired peaks of 64 targets',xlim=(0,1300),ylim=(0,1300))
mat=np.array([[sum(r['bad']>0 for r in b if r['freq']==f and r['seed']==s) for s in [261001401,261001402,261001403]] for f in [5,10,15,20]]);axs[2].imshow(mat,cmap='Blues',vmin=0,vmax=4,aspect='auto');axs[2].set(xticks=[0,1,2],xticklabels=['401','402','403'],yticks=range(4),yticklabels=['5','10','15','20'],xlabel='Seed suffix (prefix: 261001)',ylabel='Paired frequency (Hz)',title='(c) Constant-rule violations')
for i in range(4):
 for j in range(3):axs[2].text(j,i,str(mat[i,j]),ha='center',va='center',color='white' if mat[i,j]>=3 else '#243547')
for ax in axs[:2]:ax.grid(alpha=.15)
fig.tight_layout(w_pad=1.5);save(fig,'target_failure')
V=json.loads((H/'statistics/period_validation.json').read_text());S=json.loads((H/'statistics/review_summary.json').read_text());fig,axs=plt.subplots(2,3,figsize=(10.8,6.3))
for i,ds in enumerate(['original','unseen_']):
 for j,req in enumerate([500,1000,1500]):
  ax=axs[i,j];rr=[r for r in V if r['dataset']==ds and r['req']==req]
  for r in rr:
   joint=r['name'].startswith('joint');ax.scatter(r['laser_time'],r['position_peak']/req,s=65 if joint else 40,marker='s' if joint else 'o',color='#DE9746' if joint else '#548B6B',edgecolor='#BA5A53' if r['bad_arcs'] else 'white',lw=1.3,label='Joint-phase selection' if joint else None)
   if not joint:ax.annotate(str(r['phase']),(r['laser_time'],r['position_peak']/req),xytext=(3,3),textcoords='offset points',fontsize=7)
  gp=[]
  prefix='' if ds=='original' else 'unseen_'
  for p in (H/'results').glob(f'track_{prefix}review_main_10_*.json'):gp += [r for r in json.loads(p.read_text())['rows'] if r['req']==req and r['name']=='MSC-GP']
  ax.scatter(np.mean([r['laser_time'] for r in gp]),max(r['position_peak'] for r in gp)/req,marker='*',s=140,color='#177FA3',edgecolor='white',label='MSC-GP',zorder=5);ax.axhline(1,ls='--',color='#BA5A53',lw=1);ax.set(xlabel='Post-initialization ranging (s)',ylabel='Position peak / task limit',title=('Original' if i==0 else 'Held-out')+f': {req}/{req//10}');ax.grid(alpha=.15)
from matplotlib.lines import Line2D
fig.legend(handles=[Line2D([],[],marker='*',color='#177FA3',ls='',label='MSC-GP',markersize=10),Line2D([],[],marker='s',color='#DE9746',ls='',label='Joint-phase selection'),Line2D([],[],marker='o',color='#548B6B',ls='',label='Separate-phase selection')],loc='upper center',ncol=3,frameon=False)
fig.tight_layout(rect=(0,0,1,.94),h_pad=2);save(fig,'period_selection_sensitivity')
print('Follow-up figures generated')
