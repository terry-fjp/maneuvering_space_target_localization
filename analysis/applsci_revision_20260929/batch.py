import concurrent.futures,subprocess,os,sys
from pathlib import Path
D=Path(__file__).resolve().parent
def call(args):
 group,seed,chunk,dataset=args
 env=dict(os.environ,MSC_SET=dataset,OPENBLAS_NUM_THREADS='1')
 cmd=[sys.executable,str(D/'run.py'),group,'--seed',str(seed)]+([] if chunk is None else ['--chunk',str(chunk)])
 log=D/'results'/f'log_{group}_{dataset}_{seed}_{chunk}.txt'
 with log.open('w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
 print(args,r.returncode,flush=True)
 if r.returncode:raise RuntimeError(log.read_text())
if __name__=='__main__':
 group=sys.argv[1]
 if group=='development': jobs=[(group,260930101,i,'original') for i in range(5)]
 elif group=='outages':jobs=[(group,s,i,'original') for s in [260930401,260930402,260930403] for i in range(10)]
 else:jobs=[(group,s,None,ds) for ds,seeds in [('original',[260930401,260930402,260930403]),('unseen',[261001401,261001402,261001403])] for s in seeds]
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:list(ex.map(call,jobs))
