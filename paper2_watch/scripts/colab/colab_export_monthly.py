# Colab cell: reduce the cleaned ARMD table to a small monthly file (n tested, n resistant) for AMR-WATCH.
# 1) Set `df` to your CLEANED susceptibility table (conflicts removed, specimen restored) and edit COL below.
import pandas as pd
print(df.columns.tolist())                     # check the column names first
COL = dict(patient='anon_id', culture='order_proc_id_coded', time='order_time_jittered_utc',
           organism='organism', antibiotic='antibiotic', result='susceptibility', specimen='specimen')  # EDIT to match
ABX = ['Ciprofloxacin','Gentamicin','Ampicillin','Nitrofurantoin','Trimethoprim/Sulfamethoxazole']   # EDIT to your exact spellings
d = df.copy()
d = d[d[COL['organism']].str.contains('Escherichia coli', case=False, na=False)]
d = d[d[COL['specimen']].str.contains('urine', case=False, na=False)]
d = d[d[COL['antibiotic']].isin(ABX)]
d['res'] = d[COL['result']].astype(str).str.strip().str.lower().map({'resistant':1,'susceptible':0})
d = d.dropna(subset=['res']).copy()
d['t'] = pd.to_datetime(d[COL['time']], utc=True)
d = d[(d.t.dt.year>=2008)&(d.t.dt.year<=2023)]
print('jittered time range:', d.t.min(), d.t.max())
d['month'] = d.t.dt.strftime('%Y-%m'); d['year'] = d.t.dt.year
def agg(x, version):
    g = x.groupby([COL['antibiotic'],'month']).res.agg(n='size', r='sum').reset_index()
    g.columns = ['antibiotic','month','n','r']; g.insert(0,'version',version); return g
# version A: every culture-antibiotic result (as in your GEE analysis)
A = agg(d,'all_results')
# version B: first isolate per patient per antibiotic per calendar year (CLSI M39-style de-duplication)
f = d.sort_values('t').drop_duplicates([COL['patient'],COL['antibiotic'],'year'], keep='first')
B = agg(f,'first_isolate_per_patient_year')
out = pd.concat([A,B]); out.to_csv('monthly_ecoli_urine.csv', index=False)
print(out.groupby(['version','antibiotic']).agg(months=('month','nunique'), tests=('n','sum'), min_n=('n','min'), median_n=('n','median')))
from google.colab import files; files.download('monthly_ecoli_urine.csv')
