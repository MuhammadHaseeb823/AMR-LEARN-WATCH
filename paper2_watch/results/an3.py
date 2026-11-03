import json,numpy as np
V=['MA','EWMA','CUSUM','two','two+min5','two+wilson','dashboard','count']
rng=np.random.default_rng(0)
def run(f,tag):
    R=json.load(open(f))['rows']; pl=[r for r in R if r['sc']!='none']; no=[r for r in R if r['sc']=='none']
    out={}
    print(tag,len(pl),len(no))
    for k,v in enumerate(V):
        hit=np.array([r['hit'][k] for r in pl],int); hitA=np.array([r['hitAny'][k] for r in pl],int)
        fp=np.array([r['fa'][v] for r in pl]); fn=np.array([r['fa'][v] for r in no]); fa=np.concatenate([fp,fn])
        fAp=np.array([r['faAny'][v] for r in pl]); fAn=np.array([r['faAny'][v] for r in no]); faA=np.concatenate([fAp,fAn])
        S=[];F=[];SA=[];FA=[]
        for _ in range(2000):
            ip=rng.integers(0,len(pl),len(pl)); inn=rng.integers(0,len(no),len(no))
            S.append(hit[ip].mean()); SA.append(hitA[ip].mean()); F.append((fp[ip].sum()+fn[inn].sum())/(len(pl)+len(no))); FA.append((fAp[ip].sum()+fAn[inn].sum())/(len(pl)+len(no)))
        pc=lambda a:[round(float(np.percentile(a,2.5)),3),round(float(np.percentile(a,97.5)),3)]
        out[v]=dict(found_end=int(hit.sum()),n=len(pl),sens_end_ci=pc(S),found_any=int(hitA.sum()),sens_any_ci=pc(SA),fa_end_mean=round(float(fa.mean()),2),fa_end_ci=pc(F),fa_any_mean=round(float(faA.mean()),2),fa_any_ci=pc(FA),
          fa_end_median=float(np.median(fa)),fa_end_iqr=[float(np.percentile(fa,25)),float(np.percentile(fa,75))],fa_end_range=[int(fa.min()),int(fa.max())])
        o=out[v]; print('%-10s end %d/%d (%s)  any %d/%d  FAend %.2f %s  FAany %.2f'%(v,o['found_end'],o['n'],o['sens_end_ci'],o['found_any'],o['n'],o['fa_end_mean'],o['fa_end_ci'],o['fa_any_mean']))
    return out
res={'indep_seeds':run('abl_indep.json','indep'),'transient_outbreak':run('abl_outbreak.json','outbreak'),'default_seeds':run('abl_default.json','default')}
json.dump(res,open('extra_runs.json','w'),indent=1)
