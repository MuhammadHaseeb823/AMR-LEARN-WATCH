# ===== AMR-WATCH / ARMD: standalone Colab cell (no editing needed) =====
# Reloads microbiology_cultures_cohort.csv, repeats the cleaning, auto-detects the columns,
# and writes monthly_ecoli_urine.csv + yearly_ecoli_urine.csv.
import glob, re, os, pandas as pd, numpy as np

# --- 1. find the file ---
pats = ['/content/**/microbiology_cultures_cohort*.csv', '/content/drive/MyDrive/**/microbiology_cultures_cohort*.csv',
        '/content/drive/MyDrive/*/*/microbiology_cultures_cohort*.csv']
hits = [h for p in pats for h in glob.glob(p, recursive=True)]
PATH = hits[0] if hits else input('Path to microbiology_cultures_cohort.csv: ').strip()
print('Using file:', PATH)
raw = pd.read_csv(PATH, low_memory=False)
print('Rows:', len(raw)); print('Columns:', raw.columns.tolist())

# --- 2. auto-detect columns ---
def pick(pred, label):
    c = [x for x in raw.columns if pred(x.lower())]
    if not c: raise SystemExit(f'Could not find a {label} column. Columns are listed above; tell me which is which.')
    return c[0]
c_pat  = pick(lambda x: x == 'anon_id', 'patient')
c_cult = pick(lambda x: 'order_proc_id' in x, 'culture/order id')
c_time = pick(lambda x: 'order_time' in x or x.endswith('_time') or 'time_jittered' in x, 'time')
c_org  = pick(lambda x: x == 'organism', 'organism')
c_abx  = pick(lambda x: x == 'antibiotic', 'antibiotic')
c_res  = pick(lambda x: x in ('susceptibility', 'suscept') or x.startswith('suscept'), 'susceptibility')
spec_cands = [x for x in raw.columns if x not in (c_org, c_abx, c_res, c_pat, c_cult, c_time)
              and raw[x].astype(str).str.contains('urine', case=False, na=False).any()
              and raw[x].nunique() < 200]
if not spec_cands: raise SystemExit('Could not find a specimen column containing "urine".')
c_spec = spec_cands[0]
print('Detected:', dict(patient=c_pat, culture=c_cult, time=c_time, organism=c_org, antibiotic=c_abx, result=c_res, specimen=c_spec))

# --- 3. clean: drop null results, drop conflicting culture-organism-antibiotic groups ---
d = raw[[c_pat, c_cult, c_time, c_org, c_abx, c_res, c_spec]].copy()
d.columns = ['patient', 'culture', 'time', 'organism', 'abx', 'res', 'specimen']
d['res'] = d['res'].astype(str).str.strip().str.lower()
d = d[~d['res'].isin(['null', 'nan', 'none', ''])]
g = d.groupby(['culture', 'organism', 'abx'])['res'].transform('nunique')
print('Rows in conflicting groups removed:', int((g > 1).sum()))
d = d[g == 1].drop_duplicates(['culture', 'organism', 'abx', 'res'])
d = d[d['res'].isin(['resistant', 'susceptible'])]
d['r'] = (d['res'] == 'resistant').astype(int)
print('Retained resistant/susceptible rows:', len(d), '| resistant share %.2f%%' % (100 * d['r'].mean()))

# --- 4. E. coli, urine, five antibiotics, 2008-2023 ---
d = d[d['organism'].astype(str).str.contains('escherichia coli', case=False, na=False)]
d = d[d['specimen'].astype(str).str.contains('urine', case=False, na=False)]
a = d['abx'].astype(str).str.strip().str.lower()
name = np.select([a == 'ciprofloxacin', a == 'gentamicin', a == 'ampicillin', a == 'nitrofurantoin',
                  a.str.contains('trimethoprim') & a.str.contains('sulfa')],
                 ['Ciprofloxacin', 'Gentamicin', 'Ampicillin', 'Nitrofurantoin', 'TMP-SMX'], default='')
d = d.assign(abx=name); d = d[d['abx'] != '']
d['t'] = pd.to_datetime(d['time'], utc=True, errors='coerce')
d = d.dropna(subset=['t']); d = d[(d.t.dt.year >= 2008) & (d.t.dt.year <= 2023)]
print('Date range after jitter:', d.t.min(), '->', d.t.max()); print('Antibiotic counts:\n', d['abx'].value_counts())
d['month'] = d.t.dt.strftime('%Y-%m'); d['year'] = d.t.dt.year

# --- 5. two versions: all results, and first isolate per patient per antibiotic per year ---
def agg(x, key, by):
    t = x.groupby(['abx', by]).r.agg(n='size', r='sum').reset_index()
    t.columns = ['antibiotic', by, 'n', 'r']; t.insert(0, 'version', key); return t
first = d.sort_values('t').drop_duplicates(['patient', 'abx', 'year'], keep='first')
monthly = pd.concat([agg(d, 'all_results', 'month'), agg(first, 'first_isolate_per_patient_year', 'month')])
yearly  = pd.concat([agg(d, 'all_results', 'year'),  agg(first, 'first_isolate_per_patient_year', 'year')])
yearly['pct_resistant'] = (100 * yearly.r / yearly.n).round(2)
monthly.to_csv('monthly_ecoli_urine.csv', index=False); yearly.to_csv('yearly_ecoli_urine.csv', index=False)
print(monthly.groupby(['version', 'antibiotic']).agg(months=('month', 'nunique'), tests=('n', 'sum'), min_n=('n', 'min'), median_n=('n', 'median')))
print(yearly[yearly.version == 'all_results'].pivot(index='year', columns='antibiotic', values='pct_resistant'))
try:
    from google.colab import files; files.download('monthly_ecoli_urine.csv'); files.download('yearly_ecoli_urine.csv')
except Exception as e: print('Download manually from the file panel:', e)
