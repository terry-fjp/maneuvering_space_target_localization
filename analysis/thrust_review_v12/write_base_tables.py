import csv,json,hashlib
from pathlib import Path
import numpy as np
from scenario import H
P=H.parents[1]/'output/latex/remotesensing_review_v12';W=H.parents[1]/'paper-workspace/thrust_review_v12'
S=json.loads((H/'statistics/summary.json').read_text());F=json.loads((H/'frozen.json').read_text());ledger=[]
fmt=lambda x,d=2:f'{x:.{d}f}'
ci=lambda x,d=2:'['+', '.join(fmt(v,d) for v in x)+']'
names={'MSC16':'MSC','Periodic':'固定周期','RIT':'RIT','MSC-GP':'MSC-GP','NoGuard':'删除保护项','SS8-GP':'SS8替换','MSC-GP estimator':'本文估计器','EKF':'EKF','IMM-EKF':'IMM-EKF','SS2':'SS2','SS8':'SS8','SS30':'SS30'}
def table(name,cap,headers,rows,note='',wide=True):
 if name not in {'detection','detector_effect','estimators','estimator_effect','ablation','thresholds','coverage','forecast','phase'}:return
 width='\\fulllength' if wide else '\\linewidth'
 s='\\begin{table}[htbp]\n\\caption{'+cap+'}\\label{tab:'+name+'}\n'
 if wide:s+='\\begin{adjustwidth}{-\\extralength}{0cm}\\centering\n'
 s+='\\footnotesize\\setlength{\\tabcolsep}{4pt}\n\\begin{tabular*}{'+width+'}{@{\\extracolsep{\\fill}}'+'l'*len(headers)+'}\\toprule\n'+' & '.join(headers)+'\\\\\\midrule\n'
 s+='\n'.join(' & '.join(map(str,r))+'\\\\' for r in rows)+'\n\\bottomrule\\end{tabular*}\n'
 if note:s+='\\par\\smallskip\\begin{minipage}{'+width+'}\\footnotesize '+note+'\\end{minipage}\n'
 if wide:s+='\\end{adjustwidth}\n'
 s+='\\end{table}\n';p=P/'tables'/f'{name}.tex';p.write_text(s);ledger.append(dict(name=name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),headers=headers,rows=rows))
table('detection','60 s截止条件下全部2304次持续推力事件的识别结果。所有配置采用90 s抑制和2/3确认。',['方法','TP','FN','FP','精确率/\\%','及时检出/\\%','F1/\\%','时延中位/s','迟报'],[[names[r['name']],r['tp'],r['fn'],r['fp'],fmt(100*r['precision']),fmt(100*r['recall']),fmt(100*r['f1']),fmt(r['delay_median']),r['late']] for r in S['detection']],note='FP包含迟报、重复和无对应窗口的告警；时延中位数仅针对及时检出事件。未及时检出的事件始终保留在2304次分母内。')
table('detector_effect','MSC与相同管理条件下单窗口方法的配对差。',['对照','F1差/百分点','95\\%区间','及时检出率差/百分点','95\\%区间','共同事件','时延差/s'],[[r['b'],fmt(r['f1_difference']),ci(r['f1_ci']),fmt(r['recall_difference']),ci(r['recall_ci']),r['common'],fmt(r['delay_difference'])] for r in S['detection_effects']],note='差值方向为MSC减对照；时延差只在共同及时检出事件上计算。区间按64目标簇配对重采样。')
rows=[]
for req in [500,1000,1500]:
 for n in ['MSC-GP','Periodic','RIT']:
  r=next(r for r in S['tracking'] if r['req']==req and r['name']==n);rows.append([f'{req}/{req//10}',names[n],fmt(r['position_rmse']),fmt(r['velocity_rmse'],3),fmt(r['position_peak']),fmt(r['velocity_peak']),f"{r['bad_arcs']}/768",fmt(100*r['bad_fraction'],4),fmt(r['longest_bad'])])
