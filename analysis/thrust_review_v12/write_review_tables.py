import json
from pathlib import Path
from scenario import H
P=H.parents[1]/'output/latex/remotesensing_review_v12'
S=json.loads((H/'statistics/review_summary.json').read_text());F=json.loads((H/'review_frozen.json').read_text());BASE=json.loads((H/'frozen.json').read_text())
N={'Periodic':'固定周期','RIT-fine':'RIT细化','Constant':'常数项','Constant50':'中位常数项','MSC-GP':'MSC-GP','NoAlarm':'取消告警干预'}
def fmt(x,d=2):return '--' if x is None else f'{x:.{d}f}'
def ci(x,d=2):return '['+', '.join(fmt(v,d) for v in x)+']'
def table(name,cap,heads,rows,note=''):
 s='\\begin{table}[htbp]\\caption{'+cap+'}\\label{tab:'+name+'}\n\\begin{adjustwidth}{-\\extralength}{0cm}\\centering\\footnotesize\\setlength{\\tabcolsep}{3pt}\n\\begin{tabular*}{\\fulllength}{@{\\extracolsep{\\fill}}'+'l'*len(heads)+'}\\toprule\n'+' & '.join(heads)+'\\\\\\midrule\n'+'\n'.join(' & '.join(map(str,r))+'\\\\' for r in rows)+'\n\\bottomrule\\end{tabular*}\n'
 if note:s+='\\par\\smallskip\\begin{minipage}{\\fulllength}\\footnotesize '+note+'\\end{minipage}\n'
 s+='\\end{adjustwidth}\\end{table}\n';(P/'tables'/f'{name}.tex').write_text(s)
def get(ds,req,n):return next(r for r in S['tracking'] if r['dataset']==ds and r['req']==req and r['name']==n)
for ds,label in [('original','原几何'),('unseen','未参与开发的几何')]:
 rows=[]
 for req in [500,1000,1500]:
  for n in ['MSC-GP','Periodic','RIT-fine','Constant']:
   r=get(ds,req,n);rows.append([f'{req}/{req//10}',N[n],fmt(r['position_rmse']),fmt(r['velocity_rmse'],3),fmt(r['position_peak']),fmt(r['velocity_peak']),f"{r['bad_arcs']}/768",fmt(100*r['bad_fraction'],4),fmt(r['longest_bad']),fmt(r['laser_time'])])
 table('complete' if ds=='original' else 'unseen',label+'下的统一全过程评价；每行768条轨迹。',['任务','控制',r'$R_r$/m',r'$R_v$/(m/s)','位置峰值/m','速度峰值/(m/s)','越限/总数','越限时间/\\%','最长/s','测距/s'],rows)
rows=[]
for ds,label in [('original','原几何'),('unseen','未见几何')]:
 for req in [500,1000,1500]:
  for n in ['Periodic','RIT-fine','Constant']:
   r=next(e for e in S['effects'] if e['dataset']==ds and e['req']==req and e['b']==n);rows.append([label,f'{req}/{req//10}',N[n],fmt(r['saving']),ci(r['saving_ci']),get(ds,req,n)['bad_arcs']])
table('resources','初始化后MSC-GP相对各对照的测距时间差；越限不同的行不解释为相同风险下节省。',['几何','任务','对照','节省/\\%','目标簇95\\%区间','对照越限/768'],rows,note='负值表示MSC-GP使用更多时间。MSC-GP两组各任务均无观察越限；所有误差见表\\ref{tab:complete}与表\\ref{tab:unseen}。')
rows=[]
for req in [500,1000,1500]:
 r=F['rit'][str(req)];c=F['constant'][str(req)];rows.append([f'{req}/{req//10}',BASE['gp'][str(req)]['guard'],BASE['gp'][str(req)]['margin'],str(BASE['period'][str(req)]['period'])+'/'+str(BASE['period'][str(req)]['window']),r['gap'],c['quantile'],fmt(c['constant'][0]),fmt(c['constant'][1])])
table('refined_selection','细化RIT与固定协方差项的开发选择。',['任务',r'$v_g$',r'$\gamma$','周期/窗口','RIT间隔/s','常数分位/\\%','位置常数/m','速度常数/(m/s)'],rows,note='常数项保留MSC-GP同档保护速度和门限比例；所有选择仅用开发集80\\%峰值判据。')
rows=[]
for ds,label in [('original','原几何'),('unseen','未见几何')]:
 for req in [500,1000,1500]:
  for n in ['MSC-GP','Constant50','NoAlarm']:
   r=get(ds,req,n);rows.append([label,f'{req}/{req//10}',N[n],fmt(r['position_rmse']),fmt(r['velocity_rmse'],3),f"{r['bad_arcs']}/768",fmt(r['laser_time'])])
