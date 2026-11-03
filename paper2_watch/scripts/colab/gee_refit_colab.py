# ================= CELL M: re-fit the GEE for the five antibiotics and compare with the paper's TMP-SMX row =================
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
d['t'] = pd.to_datetime(d['time'], utc=True, errors='coerce'); d = d.dropna(subset=['t']); d = d[(d.t.dt.year >= 2008) & (d.t.dt.year <= 2023)]
d['y'] = (d['res'] == 'resistant').astype(int)
print('rows used:', len(d), '| by antibiotic:', d['abxn'].value_counts().to_dict())
def fit(sub, cov, yearvar):
    sub = sub.sort_values('patient')
    X = sm.add_constant(sub[[yearvar]].astype(float))
    m = sm.GEE(sub['y'], X, groups=sub['patient'], family=sm.families.Binomial(), cov_struct=cov).fit()
    b, ci = m.params[yearvar], m.conf_int().loc[yearvar]
    return np.exp(b), np.exp(ci[0]), np.exp(ci[1]), m.pvalues[yearvar]
for label, ycol in [('calendar year (2008 = 0)', lambda s: s.t.dt.year - 2008), ('fractional years since 2008-01', lambda s: (s.t - pd.Timestamp('2008-01-01', tz='UTC')).dt.days / 365.25)]:
    d['yr'] = ycol(d)
    for cname, cov in [('Independence', sm.cov_struct.Independence()), ('Exchangeable', sm.cov_struct.Exchangeable())]:
        print(f'\n==== time = {label} | working correlation = {cname} | clustered by patient ====')
        for ab in ['Ciprofloxacin', 'Gentamicin', 'Ampicillin', 'Nitrofurantoin', 'TMP-SMX']:
            try:
                o, lo, hi, p = fit(d[d['abxn'] == ab], cov, 'yr'); print(f'{ab:15s} OR per year {o:.4f} ({lo:.4f}-{hi:.4f})  p={p:.3g}')
            except Exception as e: print(ab, 'failed:', str(e)[:100])
print('\nPaper row to match: TMP-SMX 0.9821 (0.9768-0.9874)')
