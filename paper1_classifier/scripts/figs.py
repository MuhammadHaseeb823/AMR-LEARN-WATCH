import csv,collections,numpy as np,matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
BL='#0072B2';GY='#999999';OR='#D55E00';GR='#009E73'
r=list(csv.DictReader(open('run021/app_validation_0210/app_vs_reference.csv')))
# ---- Fig agreement + outcomes
fig,(a,b)=plt.subplots(1,2,figsize=(11,3.9),gridspec_kw={'width_ratios':[1.1,1]})
d=np.array([float(x['max_abs_prob_diff']) for x in r if x['max_abs_prob_diff']])
a.hist(d,bins=np.linspace(0,0.012,25),color=BL,edgecolor='w'); a.axvline(np.median(d),color=OR,lw=1.2); a.text(np.median(d)+0.0002,a.get_ylim()[1]*0.9,f'median {np.median(d):.4f}',color=OR,fontsize=8)
a.set_xlabel('Largest absolute difference in any class probability (per file)'); a.set_ylabel('Files'); a.set_title(f'(a) {len(d)} files with probabilities (largest {d.max():.4f})',loc='left',fontsize=9.5,fontweight='bold')
grp={'A':'Original photographs (57)','B':'Altered copies (114)','C':'Invalid files (8)','D':'No-colony pictures (4)'}
cats=[('answered',BL,'answered'),('abstained',GY,'abstained'),('rejected_by_quality_check',OR,'refused by quality check'),('rejected_with_message',GR,'refused with message')]
y=np.arange(4)[::-1]; left=np.zeros(4)
for k,c,l in cats:
    v=np.array([sum(1 for x in r if x['category']==g and x['outcome']==k) for g in grp]); b.barh(y,v,left=left,color=c,label=l,height=.62)
    for yy,vv,ll in zip(y,v,left):
        if vv>=4: b.text(ll+vv/2,yy,vv,ha='center',va='center',color='w',fontsize=8)
    left+=v
b.set_yticks(y);b.set_yticklabels(list(grp.values()));b.set_xlabel('Files');b.legend(fontsize=7.5,frameon=False,loc='upper center',bbox_to_anchor=(0.45,-0.2),ncol=2)
b.set_title('(b) Outcome by group',loc='left',fontsize=9.5,fontweight='bold')
fig.tight_layout();fig.savefig('p1s/figS_agreement.png',dpi=200);plt.close()
# ---- Fig alterations
alts=[('png','PNG copy'),('rgba','RGBA PNG'),('big','4x upscaled'),('rot90','Rotated 90°'),('q35','JPEG quality 35'),('grey','Greyscale')]
orig={x['file'].split('_')[1]:x for x in r if x['category']=='A' and x['file'].endswith('_0.jpg')}
ans=[];ab=[];rj=[];same=[];n=[]
for k,_ in alts:
    fs=[x for x in r if x['category']=='B' and x['file'].split('_',3)[-1].startswith(k)]
    c=collections.Counter(x['outcome'] for x in fs); ans.append(c['answered']);ab.append(c['abstained']);rj.append(c['rejected_by_quality_check'])
    comp=[(x,orig[x['file'].split('_')[1]]) for x in fs if x['app_top'] and orig[x['file'].split('_')[1]]['app_top']]
    same.append(sum(x['app_top']==o['app_top'] for x,o in comp)); n.append(len(comp))
