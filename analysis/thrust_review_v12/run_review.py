import os,json,hashlib,subprocess,concurrent.futures,argparse
from scenario import H

def job(dataset,freq,seed):
 env=os.environ.copy();env['MSC_SET']=dataset;prefix='' if dataset=='original' else 'unseen_'
 if dataset=='unseen':
  with (H/'logs'/f'detect_{prefix}{freq}_{seed}.log').open('w') as f:subprocess.run(['python3',str(H/'detect.py'),'--freq',str(freq),'--seed',str(seed)],env=env,stdout=f,stderr=f,check=True)
 with (H/'logs'/f'track_review_{prefix}{freq}_{seed}.log').open('w') as f:subprocess.run(['python3',str(H/'control.py'),'--freq',str(freq),'--seed',str(seed),'--group','review_main'],env=env,stdout=f,stderr=f,check=True)
 print('DONE',dataset,freq,seed,flush=True)
def main():
 frozen=json.loads((H/'review_frozen.json').read_text())
 for name,digest in frozen['source_sha256'].items():assert hashlib.sha256((H/name).read_bytes()).hexdigest()==digest,name
 jobs=[(dataset,freq,seed) for dataset,seeds in [('original',[260930401,260930402,260930403]),('unseen',[261001401,261001402,261001403])] for freq in [5,10,15,20] for seed in seeds]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:list(p.map(lambda a:job(*a),jobs))
if __name__=='__main__':main()
