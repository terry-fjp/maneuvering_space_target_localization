from pathlib import Path
import json,re,csv
import numpy as np
D=Path(__file__).resolve().parent;ROOT=D.parents[1];P=ROOT/'output/latex/applsci_submission_en';S=json.loads((D/'summary.json').read_text())
def table(name,caption,columns,header,rows):
 text='\\begin{table}[htbp]\\caption{'+caption+'}\\label{tab:'+name+'}\n\\begin{adjustwidth}{-\\extralength}{0cm}\\centering\\small\n\\begin{tabular}{'+columns+'}\\toprule\n'+header+'\\\\\\midrule\n'+'\n'.join(' & '.join(str(c) for c in r)+'\\\\' for r in rows)+'\n\\bottomrule\\end{tabular}\\end{adjustwidth}\\end{table}\n'
 (P/'tables'/f'{name}.tex').write_text(text)
def get(ds,req,name):return next(r for r in S['validation'] if r['dataset']==ds and r['req']==req and r['name']==name)
rows=[]
for ds,label in [('original','Original'),('unseen_','Held-out')]:
 for n,title in [('MSC-GP','MSC-GP'),('FixedAdd','Zero extra margin'),('PositiveAdd',r'Fixed add ($\alpha=0.05$)'),('PositiveScale',r'Scaled ($\kappa=1.5$)')]:
  r=get(ds,1000,n);q=r['position_peak_quantiles'];rows.append([label,title,f"{r['position_rmse']:.2f}",f'{q[2]:.1f}/{q[4]:.1f}/{q[6]:.1f}',f"{r['velocity_peak']:.2f}",f"{r['bad_arcs']}/{r['bad_targets']}",f"{r['laser_time']:.2f}"])
table('guard_alternatives','Middle-tier alternatives at 10 Hz: 192 trajectories and 64 targets per row. Position-peak entries are trajectory P50/P95/maximum (m). Failures give trajectories/targets, not a ratio. Time is mean effective ranging over $[30,700)$ s. Unrestricted additive/scaling minima coincide with zero extra margin.','llrrrrr','Set & Control & $R_r$ (m) & Peak P50/P95/max (m) & $e_{v,\\max}$ (m/s) & Failures & $T_L$ (s)',rows)
rows=[]
for ds,label in [('original','Original'),('unseen_','Held-out')]:
 for name,title in [('MSC-GP','Noise + range'),('NoiseOnly','Noise only'),('RangeOnly','Range only'),('Neither','Neither'),('ReplayNoAdapt','No noise: replay')]:
  r=get(ds,1000,name);rows.append([label,title,f"{r['position_rmse']:.2f}",f"{r['velocity_rmse']:.3f}",f"{r['position_peak']:.2f}",f"{r['velocity_peak']:.2f}",f"{r['bad_arcs']}/{r['bad_targets']}",f"{r['laser_time']:.2f}"])
table('intervention_cells','Middle-tier intervention decomposition at 10 Hz, with 192 trajectories/64 targets per row. First four rows per set are closed loop; the last replays the complete MSC-GP range sequence without noise adaptation. Failures list trajectories/targets. All alerts are shared.','llrrrrrr','Set & Intervention & $R_r$ (m) & $R_v$ (m/s) & $e_{r,\\max}$ (m) & $e_{v,\\max}$ (m/s) & Failures & $T_L$ (s)',rows)
rows=[]
for req in [500,1000]:
 for length in [10,30]:
  for method in ['MSC-GP','Periodic','Constant']:
   rr=[r for r in S['outages'] if (r['req'],r['length'],r['method'])==(req,length,method)]
   span=lambda key,d:f"{min(r[key] for r in rr):.{d}f}--{max(r[key] for r in rr):.{d}f}"
   rows.append([f'{req}/{length}',method,span('bad_arcs',0),span('bad_targets',0),f"{max(r['longest_bad'] for r in rr):.1f}",f"{max(r['max_gap'] for r in rr):.1f}",span('request_time',2),span('laser_time',2)])
