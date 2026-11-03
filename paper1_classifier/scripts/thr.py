import numpy as np,json
c=np.load('cal/c.npy');ok=np.load('cal/ok.npy')
import csv
pl=[]
for i in range(5):
    for r in csv.DictReader(open(f'audit/main/f{i}/image_predictions_for_app_FULL.csv')): pl.append(r['plate'])
pl=np.array(pl);ids=sorted(set(pl));idx={p:np.where(pl==p)[0] for p in ids}
T=[0,0.5,0.7,0.8,0.9,0.95,0.99]
rng=np.random.default_rng(0);B=2000
bc={t:[] for t in T};ba={t:[] for t in T}
for _ in range(B):
    pick=rng.integers(0,len(ids),len(ids));ii=np.concatenate([idx[ids[j]] for j in pick]);cc=c[ii];oo=ok[ii]
    for t in T:
        m=cc>=t;bc[t].append(m.mean());ba[t].append(oo[m].mean() if m.any() else np.nan)
rows=[]
for t in T:
    m=c>=t;r=dict(t=t,n=int(m.sum()),cov=round(100*m.mean(),1),acc=round(100*ok[m].mean(),1),cov_ci=[round(100*x,1) for x in np.percentile(bc[t],[2.5,97.5])],acc_ci=[round(100*x,1) for x in np.nanpercentile(ba[t],[2.5,97.5])])
    rows.append(r);print(r)
json.dump(rows,open('cal/thr.json','w'))
