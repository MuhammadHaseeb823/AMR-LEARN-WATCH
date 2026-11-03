import json,numpy as np,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
d=json.load(open('extra_runs.json'))
exps=[('default_seeds','Default seeds\n(persistent rise)'),('indep_seeds','New seeds\n(persistent rise)'),('transient_outbreak','Transient outbreak\n(months 15-18)')]
rules=[('two','Two of three','#2a6f97'),('dashboard','Dashboard rule','#b3261e'),('count','Count-based','#2e7d32')]
plt.rcParams.update({'font.size':9})
fig,ax=plt.subplots(1,3,figsize=(14,4.2))
w=0.26
for pi,(key,ttl) in enumerate([('end','(a) Rises found, judged at the end of the series (%)'),('any','(b) Rises found, judged at any month 12 to 24 (%)')]):
    a=ax[pi]
    for ri,(r,lab,c) in enumerate(rules):
        v=[100*d[e][r]['found_'+key]/d[e][r]['n'] for e,_ in exps]
        lo=[100*d[e][r]['sens_'+key+'_ci'][0] for e,_ in exps]; hi=[100*d[e][r]['sens_'+key+'_ci'][1] for e,_ in exps]
        x=np.arange(3)+(ri-1)*w
        a.bar(x,v,w,color=c,label=lab); a.errorbar(x,v,yerr=[np.array(v)-lo,np.array(hi)-v],fmt='none',ecolor='k',capsize=2,lw=.8)
    a.set_xticks(range(3)); a.set_xticklabels([l for _,l in exps]); a.set_ylim(0,105); a.set_title(ttl,loc='left',fontsize=9.5,fontweight='bold')
ax[1].legend(frameon=False,fontsize=8,loc='lower left',bbox_to_anchor=(0,-0.42),ncol=3)
a=ax[2]
for ri,(r,lab,c) in enumerate(rules):
    for j,(key,hatch) in enumerate([('end',''),('any','//')]):
        v=[d[e][r]['fa_'+key+'_mean'] for e,_ in exps[:2]]
        x=np.arange(2)*1.3+(ri-1)*w*1.0+ (j-0.5)*w/2.2
        a.bar(x,v,w/2.2,color=c,hatch=hatch,edgecolor='white' if not hatch else 'k',lw=.4)
a.set_xticks(np.arange(2)*1.3); a.set_xticklabels(['Default seeds','New seeds']); a.set_ylabel('False alerts per dataset'); a.set_title('(c) False alerts: solid = end of series, hatched = any month 12 to 24',loc='left',fontsize=9,fontweight='bold')
for s in ax: s.spines[['top','right']].set_visible(False)
fig.tight_layout(); fig.savefig('fig_extra.png',dpi=200)