table('outage_phases','Laser-outage phase scan at 10 Hz. Each phase has 192 trajectories/64 targets. Ranges span five predefined offsets; longest violation and successful-range gap are maxima over all phases. Times refer to $[30,700)$; target counts are not summed across phases.','rlrrrrrr','Limit (m)/$L$ (s) & Control & Failed arcs & Failed targets & Longest (s) & Gap (s) & Requested (s) & Effective (s)',rows)
# Extend the existing forecast table with signed-tail and directional fields.
old=json.loads((ROOT/'analysis/thrust_review_v12/statistics/forecast_5.json').read_text())
rows=[]
for r in sorted(S['forecast'],key=lambda r:(r['freq'],r['req'])):
 old=next(v for v in json.loads((ROOT/f"analysis/thrust_review_v12/statistics/forecast_{r['freq']}.json").read_text()) if v['req']==r['req'])
 rows.append([r['freq'],r['req'],f"{old['position_relative_p95']:.3f}/{old['velocity_relative_p95']:.3f}",f"{r['position_under_p99']:.3f}/{r['velocity_under_p99']:.3f}",f"{r['position_under_max']:.3f}/{r['velocity_under_max']:.3f}",r['off_on'],r['on_off']])
table('forecast','Aggregate versus sequential prediction: 4288 starts per frequency/tier. Paired entries are position/velocity percentages. Underestimation is $100(B_{\\rm ref}-B_{\\rm agg})_+/B_{\\rm ref}$ at the endpoint. Decision counts use the sequential maximum within the interval, including its endpoint; arrows are aggregate $\\to$ reference.','rrrrrrr','Hz & Limit (m) & Abs. P95 (\\%) & Under P99 (\\%) & Under max (\\%) & Off$\\to$on & On$\\to$off',rows)
# Complete supplementary records, including displaced tables in readable Markdown.
md=['# S1 additional results: AS-MSCGP-20260929-R2','', 'All times are seconds. RMSE pools equal-weight trajectory MSE. Failures use all [30,700) epochs. Bootstrap is paired by target; no high-rate epoch is treated as a replicate.','']
for name in ['service500','service1000','service1500','period_validation_original','period_validation_unseen','failure_detail','peak_distribution']:
 text=(P/'tables'/f'{name}.tex').read_text();caption=text.split('\\caption{',1)[1].split('}\\label',1)[0];lines=text.split('\\toprule',1)[1].split('\\bottomrule',1)[0].replace('\\midrule','')
 cells=[]
 for line in lines.splitlines():
  if '&' not in line:continue
  line=line.strip().removesuffix('\\\\').replace('\\%','%').replace('\\','')
  cells.append([v.strip() for v in line.split('&')])
 md+=['## '+name,'',caption,'']
 if cells:
  md+=['| '+' | '.join(cells[0])+' |','| '+' | '.join(['---']*len(cells[0]))+' |']
  md+=['| '+' | '.join(row)+' |' for row in cells[1:]]
 md+=['']
md+=['## New experiments','','Full machine-readable records: `analysis/applsci_revision_20260929/summary.json`. Per-trajectory records and signed forecast starts are in its `results/` directory.','']
for key,columns in [('validation',['dataset','req','name','position_rmse','velocity_rmse','position_peak','velocity_peak','bad_arcs','bad_targets','laser_time']),('outages',['req','method','length','offset','bad_arcs','bad_targets','longest_bad','max_gap','request_time','request_windows','laser_time'])]:
 md+=['## '+key,'','| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |']
 for r in S[key]:md.append('| '+' | '.join(f'{r[k]:.4f}' if isinstance(r[k],float) else str(r[k]) for k in columns)+' |')
 md.append('')
(D/'SUPPLEMENTARY_RESULTS.md').write_text('\n'.join(md))
# Figure replaces the old limited-phase service figure, whose source remains in S1.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,axs=plt.subplots(2,3,figsize=(10.5,5.6),layout='constrained');colors={'MSC-GP':'#176C9C','Periodic':'#D67B27','Constant':'#51835D'}
for i,req in enumerate([500,1000]):
 for j,(key,title) in enumerate([('bad_arcs','Violating trajectories / 192'),('request_time','Mean requested time (s)'),('laser_time','Mean effective time (s)')]):
  ax=axs[i,j]
  for method,color in colors.items():
   for length,linestyle,marker in [(10,'-','o'),(30,'--','s')]:
    rr=sorted([r for r in S['outages'] if (r['req'],r['method'],r['length'])==(req,method,length)],key=lambda r:r['offset'])
    ax.plot([r['offset'] for r in rr],[r[key] for r in rr],color=color,ls=linestyle,marker=marker,ms=4,lw=1.3,label=f'{method}, {length} s')
  ax.set_title(f'({chr(97+i*3+j)}) {req} m / {req//10} m/s',loc='left',fontsize=10);ax.set_ylabel(title);ax.set_xticks([-20,0,20,30,50]);ax.set_xlabel('Outage offset from thrust onset (s)');ax.grid(alpha=.16)
handles,labels=axs[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside upper center',ncol=3,frameon=False)
fig.savefig(P/'figures/service_phases.pdf');plt.close(fig)
