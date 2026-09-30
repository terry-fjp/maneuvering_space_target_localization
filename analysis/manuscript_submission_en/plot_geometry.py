import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'thrust_review_v12'))
import json,csv
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager
from scenario import H,ACCELS
P=H.parents[1]/'output/latex/remotesensing_submission_en';plt.rcParams.update({'font.family':['DejaVu Sans'],'font.size':9,'pdf.fonttype':42,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(10.7,4))
for file,label,col,marker in [('targets.csv','Original 64','#177FA3','o'),('unseen_targets.csv','Held-out 64','#DE9746','^')]:
 rr=list(csv.DictReader((H/'data'/file).open()));axes[0].scatter([float(r['radial_rate_m_s'])/1000 for r in rr],[float(r['los_rate_deg_s']) for r in rr],s=30,color=col,alpha=.75,marker=marker,label=label)
axes[0].set(xlabel='Initial radial velocity (km/s)',ylabel='Initial LOS rate (°/s)',title='(a) Disjoint encounter geometries');axes[0].legend(frameon=False,loc='upper center',bbox_to_anchor=(.5,1.03),ncol=2,fontsize=8);axes[0].grid(alpha=.15)
p=json.loads((H/'data/unseen_plan.json').read_text());times=np.array(p['times']);levels=np.array(p['levels']);direction=np.array(p['axes'])
for k,marker in enumerate(['o','^','s']):
 rows,cols=np.where(direction==k);sc=axes[1].scatter(times[rows,cols],rows,c=np.array(ACCELS)[levels[rows,cols]],cmap='viridis',s=16,marker=marker,vmin=.01,vmax=.2,label=['LOS','Transverse 1','Transverse 2'][k])
axes[1].set(xlabel='Thrust onset (s)',ylabel='Held-out target index',title='(b) Reassigned maneuver parameters');axes[1].legend(frameon=False,ncol=3,loc='upper center',bbox_to_anchor=(.5,1.03),fontsize=7);fig.colorbar(sc,ax=axes[1],label='Acceleration (m/s²)',pad=.02);axes[1].grid(alpha=.15);fig.tight_layout()
for ext in ['pdf','png']:fig.savefig(P/'figures'/f'geometry_holdout.{ext}',dpi=260,bbox_inches='tight')
