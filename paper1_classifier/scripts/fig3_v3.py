import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, numpy as np, pandas as pd, glob
A=glob.glob('/mnt/user-data/attachments/*/')[0]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False})
BL='#0072B2';OR='#D55E00';GR='#666';GN='#009E73'
# ---- Figure 3
fig,(a,b)=plt.subplots(1,2,figsize=(9.2,4.3),gridspec_kw={'width_ratios':[1,1.25]})
folds=[('Fold 1\n(38 isolates)',75.1,59.0,90.2),('Fold 2\n(33)',86.5,77.1,92.9),('Fold 3\n(29)',64.4,43.7,84.7),('Fold 4\n(27)',86.7,77.5,94.3),('Fold 5\n(24)',58.4,38.6,77.9),('All folds\n(151)',75.8,68.6,82.7)]
for i,(n,v,l,h) in enumerate(folds):
    c=GR if i<5 else BL
    a.errorbar(i,v,yerr=[[v-l],[h-v]],fmt='o',color=c,capsize=3,ms=6 if i<5 else 8)
    a.text(i+0.13,v,f'{v:.1f}',ha='left',va='center',fontsize=8,color='#222')
a.axhline(5.3,color=OR,ls='--',lw=1); a.text(5.45,6.5,'chance 5.3%',color=OR,ha='right',fontsize=8)
a.set_xticks(range(6)); a.set_xticklabels([f[0] for f in folds],fontsize=7.5); a.set_ylim(0,102); a.set_ylabel('Accuracy per photograph (%)')
a.set_title('(a) By test fold, main run',loc='left',fontsize=9.5,fontweight='bold')
runs=[('Whole photograph, main run',75.8,68.6,82.7,BL),('  repeat, other folds A',74.8,67.8,81.9,BL),('  repeat, other folds B',69.1,61.5,76.4,BL),('  earlier CPU run',72.2,65.5,78.9,BL),
('Colony-crop model',94.6,91.7,96.9,GN),('Crop model, no-colony patches',33.6,27.1,41.5,GN),('Corner patches only',16.8,11.4,22.7,GR),('Corners, shuffled labels',4.6,1.9,8.1,GR),('Whole photograph, shuffled labels',5.5,2.6,8.5,GR),('Crop model, shuffled labels',3.6,1.3,6.6,GR)]
for i,(n,v,l,h,c) in enumerate(runs):
    y=len(runs)-1-i; b.errorbar(v,y,xerr=[[v-l],[h-v]],fmt='o',color=c,capsize=3,ms=6)
    b.text(h+1.5,y,f'{v:.1f}',va='center',fontsize=8)
b.axvline(5.3,color=OR,ls='--',lw=1); b.set_yticks(range(len(runs))); b.set_yticklabels([r[0] for r in runs][::-1],fontsize=8)
b.set_xlim(0,103); b.set_xlabel('Accuracy per photograph (%) with 95% interval'); b.set_title('(b) Runs and controls, all five folds',loc='left',fontsize=9.5,fontweight='bold')
fig.tight_layout(); fig.savefig('figs/p1_fig3_v3.png',dpi=200); plt.close(fig)
