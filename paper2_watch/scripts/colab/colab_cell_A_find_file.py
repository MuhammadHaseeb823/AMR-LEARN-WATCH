# CELL A: connect Drive and look for the ARMD file
from google.colab import drive
drive.mount('/content/drive')
import glob
found = []
for p in ['/content/**/microbiology_cultures_cohort*.csv', '/content/drive/MyDrive/**/microbiology_cultures_cohort*.csv', '/content/drive/MyDrive/**/*cohort*.csv']:
    found += glob.glob(p, recursive=True)
found = sorted(set(found))
print('FILES FOUND:' if found else 'NO FILE FOUND - see the guide, option 2 or 3')
for f in found: print('  ', f)
