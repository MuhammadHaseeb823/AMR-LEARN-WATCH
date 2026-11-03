import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, numpy as np, json
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
BL='#0072B2';OR='#D55E00';GY='#999999'
T=json.load(open('cal/thr.json'))
fig,(a,b)=plt.subplots(1,2,figsize=(10.2,4.1),gridspec_kw={'width_ratios':[1,1.25]})
names=['Raw\nconfidence','Logistic\nrecalibration','Isotonic\nrecalibration'];v=[0.125,0.100,0.110];lo=[0.072,0.059,0.066];hi=[0.190,0.172,0.186]
for i in range(3):
    a.errorbar(i,v[i],yerr=[[v[i]-lo[i]],[hi[i]-v[i]]],fmt='o',color=[GY,BL,BL][i],capsize=4)
    a.text(i+0.12,v[i],f'{v[i]:.3f}',va='center',fontsize=8)
a.set_xticks(range(3));a.set_xticklabels(names,fontsize=8);a.set_xlim(-.5,2.7);a.set_ylim(0,0.22);a.set_ylabel('Expected calibration error (10 bins)')
a.set_title('(a) Recalibrating on other folds',loc='left',fontweight='bold',fontsize=9.5)
cov=[t['cov'] for t in T];acc=[t['acc'] for t in T]
b.errorbar(cov,acc,yerr=[[t['acc']-t['acc_ci'][0] for t in T],[t['acc_ci'][1]-t['acc'] for t in T]],fmt='o-',color=BL,capsize=3)
for t in T:
    lab='none' if t['t']==0 else f"≥{t['t']}"
    b.text(t['cov']+1.2,t['acc']-3.2,lab,fontsize=8)
b.axhline(90,color=OR,ls=':',lw=1);b.text(100,91,'90%',color=OR,ha='right',fontsize=8)
b.set_xlim(10,105);b.set_ylim(60,102);b.set_xlabel('Photographs answered (% of 950)');b.set_ylabel('Accuracy when answered (%)')
b.set_title('(b) Threshold, coverage and accuracy',loc='left',fontweight='bold',fontsize=9.5)
fig.tight_layout();fig.savefig('cal/p1_fig_calibration.png',dpi=200)