fig,(a,b,c)=plt.subplots(1,3,figsize=(11.5,3.9),gridspec_kw={'width_ratios':[1.15,1,0.9]})
y=np.arange(6)[::-1]; ans=np.array(ans);ab=np.array(ab);rj=np.array(rj)
a.barh(y,ans,color=BL,label='answered',height=.62);a.barh(y,ab,left=ans,color=GY,label='abstained',height=.62);a.barh(y,rj,left=ans+ab,color=OR,label='refused (blur check)',height=.62)
for yy,x1,x2 in zip(y,ans,ab): a.text(x1/2,yy,x1,ha='center',va='center',color='w',fontsize=8);a.text(x1+x2/2,yy,x2,ha='center',va='center',color='w',fontsize=8)
a.set_yticks(y);a.set_yticklabels([l for _,l in alts]);a.set_xlim(0,19);a.set_xlabel('Altered copies (19 each)');a.legend(fontsize=7.5,frameon=False,loc='upper center',bbox_to_anchor=(0.5,-0.2),ncol=3,handlelength=1,columnspacing=0.8)
a.set_title('(a) Outcome of altered copies',loc='left',fontsize=9.5,fontweight='bold')
b.barh(y,[100*s/m for s,m in zip(same,n)],color=[GY if s/m>=0.9 else OR for s,m in zip(same,n)],height=.62)
for yy,s,m in zip(y,same,n): b.text(100*s/m+1.5,yy,f'{s}/{m}',va='center',fontsize=8)
b.set_yticks(y);b.set_yticklabels([]);b.set_xlim(0,115);b.set_xlabel('% with the same top class as the original');b.axvline(100,color='#ccc',lw=.8)
b.set_title('(b) Top class unchanged',loc='left',fontsize=9.5,fontweight='bold')
v=['0.17.1','0.19.0','0.20.0','0.21.0'];med=[6.7,8.1,7.7,6.5];lo=[6.5,7.8,7.7,6.4];hi=[7.0,8.5,7.9,6.8]
c.errorbar(range(4),med,yerr=[np.array(med)-lo,np.array(hi)-med],fmt='o',color=BL,capsize=4)
for i,m in enumerate(med): c.text(i+0.12,m,f'{m}',va='center',fontsize=8)
c.set_xticks(range(4));c.set_xticklabels(v);c.set_xlim(-.5,3.7);c.set_ylim(0,10);c.set_ylabel('Seconds from button to answer');c.set_xlabel('Application version')
c.set_title('(c) Time to answer (median, IQR)',loc='left',fontsize=9.5,fontweight='bold')
fig.tight_layout();fig.savefig('p1s/figS_alterations.png',dpi=200);plt.close()
# ---- workflow
fig,ax=plt.subplots(figsize=(11,3.2));ax.axis('off');ax.set_xlim(0,11);ax.set_ylim(0,3.2)
def box(x,y,w,h,t,c='#E8F1F8',ec=BL):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.04,rounding_size=0.08',fc=c,ec=ec,lw=1.2));ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=8.5)
def arr(x1,y1,x2,y2): ax.annotate('',(x2,y2),(x1,y1),arrowprops=dict(arrowstyle='->',color='#555',lw=1.2))
box(0.1,1.15,2.0,0.9,'Locked suite\n183 files\nSHA-256 manifest')
box(2.9,2.0,2.4,0.9,'PyTorch reference\n(saved checkpoint)\nprobabilities, 3 views')
box(2.9,0.3,2.4,0.9,'AMR-LEARN 0.21.0\nin headless Chromium\nprobabilities, 3 views')
box(6.2,1.15,2.1,0.9,'Comparison\ntop class, decision,\nprobability difference',c='#FDF0E6',ec=OR)
box(9.0,1.15,1.9,0.9,'Report\n+ 19 behaviour tests\n+ release hashes',c='#E8F5EF',ec=GR)
arr(2.1,1.8,2.9,2.4);arr(2.1,1.4,2.9,0.8);arr(5.3,2.4,6.2,1.8);arr(5.3,0.8,6.2,1.4);arr(8.3,1.6,9.0,1.6)
ax.text(5.5,3.05,'Test workflow',fontsize=10,fontweight='bold',ha='center')
fig.savefig('p1s/figS_workflow.png',dpi=200,bbox_inches='tight');plt.close()
print(same,n,ans,ab,rj)
