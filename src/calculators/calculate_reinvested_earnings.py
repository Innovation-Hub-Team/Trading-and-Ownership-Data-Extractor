import json
import pandas as pd
import re

# Load retained earnings data
with open('data/results/retained_earnings_results.json', 'r', encoding='utf-8') as f:
    retained_data = json.load(f)

# Extract year from pdf_filename for all entries
for r in retained_data:
    match = re.search(r'(\d{4})[^\d]*(\d{4})', r['pdf_filename'])
    if match:
        r['year'] = int(match.group(2))  # Use the second 4-digit number as year
    else:
        r['year'] = None

# Add error column for failed extractions
for r in retained_data:
    if not r.get('success'):
        r['error'] = r.get('error', 'Extraction failed')
    else:
        r['error'] = ''

retained_df = pd.DataFrame(retained_data)

# Load foreign ownership data
ownership_df = pd.read_csv('data/ownership/foreign_ownership_data.csv')

def clean_pct(val):
    if pd.isnull(val):
        return None
    return float(str(val).replace('%','').replace(',','').strip())

ownership_df['foreign_ownership_pct'] = ownership_df['foreign_ownership'].apply(clean_pct)

# Ensure both keys are strings for merging
retained_df['company_symbol'] = retained_df['company_symbol'].astype(str)
ownership_df['symbol'] = ownership_df['symbol'].astype(str)

# Merge on company_symbol <-> symbol
merged = pd.merge(
    retained_df,
    ownership_df,
    left_on='company_symbol',
    right_on='symbol',
    how='left'
)

# Calculate reinvested earnings only for successful extractions
merged['retained_earnings'] = merged.apply(
    lambda row: row['numeric_value'] if row.get('success') and pd.notnull(row.get('numeric_value')) else '', axis=1
)
merged['reinvested_earnings'] = merged.apply(
    lambda row: row['numeric_value'] * (row['foreign_ownership_pct'] / 100) if row.get('success') and pd.notnull(row.get('numeric_value')) and pd.notnull(row.get('foreign_ownership_pct')) else '', axis=1
)

# Select and rename columns for output
output_cols = [
    'company_symbol',
    'year',
    'retained_earnings',
    'foreign_ownership_pct',
    'reinvested_earnings',
    'pdf_filename',
    'company_name',
    'error'
]

output = merged[output_cols]

# Save to CSV
output.to_csv('frontend/public/reinvested_earnings_results.csv', index=False, encoding='utf-8')

# Also save to backend data/results directory for API serving
import os
os.makedirs('data/results', exist_ok=True)
output.to_csv('data/results/reinvested_earnings_results.csv', index=False, encoding='utf-8')

print('Done! Results saved to frontend/public/reinvested_earnings_results.csv')
print('Results also saved to data/results/reinvested_earnings_results.csv for API serving') 