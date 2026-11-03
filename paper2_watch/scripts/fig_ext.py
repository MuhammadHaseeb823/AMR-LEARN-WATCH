import json, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, numpy as np
r=json.load(open('ext_out.json'))
B,O,A,INK,GR='#2a78d6','#eb6834','#1baf7a','#0b0b0b','#52514e'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#9a998f','axes.labelcolor':GR,'xtick.color':GR,'ytick.color':GR})
# ---- Figure 7: sensitivity vs false alerts, sweeps ----
fig,ax=plt.subplots(1,2,figsize=(10.5,4.6),sharey=True)
for a,(sw,key,title) in zip(ax,[('sweep_main','main','(a) Main seeds (7000 + 31i)'),('sweep_new','newseeds','(b) New seeds (50,000 + 37i)')]):
    S=r[sw]
    for name,col,mk,lab,off in [('CUSUM_h',B,'o','CUSUM, limit h = 2 to 10 SD',(8,-14)),('count_alpha',O,'s','Exact binomial, alpha 0.1 to 0.0001',(8,6)),('dashboard_minr',A,'^','Dashboard rule, minimum resistant count 1 to 8',(-4,-17))]:
        x=[max(d['fa_per_ds'],0.04) for d in S[name]]; y=[d['found'] for d in S[name]]
        a.plot(x,y,'-',color=col,lw=2,marker=mk,ms=6,mec='#fcfcfb',mew=1.2,label=lab,zorder=3)
    # fixed operating points (default settings)
    b=r['base'][key]
    for k,l,dx,dy in [('dashboard','Dashboard default (min 5)',6,-13),('count01','Count test, 0.01',-30,12),('count_BH','Count + FDR 5%',6,-12),('two','Two of three',-70,6),('MA','Moving average',6,-4),('C2','EARS-C2-style',6,-3)]:
        a.plot(b[k]['fa_per_ds'],b[k]['found'],'o',ms=9,mfc='none',mec=INK,mew=1.6,zorder=4)
        a.annotate(l,(b[k]['fa_per_ds'],b[k]['found']),xytext=(dx,dy),textcoords='offset points',fontsize=8,color=INK)
    a.set_xscale('log'); a.set_xlim(0.04,40); a.set_ylim(0,63); a.set_xlabel('False alerts per dataset (log scale)'); a.set_title(title,loc='left',fontsize=10,color=INK)
    a.grid(axis='y',color='#e6e5e0',lw=0.6); a.set_axisbelow(True)
ax[0].set_ylabel('Planted rises found, out of 60')
h,l=ax[0].get_legend_handles_labels(); fig.legend(h,l,loc='lower center',ncol=3,frameon=False,fontsize=8.5)
fig.suptitle('Sensitivity against false alerts as each threshold is varied (synthetic data, end-of-series measure; rings = shipped or default settings)',fontsize=9.5,color=INK,x=0.01,ha='left')
fig.tight_layout(rect=(0,0.07,1,0.94)); fig.savefig('p2_fig7_curves.png',dpi=200)
# ---- Figure 8: robustness to seasonality and duplicates ----
conds=[('base','None'),('season_favourable','Seasonal,\nfavourable'),('season_adverse','Seasonal,\nadverse'),('dup15','15% repeat\nisolates'),('season_adverse_dup15','Adverse season\n+ repeats')]
ms=[('dashboard','Dashboard rule',B),('count01','Count test, 0.01',O),('count_BH','Count test + FDR 5%',A),('CUSUM','CUSUM',GR)]
fig,ax=plt.subplots(1,2,figsize=(10.5,4.4),gridspec_kw={'width_ratios':[1,1]})
x=np.arange(len(conds)); w=0.2
for i,(k,l,c) in enumerate(ms):
    ax[0].bar(x+(i-1.5)*w,[r[cn]['main'][k]['fa_per_ds'] for cn,_ in conds],w*0.9,color=c,label=l)
    ax[1].bar(x+(i-1.5)*w,[r[cn]['main'][k]['found'] for cn,_ in conds],w*0.9,color=c)
for a,t,yl in [(ax[0],'(a) False alerts per dataset','False alerts per dataset'),(ax[1],'(b) Planted rises found, out of 60','Planted rises found')]:
    a.set_xticks(x); a.set_xticklabels([c[1] for c in conds],fontsize=7.5); a.set_title(t,loc='left',fontsize=10,color=INK); a.set_ylabel(yl); a.grid(axis='y',color='#e6e5e0',lw=0.6); a.set_axisbelow(True)
ax[1].set_ylim(0,66)
h,l=ax[0].get_legend_handles_labels(); fig.legend(h,l,loc='lower center',ncol=4,frameon=False,fontsize=8.5)
fig.suptitle('Effect of seasonality and duplicate isolates (main seeds; 60 planted and 60 unplanted datasets)',fontsize=9.5,color=INK,x=0.01,ha='left')
fig.tight_layout(rect=(0,0.07,1,0.94)); fig.savefig('p2_fig8_robust.png',dpi=200)
