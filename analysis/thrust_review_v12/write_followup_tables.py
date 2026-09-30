import json
from scenario import H
# Reuse formatting without importing a module that rewrites earlier tables.
from pathlib import Path
P=H.parents[1]/'output/latex/remotesensing_review_v12'
S=json.loads((H/'statistics/followup_summary.json').read_text());D=json.loads((H/'statistics/period_development.json').read_text());V=json.loads((H/'statistics/period_validation.json').read_text())
def f(x,d=2):return f'{x:.{d}f}'
def ci(x,d=2):return '['+', '.join(f(v,d) for v in x)+']'
def table(name,caption,heads,rows,note=''):
 s='\\begin{table}[htbp]\\caption{'+caption+'}\\label{tab:'+name+'}\n\\begin{adjustwidth}{-\\extralength}{0cm}\\centering\\footnotesize\\setlength{\\tabcolsep}{3pt}\n\\begin{tabular*}{\\fulllength}{@{\\extracolsep{\\fill}}'+'l'*len(heads)+'}\\toprule\n'+' & '.join(heads)+'\\\\\\midrule\n'+'\n'.join(' & '.join(map(str,r))+'\\\\' for r in rows)+'\n\\bottomrule\\end{tabular*}\n'
 if note:s+='\\par\\smallskip\\begin{minipage}{\\fulllength}\\footnotesize '+note+'\\end{minipage}\n'
 s+='\\end{adjustwidth}\\end{table}\n';(P/'tables'/f'{name}.tex').write_text(s)
names={'Periodic':'原固定周期','RIT-fine':'RIT细化','Constant':'常数项'}
table('failure_clusters','越限在独立目标间的分布及MSC-GP减对照的目标簇配对差。',['几何','任务','对照','失败轨迹/768','失败目标/64','越限比例差/百分点','95\\%区间'],[['原组' if r['dataset']=='original' else '留出组',r['req'],names[r['method']],r['failed_tracks'],r['failed_targets'],f(r['paired_failure_pp']),ci(r['failure_ci'])] for r in S['cluster']],note='每目标12条相关轨迹。每次重采样保留其四频率和三种子；零事件列的[0,0]只是本样本Bootstrap退化区间，不是总体风险上界。')
rr=sorted([r for r in S['failures'] if r['dataset']=='unseen_' and r['req']==1000 and r['name']=='Constant'],key=lambda r:(r['target'],r['freq'],r['seed']))
table('failure_detail','留出组1000 m/100 m/s任务的常数项9条越限明细。',['目标索引','NORAD','Hz','噪声种子','位置峰值/m','速度峰值/(m/s)','最长越限/s'],[[r['target'],r['norad'],r['freq'],r['seed'],f(r['position_peak']),f(r['velocity_peak']),f(r['longest_bad'])] for r in rr],note='索引从0开始。MSC-GP在相同目标、频率和种子组合均无越限；9条轨迹来自5个目标。')
table('peak_distribution','留出组中间档每轨迹峰值分布；各方法768条。',['方法','位置中位/m','位置P95/m','位置P99/m','位置最大/m','速度中位/(m/s)','速度P95/(m/s)','速度最大/(m/s)'],[[r['method'],*[f(r['position_quantiles'][k]) for k in [2,4,5,6]],*[f(r['velocity_quantiles'][k]) for k in [2,4,6]]] for r in S['peak_distribution'] if r['dataset']=='unseen_' and r['req']==1000 and r['method'] in ['MSC-GP','Constant']],note='分位数展示轨迹分布；推断仍以64目标为簇，不把768条轨迹视为独立目标。')
table('trigger_sources','初始化后整数秒常规预测触发的支路来源。',['几何','任务','决策总数','仅位置','仅速度','二者共同','均未触发','速度量/门限最大值'],[['原组' if r['dataset']=='original' else '留出组',r['req'],r['seconds'],r['position_only'],r['velocity_only'],r['both'],r['neither'],f(r['max_velocity_ratio'],3)] for r in S['triggers']],note='每行768条轨迹×670个决策时刻，不含初始化或告警独立触发；它们仍可与常规指令取并集。计数不作为独立统计样本。')
rows=[]
for scope in ['coarse','refined']:
 for req in [500,1000,1500]:
  a=next(r for r in D['selection'] if r['scope']==scope and r['req']==req and r['rule']=='joint');b=[r for r in D['selection'] if r['scope']==scope and r['req']==req and r['rule']=='individual'];rows.append(['原候选' if scope=='coarse' else '细化候选',req,a['period'],f(a['laser_time']),'/'.join(str(r['period']) for r in b),'/'.join(f(r['laser_time']) for r in b)])
table('phase_selection','同一开发集的两类周期筛选；所选窗口均为1 s。',['候选','任务','共同可行周期/s','四相位均时/s','分别可行周期/s','分别可行工作时间/s'],rows,note='四项依次为相位0、1/4、1/2、3/4。共同规则要求四相位均满足80\\%双峰值判据，按四相位平均工作时间选参，验证执行相位0；分别规则在每相位独立筛选。细化保留原候选并补齐31--110 s的1 s窗口周期；选到110 s时受搜索边界限制，不称全局最优。')
for ds,tag in [('original','原组'),('unseen_','留出组')]:
 rows=[]
 for r in V:
  if r['dataset']!=ds:continue
  rows.append([r['req'],'共同' if r['name'].startswith('joint') else '分别',r['phase'],r['period'],f(r['position_peak']),f(r['laser_time']),f"{r['bad_arcs']}/192",f(r['saving']),ci(r['saving_ci'])])
 table('period_validation_'+('original' if ds=='original' else 'unseen'),tag+'10 Hz冻结周期敏感性验证；每配置192条轨迹。',['任务','筛选','相位/T','周期/s','位置峰值/m','工作时间/s','越限/总数','GP节省/\\%','95\\%区间'],rows,note='所有配置在开发集选择后冻结。节省为MSC-GP相对本行周期的初始化后670 s时间差；MSC-GP均无观察越限。对照有越限的行不解释为等风险节省，负值表示MSC-GP时间更多。')
print('Follow-up tables written')