table('complete','统一初始化后时域的全过程精度。每行768条轨迹。',['任务','策略',r'$R_r$/m',r'$R_v$/(m/s)','位置峰值/m','速度峰值/(m/s)','越限/总数','越限时间/\\%','最长越限/s'],rows)
rows=[]
for req in [500,1000,1500]:
 for src in ['MSC-GP','Periodic']:
  for r in [r for r in S['estimators'] if r['req']==req and r['source']==src]:rows.append([f'{req}/{req//10}',names[src],names[r['name']],fmt(r['position_rmse']),fmt(r['velocity_rmse'],3),fmt(r['event_position_rmse']),fmt(r['event_velocity_rmse'],3),f"{r['bad_arcs']}/768"])
table('estimators','两种公共间歇测距序列下的估计方法比较。每行768条轨迹，推力段包含2304个60 s事件窗口。',['任务','公共时序','估计器','全程位置/m','全程速度/(m/s)','推力段位置/m','推力段速度/(m/s)','越限/总数'],rows,note='误差列均为RMSE；同一任务同一时序内有效量测逐历元完全相同。')
table('estimator_effect','本文估计器减其他方法的全过程位置与速度RMSE配对差。',['任务','公共时序','对照','位置差/m','95\\%区间','速度差/(m/s)','95\\%区间'],[[f"{r['req']}/{r['req']//10}",names[r['source']],r['b'],fmt(r['position_difference']),ci(r['position_ci']),fmt(r['velocity_difference'],3),ci(r['velocity_ci'],3)] for r in S['estimator_effects']])
rows=[]
for req in [500,1000,1500]:
 a=F['gp'][str(req)];b=F['period'][str(req)];c=F['rit'][str(req)];rows.append([f'{req}/{req//10}',a['guard'],a['margin'],f"{b['period']}/{b['window']}",c['gap']])
table('selection','按共同开发判据冻结的测距控制参数。',['任务',r'$v_g$/(m/s)',r'$\gamma$',r'周期$T/D$/s',r'RIT间隔$\tau_{\max}$/s'],rows,wide=False)
rows=[]
for req in [500,1000,1500]:
 a=next(r for r in S['tracking'] if r['req']==req and r['name']=='MSC-GP')
 for n in ['Periodic','RIT']:
  b=next(r for r in S['tracking'] if r['req']==req and r['name']==n);e=next(r for r in S['effects'] if r['req']==req and r['b']==n)
  rows.append([f'{req}/{req//10}',names[n],fmt(a['laser_time']),fmt(b['laser_time']),fmt(e['saving']),ci(e['saving_ci']),fmt(100*(1-a['laser_all_time']/b['laser_all_time']))])
table('resources','相同任务约束下的等效测距工作时间。',['任务','对照','MSC-GP时间/s','对照时间/s','670 s节省/\\%','95\\%区间','700 s节省/\\%'],rows,note='主时间列使用[30,700) s；最后一列包含实际初始化。负节省表示MSC-GP工作更多。精度是否满足任务同时见表\\ref{tab:complete}，不作等RMSE比较。')
rows=[]
for req in [500,1000,1500]:
 for n in ['MSC-GP','NoGuard','SS8-GP']:
  r=next(r for r in S['tracking'] if r['req']==req and r['name']==n);rows.append([f'{req}/{req//10}',names[n],fmt(r['position_rmse']),fmt(r['velocity_rmse'],3),f"{r['bad_arcs']}/768",fmt(r['longest_bad']),fmt(r['laser_time'])])
