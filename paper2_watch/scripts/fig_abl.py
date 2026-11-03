import json,numpy as np,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R=json.load(open('ablation.json'))['peak30']
V=['MA','EWMA','CUSUM','two','two+min5','two+wilson','dashboard','count']
L={'MA':'Moving average','EWMA':'EWMA','CUSUM':'CUSUM','two':'Two of three','two+min5':'Two of three + min 5','two+wilson':'Two of three + Wilson','dashboard':'Dashboard rule','count':'Count-based'}
col={'MA':'#7f8c9a','EWMA':'#7f8c9a','CUSUM':'#7f8c9a','two':'#2a6f97','two+min5':'#e07a1f','two+wilson':'#e07a1f','dashboard':'#b3261e','count':'#2e7d32'}
fig,ax=plt.subplots(1,3,figsize=(14,4.8),dpi=200,gridspec_kw={'width_ratios':[1.1,1.1,1]})
a=ax[0]
for v in V:
    o=R[v]; x=o['fa_mean']; y=100*o['sens_strict']
    a.errorbar(x,y,yerr=[[y-100*o['sens_strict_ci'][0]],[100*o['sens_strict_ci'][1]-y]],xerr=[[x-o['fa_ci'][0]],[o['fa_ci'][1]-x]],fmt='o',color=col[v],ms=6,capsize=2,lw=1)
off={'MA':(0.4,-1),'EWMA':(-5.2,-6),'CUSUM':(-1.5,-6.5),'two':(-4.2,5),'two+min5':(0.5,4),'two+wilson':(0.5,-1),'dashboard':(0.5,-9),'count':(0.5,-1)}
pos={'MA':(5.2,84),'EWMA':(10.0,86),'CUSUM':(15.0,80),'two':(12.4,47),'two+min5':(4.6,28),'two+wilson':(0.1,66),'dashboard':(0.6,14),'count':(2.2,92)}
for v in V: a.annotate(L[v],(R[v]['fa_mean'],100*R[v]['sens_strict']),xytext=pos[v],fontsize=7,arrowprops=dict(arrowstyle='-',color='#888',lw=0.6,shrinkA=1,shrinkB=3),va='center')
a.set_xlabel('False alerts per dataset (end of series)');a.set_ylabel('Planted rises flagged at the end of the series (%)');a.set_ylim(0,105);a.set_xlim(-0.5,19)
a.set_title('(a) Sensitivity against false alerts\n30% peak, 60 + 60 datasets, 95% intervals (resampling datasets)',fontsize=8)
b=ax[1]
data=[R[v]['fa_dist'] for v in V]
bp=b.boxplot(data,orientation='horizontal',tick_labels=[L[v] for v in V],patch_artist=True,widths=0.6,medianprops=dict(color='k'),flierprops=dict(markersize=2))
for p_,v in zip(bp['boxes'],V): p_.set_facecolor(col[v]);p_.set_alpha(0.55)
b.invert_yaxis();b.tick_params(axis='y',labelsize=7);b.set_xlabel('False alerts in one dataset (40 series)')
b.set_title('(b) Distribution of false alerts across the 120 datasets',fontsize=8)
c=ax[2]; y=np.arange(len(V)); h=0.38
c.barh(y-h/2,[R[v]['fa_mean'] for v in V],h,color='#2a6f97',label='Flagged at the end of the series');c.barh(y+h/2,[R[v]['faAny_mean'] for v in V],h,color='#e0a31f',label='Flagged at any month, 12 to 24')
c.set_yticks(y);c.set_yticklabels([L[v] for v in V],fontsize=7);c.invert_yaxis();c.set_xlabel('False alerts per dataset');c.legend(fontsize=7,loc='lower right')
c.set_title('(c) Two ways of counting a false alert',fontsize=8)
fig.tight_layout();fig.savefig('fig_ablation.png')
