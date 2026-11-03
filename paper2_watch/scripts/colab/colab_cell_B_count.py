# CELL B: count the result types (no typing needed; it uses the first file found by CELL A)
import pandas as pd
try:
    PATH = found[0]
except Exception:
    raise SystemExit('Run CELL A first, and it must list at least one file.')
print('Using file:', PATH)
raw = pd.read_csv(PATH, low_memory=False)
print('Total rows:', len(raw))
print('Columns:', raw.columns.tolist())
org = raw['organism'].astype(str).str.contains('escherichia coli', case=False, na=False)
spec = [c for c in raw.columns if raw[c].astype(str).str.contains('urine', case=False, na=False).any() and raw[c].nunique() < 200][0]
print('Specimen column used:', spec)
sub = raw[org & raw[spec].astype(str).str.contains('urine', case=False, na=False)]
print('E. coli urine rows:', len(sub))
print('--- ALL antibiotics ---')
print(sub['susceptibility'].astype(str).str.strip().str.lower().value_counts(dropna=False))
five = sub['antibiotic'].astype(str).str.lower().isin(['ciprofloxacin','gentamicin','ampicillin','nitrofurantoin','trimethoprim/sulfamethoxazole','trimethoprim-sulfamethoxazole'])
print('--- the five antibiotics only ---')
print(sub[five]['susceptibility'].astype(str).str.strip().str.lower().value_counts(dropna=False))
