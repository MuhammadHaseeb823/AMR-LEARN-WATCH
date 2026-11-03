# CELL E: full data-flow counts for Table 2 (run after cell A; uses the same file; takes a few minutes)
import pandas as pd
raw = pd.read_csv(found[0], low_memory=False)
print('Source rows:', len(raw), '| patients:', raw['anon_id'].nunique())
d = raw[['anon_id', 'order_proc_id_coded', 'organism', 'antibiotic', 'susceptibility']].copy()
d.columns = ['patient', 'culture', 'organism', 'abx', 'res']
d['res'] = d['res'].astype(str).str.strip().str.lower()
print('\nResult categories in the whole source file:'); print(d['res'].value_counts(dropna=False))
nul = d['res'].isin(['null', 'nan', 'none', ''])
print('\nStep 1 - rows with Null/blank result removed:', int(nul.sum()))
d = d[~nul]
g = d.groupby(['culture', 'organism', 'abx'])['res'].transform('nunique')
print('Step 2 - rows in conflicting culture-organism-antibiotic groups removed:', int((g > 1).sum()))
d = d[g == 1]
before = len(d)
d = d.drop_duplicates(['culture', 'organism', 'abx', 'res'])
print('Step 3 - exact duplicate rows removed:', before - len(d))
print('\nRemaining rows by category (these are what Step 4 sorts):'); print(d['res'].value_counts())
other = ~d['res'].isin(['resistant', 'susceptible'])
print('\nStep 4 - rows that are not resistant/susceptible, removed:', int(other.sum()))
print(d[other]['res'].value_counts())
d = d[~other]
print('\nResistant or susceptible rows left:', len(d), '| resistant share: %.2f%%' % (100 * (d['res'] == 'resistant').mean()))
print('(The paper has 1,541,238 and 16.78%.)')
