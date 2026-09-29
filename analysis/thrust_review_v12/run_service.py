import concurrent.futures,subprocess,json
from scenario import H
from configurations import review_configs

def job(args):
 seed,chunk=args
 with (H/'logs'/f'service_{seed}_{chunk}.log').open('w') as f:subprocess.run(['python3',str(H/'control.py'),'--freq','10','--seed',str(seed),'--group','review_service','--chunk',str(chunk)],stdout=f,stderr=f,check=True)
 print('SERVICE',seed,chunk,'DONE',flush=True)
if __name__=='__main__':
 jobs=[(seed,i) for seed in [260930401,260930402,260930403] for i in range((len(review_configs('review_service'))+11)//12)]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(job,jobs))
