import pandas as pd,numpy as np,glob,json
d=pd.concat([pd.read_csv(f).assign(fold=i) for i,f in enumerate(sorted(glob.glob('audit/main/f*/image_predictions_for_app_FULL.csv')))]).reset_index(drop=True)
cls=sorted(d.reference.unique()); K=len(cls); ix={c:i for i,c in enumerate(cls)}
y=d.reference.map(ix).values; p=d.predicted.map(ix).values; iso=d.plate.values
def met(y,p):
    cm=np.zeros((K,K),int); np.add.at(cm,(y,p),1)
    tp=np.diag(cm); sup=cm.sum(1); pred=cm.sum(0)
    rec=np.divide(tp,sup,out=np.zeros(K),where=sup>0); prec=np.divide(tp,pred,out=np.zeros(K),where=pred>0)
    f1=np.divide(2*prec*rec,prec+rec,out=np.zeros(K),where=(prec+rec)>0)
    present=sup>0
    return dict(acc=tp.sum()/cm.sum(),bacc=rec[present].mean(),macro_f1=f1[present].mean(),cm=cm,rec=rec,prec=prec,f1=f1,sup=sup)
m=met(y,p)
ui=np.unique(iso); idx={u:np.where(iso==u)[0] for u in ui}
rng=np.random.default_rng(0); B=2000; out={'acc':[],'bacc':[],'macro_f1':[]}
for _ in range(B):
    s=rng.choice(ui,len(ui)); ii=np.concatenate([idx[u] for u in s]); r=met(y[ii],p[ii])
    for k in out: out[k].append(r[k])
ci={k:[float(np.percentile(v,2.5)),float(np.percentile(v,97.5))] for k,v in out.items()}
# isolate-level: per species isolate counts correct share
res=dict(n=len(d),isolates=len(ui),accuracy=m['acc'],balanced_accuracy=m['bacc'],macro_f1=m['macro_f1'],ci=ci,
 per_class={c:dict(support=int(m['sup'][i]),precision=float(m['prec'][i]),recall=float(m['rec'][i]),f1=float(m['f1'][i])) for c,i in ix.items()})
json.dump(res,open('ph3/metrics.json','w'),indent=1)
np.save('ph3/cm.npy',m['cm'])
print({k:(round(v,4) if isinstance(v,float) else v) for k,v in res.items() if k in('n','isolates','accuracy','balanced_accuracy','macro_f1')},ci)
for c in cls: print(c,res['per_class'][c])
