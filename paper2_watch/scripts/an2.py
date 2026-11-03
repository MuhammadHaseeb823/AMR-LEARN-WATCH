import json,numpy as np
from an import V,load
def sec(r):
    x=sorted(i for i in r['detIdx'] if i is not None); return x[1] if len(x)>=2 else None
def strict(r,k):
    if not r['hit'][k]: return 0
    if k in (0,7): return 1
    if k==1: return int(r['detIdx'][1]>=16)
    if k==2: return int(r['detIdx'][2]>=16)
    s_=sec(r); return int(s_ is not None and s_>=16)
pc=lambda a:[float(np.nanpercentile(a,2.5)),float(np.nanpercentile(a,97.5))]
res={}; rng=np.random.default_rng(0)
for tag,f in [('peak15','abl_15.json'),('peak30','abl_default.json'),('peak50','abl_50.json')]:
    R=load(f); pl=[r for r in R if r['sc']=='planted']; no=[r for r in R if r['sc']=='none']
    out={}
    for k,v in enumerate(V):
        hit=np.array([r['hit'][k] for r in pl],int); hs=np.array([strict(r,k) for r in pl],int); hitA=np.array([r['hitAny'][k] for r in pl],int)
        fa_p=np.array([r['fa'][v] for r in pl]); fa_n=np.array([r['fa'][v] for r in no]); fa=np.concatenate([fa_p,fa_n])
        faA=np.array([r['faAny'][v] for r in R])
        S=[];SS=[];F=[];P=[]
        for _ in range(2000):
            ip=rng.integers(0,60,60); inn=rng.integers(0,60,60)
            h=hit[ip].sum(); f_=fa_p[ip].sum()+fa_n[inn].sum()
            S.append(h/60); SS.append(hs[ip].sum()/60); F.append(f_/120); P.append(h/(h+f_) if h+f_ else np.nan)
        out[v]=dict(hits=int(hit.sum()),hits_strict=int(hs.sum()),hitsAny=int(hitA.sum()),sens=hit.sum()/60,sens_ci=pc(S),sens_strict=hs.sum()/60,sens_strict_ci=pc(SS),
          fa_total=int(fa.sum()),fa_mean=float(fa.mean()),fa_ci=pc(F),fa_median=float(np.median(fa)),fa_p90=float(np.percentile(fa,90)),fa_max=int(fa.max()),share_zero=float((fa==0).mean()),
          faAny_mean=float(faA.mean()),prec=float(hit.sum()/(hit.sum()+fa.sum())),prec_ci=pc(P),prec_strict=float(hs.sum()/(hs.sum()+fa.sum())),
          fa_planted_sets=float(fa_p.mean()),fa_none_sets=float(fa_n.mean()),fa_dist=fa.tolist())
    dec=[r['decoy'] for r in pl if r['decoy']]
    out['decoy_flagged']={v:int(sum(d[k] for d in dec)) for k,v in enumerate(V)}; out['decoy_n']=len(dec)
    out['target_isolates_per_month']=float(np.mean([np.mean(r['nTarget']) for r in pl]))
    res[tag]=out
json.dump(res,open('ablation.json','w'))
for tag in res:
    print(tag)
    for v in V:
        o=res[tag][v]; print(f"  {v:11s} found {o['hits']:2d} ({100*o['sens']:.0f}%, {100*o['sens_ci'][0]:.0f}-{100*o['sens_ci'][1]:.0f}) strict {o['hits_strict']:2d} ({100*o['sens_strict']:.0f}%, {100*o['sens_strict_ci'][0]:.0f}-{100*o['sens_strict_ci'][1]:.0f}) FA/ds {o['fa_mean']:.2f} anyFA {o['faAny_mean']:.2f} real-share {100*o['prec']:.0f}%/{100*o['prec_strict']:.0f}%")