table('ablation','当前流程的保护项消融及SS8检测器替换。各配置独立闭环。',['任务','配置','位置RMSE/m','速度RMSE/(m/s)','越限/总数','最长越限/s','工作时间/s'],rows)
strata=list(csv.DictReader((H/'statistics/tracking_strata.csv').open()));rows=[]
for req in [500,1000,1500]:
 for f in [5,10,15,20]:
  rr=[next(r for r in strata if r['name']==n and r['req']==str(req) and r['axis']=='freq' and r['value']==str(f)) for n in ['MSC-GP','Periodic','RIT']]
  rows.append([f'{req}/{req//10}',f,192,*[fmt(float(r['position_rmse'])) for r in rr],*[r['bad_arcs'] for r in rr]])
table('frequencies','分频率全过程位置精度与越限数。三方法使用相同轨迹和历元。',['任务','Hz','轨迹数','GP位置/m','周期位置/m','RIT位置/m','GP越限','周期越限','RIT越限'],rows)
table('thresholds','逐频检测门限与无机动检查。标定和独立检查各64目标、11.378目标小时。',['Hz','方法','门限','标定告警数','检查告警数','检查率','95\\%区间'],[[r['freq'],names[r['name']],fmt(r['threshold'],5),r['calibration_count'],r['check_count'],fmt(r['rate'],3),ci(r['ci'],3)] for r in S['null']],note='率单位为次/目标小时。区间按独立检查中64个目标重采样，反映有限暴露下的不确定性；共同标定目标为0.5，不保证独立检查率低于该值。')
table('coverage','MSC-GP后验协方差椭球的经验覆盖率。',['任务','位置覆盖/\\%','速度覆盖/\\%','轨迹数'],[[f"{r['req']}/{r['req']//10}",fmt(100*r['position_coverage']),fmt(100*r['velocity_coverage']),r['n']] for r in S['tracking'] if r['name']=='MSC-GP'],note='统一[30,700) s，每轨迹670f历元；先求每轨迹覆盖比例再等权汇总。每档原始历元总数6432000，不作为独立样本。使用未加保护项的后验协方差，名义椭球水平99.9\\%。',wide=False)
forecast=[]
for f in [5,10,15,20]:
 path=H/'statistics'/f'forecast_{f}.json'
 if path.exists():forecast+=json.loads(path.read_text())
if len(forecast)==12:table('forecast','合并预测与同起点逐历元参考比较。每10 s取样，首个验证种子。',['Hz','任务','起点数','位置偏差P95/\\%','速度偏差P95/\\%','决策不一致/\\%'],[[r['freq'],f"{r['req']}/{r['req']//10}",r['n'],fmt(r['position_relative_p95'],3),fmt(r['velocity_relative_p95'],3),fmt(r['decision_mismatch_percent'],3)] for r in forecast],note='末端界绝对相对偏差与秒内最大界的决策差分别检查；参考与合并预测加入相同保护项。该检查不改变正式控制指令。')
phase=[]
from summarize import agg
for seed in [260930401,260930402,260930403]:
 path=H/'results'/f'track_phases_10_{seed}.json'
 if path.exists():phase+=json.loads(path.read_text())['rows']
ps=[]
if len(phase)==3456:
 for req in [500,1000,1500]:
  for name,ph in [('Periodic',0),('Periodic-0.25',.25),('Periodic-0.5',.5),('Periodic-0.75',.75)]:ps.append(dict(req=req,phase=ph,**agg([r for r in phase if r['req']==req and r['name']==name])))
 table('phase','10 Hz固定周期的四相位敏感性。每行192条轨迹，参数不回调。',['任务',r'$\phi/T$','位置RMSE/m','位置峰值/m','越限/总数','工作时间/s'],[[f"{r['req']}/{r['req']//10}",r['phase'],fmt(r['position_rmse']),fmt(r['position_peak']),f"{r['bad_arcs']}/192",fmt(r['laser_time'])] for r in ps])
 (H/'statistics/phase.json').write_text(json.dumps(ps,indent=2))
(W/'table_ledger.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256((H/'statistics/summary.json').read_bytes()).hexdigest(),tables=ledger),ensure_ascii=False,indent=2));print('Tables',len(ledger))
