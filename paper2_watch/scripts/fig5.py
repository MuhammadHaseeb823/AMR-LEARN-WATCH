import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, numpy as np, json, re
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
d=json.load(open('val021.json'))
BL='#0072B2';OR='#D55E00';GY='#777777'
def get(k,name):
    for r in d[k]['rows']:
        if r[0].startswith(name): return r
def sens(r): return int(r[1])
peaks=['0.15','0.30','0.50'];ramps=['1','4','8']
def grid(name):
    G=np.zeros((3,3),int)
    for i,p in enumerate(peaks):
        for j,rp in enumerate(ramps):
            k=f'60_{p}_{rp}' ;G[i,j]=sens(get(k,name))
    return G
GD=grid('2 of 3 agree + interval');GC=grid('Count-based')
fig=plt.figure(figsize=(11.5,4.1));gs=fig.add_gridspec(1,3,width_ratios=[1,1,1.25])
for n,(G,t) in enumerate([(GD,'(a) Dashboard rule: planted rises found (of 60)'),(GC,'(b) Count-based comparison: rises found (of 60)')]):
    a=fig.add_subplot(gs[0,n]);a.imshow(G,cmap='Blues',vmin=0,vmax=60)
    for i in range(3):
        for j in range(3): a.text(j,i,G[i,j],ha='center',va='center',color='white' if G[i,j]>35 else 'black',fontsize=10)
    a.set_xticks(range(3));a.set_xticklabels(['fast\n(1 mo)','medium\n(4 mo)','slow\n(8 mo)']);a.set_yticks(range(3));a.set_yticklabels(['15%','30%','50%'])
    a.set_xlabel('Speed of the rise');a.set_ylabel('Peak resistant share');a.set_title(t,loc='left',fontsize=8.5,fontweight='bold')
    for s in a.spines.values(): s.set_visible(False)
c=fig.add_subplot(gs[0,2])
names=[('Moving average','MA'),('EWMA','EWMA'),('CUSUM','CUSUM'),('2 of 3 agree','2 of 3'),('2 of 3 agree + interval','Dashboard'),('Count-based','Count-based')]
cols=[GY,GY,GY,GY,OR,BL]
for (nm,lab),col in zip(names,cols):
    r=get('60_0.30_4',nm);s=sens(r);fa=float(r[4]);m=re.search(r'\((\d+)–(\d+)\)',r[5]);lo,hi=int(m.group(1)),int(m.group(2))
    c.errorbar(fa,100*s/60,yerr=[[100*s/60-lo],[hi-100*s/60]],fmt='o',color=col,capsize=3)
    c.annotate(lab,(fa,100*s/60),xytext=(6,-9 if lab in('EWMA','2 of 3') else 6),textcoords='offset points',fontsize=8,color=col)
c.set_xlabel('False alerts per synthetic dataset');c.set_ylabel('Planted rises found (%)');c.set_ylim(30,105);c.set_xlim(-0.5,19)
c.set_title('(c) Sensitivity against false alerts\n(30% peak, medium speed)',loc='left',fontsize=8.5,fontweight='bold')
fig.tight_layout();fig.savefig('p3_fig_grid.png',dpi=200)
print(GD,GC)
