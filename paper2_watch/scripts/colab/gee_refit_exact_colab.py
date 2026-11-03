# ================= CELL N: the GEE again, with January 2008 removed as in the paper (Independence, calendar year) =================
# Self-contained: it connects Drive and finds the ARMD file itself. Takes several minutes. Nothing is changed in Drive.
from google.colab import drive
drive.mount('/content/drive')
import glob
found = sorted(set(glob.glob('/content/drive/MyDrive/**/microbiology_cultures_cohort*.csv', recursive=True)))
print('Using file:', found[0] if found else 'NONE FOUND')
if not found: raise SystemExit('The ARMD file is not in this Drive. Use the Drive where cell A found it.')
import numpy as np, pandas as pd, statsmodels.api as sm
print('statsmodels', sm.__version__ if hasattr(sm, '__version__') else '')
raw = pd.read_csv(found[0], low_memory=False,
                  usecols=['anon_id', 'order_proc_id_coded', 'order_time_jittered_utc', 'organism', 'antibiotic', 'susceptibility', 'culture_description'])
d = raw.rename(columns={'anon_id': 'patient', 'order_proc_id_coded': 'culture', 'order_time_jittered_utc': 'time', 'susceptibility': 'res', 'antibiotic': 'abx'}).copy()
d['res'] = d['res'].astype(str).str.strip().str.lower()
d = d[~d['res'].isin(['null', 'nan', 'none', ''])]
g = d.groupby(['culture', 'organism', 'abx'])['res'].transform('nunique'); d = d[g == 1].drop_duplicates(['culture', 'organism', 'abx', 'res'])
d = d[d['res'].isin(['resistant', 'susceptible'])]
d = d[d['organism'].astype(str).str.contains('escherichia coli', case=False, na=False) & d['culture_description'].astype(str).str.contains('urine', case=False, na=False)]
a = d['abx'].astype(str).str.strip().str.lower()
d['abxn'] = np.select([a == 'ciprofloxacin', a == 'gentamicin', a == 'ampicillin', a == 'nitrofurantoin', a.str.contains('trimethoprim') & a.str.contains('sulfa')],
                      ['Ciprofloxacin', 'Gentamicin', 'Ampicillin', 'Nitrofurantoin', 'TMP-SMX'], default='')
d = d[d['abxn'] != '']
d['t'] = pd.to_datetime(d['time'], utc=True, errors='coerce'); d = d.dropna(subset=['t']); d = d[(d.t >= pd.Timestamp('2008-02-01', tz='UTC')) & (d.t.dt.year <= 2023)]   # February 2008 to December 2023, as in the paper
d['y'] = (d['res'] == 'resistant').astype(int)
print('rows used:', len(d), '| by antibiotic:', d['abxn'].value_counts().to_dict())

d['yr'] = d.t.dt.year - 2008
print('Paper Table 4 for comparison: Cipro 1.0056 (0.9987-1.0125) p=0.110 | Gent 0.9993 (0.9902-1.0085) p=0.881 | Amp 0.9926 (0.9879-0.9974) p=0.002 | Nitro 0.9386 (0.9185-0.9591) | TMP-SMX 0.9821 (0.9768-0.9874)\n')
for ab in ['Ciprofloxacin', 'Gentamicin', 'Ampicillin', 'Nitrofurantoin', 'TMP-SMX']:
    sub = d[d['abxn'] == ab].sort_values('patient')
    X = sm.add_constant(sub[['yr']].astype(float))
    m = sm.GEE(sub['y'], X, groups=sub['patient'], family=sm.families.Binomial(), cov_struct=sm.cov_struct.Independence()).fit()
    ci = m.conf_int().loc['yr']
    print(f"{ab:15s} n={len(sub):6d} OR {np.exp(m.params['yr']):.4f} ({np.exp(ci[0]):.4f}-{np.exp(ci[1]):.4f}) p={m.pvalues['yr']:.3g}")