table('new_ablation','固定中位项与取消告警干预消融。',['几何','任务','配置','位置RMSE/m','速度RMSE/(m/s)','越限/总数','测距/s'],rows)
rows=[]
for r in S['delay_differences']:rows.append(['原几何' if r['dataset']=='original' else '未见几何',r['baseline'],r['common'],fmt(r['difference']),ci(r['ci'])])
table('paired_delay','MSC减各单窗口的共同及时检出事件平均时延差。',['几何','对照','共同事件数','差值/s','目标簇95\\%区间'],rows,note='每个目标的配对差之和及配对事件数同时重采样；不是把事件或历元作为独立样本。')
rows=[]
for r in S['budget_curves']:rows.append([r['name'].replace('MSC16','MSC'),r['null_count'],fmt(r['rate'],3),ci(r['rate_ci'],3),fmt(100*r['recall']),fmt(100*r['f1']),fmt(r['delay_median'])])
table('budgets','10 Hz四种无机动预算下的检测验证。',['方法@名义预算','检查告警数','实际率','95\\%区间','及时检出/\\%','F1/\\%','时延中位/s'],rows,note='名义预算与实际率单位均为次/目标小时。独立无机动暴露34.133目标小时；每个检测配置576次持续推力事件。')
rows=[]
for ds,label in [('original','原几何'),('unseen','未见几何')]:
 for req in [500,1000,1500]:
  for group,gl in [('all','全部'),('near','临界'),('off','拟关闭')]:
   r=next(r for r in S['bypass'] if r['dataset']==ds and r['req']==req and r['group']==group);rows.append([label,f'{req}/{req//10}',gl,r['n'],fmt(r['position_raw_under_percent']),fmt(r['position_guard_under_percent']),fmt(r['position_guard_under_max']),r['off_unsafe']])
table('bypass','下一秒仅测角旁路的真实位置误差与决策量检查。',['几何','任务','子集','起点数','原始低估/\\%','保护低估/\\%','最大低估/m','拟关但越限'],rows,note='临界指保护决策量/控制门限在[0.8,1.2]；拟关闭指不超过1。低估比较下一秒真实误差最大值与预测量，不以名义协方差覆盖替代。三任务分别统计。')
rows=[]
for r in S['bypass']:
 if r['group']=='all':rows.append(['原几何' if r['dataset']=='original' else '未见几何',f"{r['req']}/{r['req']//10}",fmt(r['position_guard_under_conditional_p95']),fmt(r['velocity_raw_under_percent']),fmt(r['velocity_guard_under_percent']),fmt(r['velocity_guard_under_conditional_p95']),fmt(r['velocity_guard_under_max'])])
table('bypass_velocity','旁路重放的补充低估统计。',['几何','任务','位置低估条件P95/m','速度原始低估/\\%','速度保护低估/\\%','速度低估条件P95','速度最大低估'],rows,note='条件P95仅针对真实误差大于保护预测量的起点；无低估时记--。速度幅度单位m/s。')
for req in [500,1000,1500]:
 rows=[]
 for condition in ['ideal','delay0.5','delay1','delay2','gap10','gap30','delay1-gap10']:
  for n in ['MSC-GP','Periodic','RIT-fine','Constant']:
   r=next(r for r in S['service'] if r['req']==req and r['name']==n+'|'+condition);rows.append([condition,N[n],f"{r['bad_arcs']}/192",fmt(r['longest_bad']),fmt(r['position_rmse']),fmt(r['request_windows']),fmt(r['request_time']),fmt(r['laser_time'])])
 table(f'service{req}',f'{req} m/{req//10} m/s任务的非理想服务检查（10 Hz，192轨迹）。',['服务','控制','越限/总数','最长/s','位置RMSE/m','请求窗口数','请求/s','有效/s'],rows,note='delay仅延迟测距服务；gap仅屏蔽激光，各控制使用相同掩码，光学持续。请求不撤销、不补发，返回仍为当前共同历元；执行见表\\ref{tab:service_execution}。')
print('Review tables written')
rows=[]
for ds,label in [('original','原几何'),('unseen','未见几何')]:
 for req in [500,1000,1500]:rows.append([label,f'{req}/{req//10}',*[fmt(get(ds,req,n)['laser_all_time']) for n in ['MSC-GP','Periodic','RIT-fine','Constant']],fmt(100*(1-get(ds,req,'MSC-GP')['laser_all_time']/get(ds,req,'Periodic')['laser_all_time']))])
table('full_resources','包含实际初始化的700 s全弧平均有效测距时间。',['几何','任务','MSC-GP/s','周期/s','RIT细化/s','常数项/s','GP对周期节省/\\%'],rows,note='初始化后670 s工作量见主表；节省由未舍入记录计算，未给所有轨迹机械增加30 s。')
