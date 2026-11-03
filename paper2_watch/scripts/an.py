import json,numpy as np
V=['MA','EWMA','CUSUM','two','two+min5','two+wilson','dashboard','count']
def load(f): return json.load(open(f))['rows']
def summ(rows,key='fa',hitk='hit'):
    out={}
    pl=[r for r in rows if r['sc']=='planted']
    for k,v in enumerate(V):
        hits=sum(1 for r in pl if r[hitk][k]); fa=[r[key][v] for r in rows]
        out[v]=dict(hits=hits,fa_total=sum(fa),fa_per=sum(fa)/len(rows))
    return out
if __name__=='__main__':
    r=load('abl_default.json'); s=summ(r)
    for v in V: print(v,s[v])
