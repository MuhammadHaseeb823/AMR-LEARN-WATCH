import pandas as pd,numpy as np,glob,json
d=pd.concat([pd.read_csv(f) for f in sorted(glob.glob('audit/main/f*/image_predictions_for_app_FULL.csv'))]).reset_index(drop=True)
cl=sorted(d.reference.unique()); ci={c:i for i,c in enumerate(cl)}
y=d.reference.map(ci).values; p=d.predicted.map(ci).values; iso=d.plate.values
def mets(y,p):
    K=len(cl); cm=np.zeros((K,K),int)
    np.add.at(cm,(y,p),1)
    tp=np.diag(cm); sup=cm.sum(1); pred=cm.sum(0)
    rec=np.divide(tp,sup,out=np.zeros(K),where=sup>0); prec=np.divide(tp,pred,out=np.zeros(K),where=pred>0)
    f1=np.divide(2*prec*rec,prec+rec,out=np.zeros(K),where=(prec+rec)>0)
    present=sup>0
    return dict(acc=tp.sum()/cm.sum(),bacc=rec[present].mean(),macrof1=f1[present].mean()),cm,prec,rec,f1,sup
m,cm,prec,rec,f1,sup=mets(y,p)
rng=np.random.default_rng(0); ids=np.unique(iso); idx={i:np.where(iso==i)[0] for i in ids}
B=[]
for b in range(2000):
    s=rng.choice(ids,len(ids)); ii=np.concatenate([idx[i] for i in s]); B.append(mets(y[ii],p[ii])[0])
B=pd.DataFrame(B); ci95={k:[float(B[k].quantile(.025)),float(B[k].quantile(.975))] for k in B}
out=dict(overall=m,ci95=ci95,per_class=[dict(cls=c,support=int(sup[i]),precision=float(prec[i]),recall=float(rec[i]),f1=float(f1[i])) for i,c in enumerate(cl)],classes=cl,cm=cm.tolist())
json.dump(out,open('p1m/metrics.json','w'),indent=1)
print(m,ci95)
print(pd.DataFrame(out['per_class']).round(3).to_string())
