import numpy as np,csv,json
c=np.load('cal/c.npy');ok=np.load('cal/ok.npy')
pl=[]
for i in range(5):
    for r in csv.DictReader(open(f'audit/main/f{i}/image_predictions_for_app_FULL.csv')): pl.append(r['plate'])
pl=np.array(pl);ids=sorted(set(pl));idx={p:np.where(pl==p)[0] for p in ids}
edges=[0.9,0.95,0.99,1.0001]
rng=np.random.default_rng(0);B=2000;bs=[[] for _ in range(3)]
for _ in range(B):
    pick=rng.integers(0,len(ids),len(ids));ii=np.concatenate([idx[ids[j]] for j in pick]);cc=c[ii];oo=ok[ii]
    for b in range(3):
        m=(cc>=edges[b])&(cc<edges[b+1]);bs[b].append(oo[m].mean() if m.any() else np.nan)
out=[]
for b in range(3):
    m=(c>=edges[b])&(c<edges[b+1]);ci=np.nanpercentile(bs[b],[2.5,97.5])*100
    out.append(dict(lo=edges[b],hi=min(edges[b+1],1.0),n=int(m.sum()),k=int(ok[m].sum()),acc=round(100*ok[m].mean(),1),l=round(ci[0],1),h=round(ci[1],1)));print(out[-1])
json.dump(out,open('cal/bands.json','w'))
