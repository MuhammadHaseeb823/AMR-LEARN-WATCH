import csv,json,collections,numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
fs=[f'audit/main/f{i}/image_predictions_for_app_FULL.csv' for i in range(5)]
D=[]
for i,f in enumerate(fs):
    for r in csv.DictReader(open(f)): D.append((i,r['reference'],r['predicted'],float(r['confidence']),r['plate']))
fold=np.array([d[0] for d in D]);ref=np.array([d[1] for d in D]);pr=np.array([d[2] for d in D]);c=np.array([d[3] for d in D]);pl=np.array([d[4] for d in D])
ok=(ref==pr).astype(float)
def lg(x): x=np.clip(x,1e-3,1-1e-3);return np.log(x/(1-x))
def ece(cf,o,nb=10):
    b=np.minimum((cf*nb).astype(int),nb-1);e=0
    for k in range(nb):
        m=b==k
        if m.any(): e+=m.mean()*abs(o[m].mean()-cf[m].mean())
    return e
def brier(cf,o): return np.mean((cf-o)**2)
def ll(cf,o): cf=np.clip(cf,1e-4,1-1e-4);return -np.mean(o*np.log(cf)+(1-o)*np.log(1-cf))
pl_cal=np.zeros(len(c));iso_cal=np.zeros(len(c))
for k in range(5):
    tr=fold!=k;te=fold==k
    m=LogisticRegression(C=1e6).fit(lg(c[tr]).reshape(-1,1),ok[tr]);pl_cal[te]=m.predict_proba(lg(c[te]).reshape(-1,1))[:,1]
    iso=IsotonicRegression(y_min=0,y_max=1,out_of_bounds='clip').fit(c[tr],ok[tr]);iso_cal[te]=iso.predict(c[te])
M={'raw':c,'platt':pl_cal,'isotonic':iso_cal}
res={}
for n,v in M.items(): res[n]={'ece':ece(v,ok),'brier':brier(v,ok),'logloss':ll(v,ok)}
print(json.dumps(res,indent=1))
# cluster bootstrap over isolates
iso_ids=sorted(set(pl));idx={p:np.where(pl==p)[0] for p in iso_ids}
rng=np.random.default_rng(0);B=2000;boot={n:[] for n in M};diff={'platt':[],'isotonic':[]}
for _ in range(B):
    pick=rng.integers(0,len(iso_ids),len(iso_ids));ii=np.concatenate([idx[iso_ids[j]] for j in pick])
    e={n:ece(v[ii],ok[ii]) for n,v in M.items()}
    for n in M: boot[n].append(e[n])
    for n in diff: diff[n].append(e['raw']-e[n])
for n in M: print(n,'ECE 95%',np.percentile(boot[n],[2.5,97.5]).round(3))
for n in diff: print(n,'ECE reduction 95%',np.percentile(diff[n],[2.5,97.5]).round(3),'frac>0',np.mean(np.array(diff[n])>0))
# coverage / accuracy at calibrated thresholds
for n,v in M.items():
    print(n,[ (t,int((v>=t).sum()),round(100*(v>=t).mean(),1),round(100*ok[v>=t].mean(),1) if (v>=t).any() else None) for t in [0.5,0.7,0.8,0.9,0.95]])
# empirical bands (pooled raw)
bands=[0,.5,.7,.8,.9,.95,.99,1.0001]
rows=[]
for a,b in zip(bands[:-1],bands[1:]):
    m=(c>=a)&(c<b); 
    if m.sum(): 
        k=int(ok[m].sum());n=int(m.sum());
        # Wilson
        z=1.96;p=k/n;d=1+z*z/n;cc=p+z*z/(2*n);aa=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n));rows.append((a,min(b,1.0),n,k,round(100*p,1),round(100*(cc-aa)/d,1),round(100*(cc+aa)/d,1)))
for r in rows: print(r)
json.dump({'res':res,'bands':rows},open('cal/cal.json','w'))
np.save('cal/c.npy',c);np.save('cal/ok.npy',ok);np.save('cal/pl.npy',pl_cal);np.save('cal/iso.npy',iso_cal)
# full-data platt params for reference
m=LogisticRegression(C=1e6).fit(lg(c).reshape(-1,1),ok);print('platt all-data',m.coef_,m.intercept_)
