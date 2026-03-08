import pandas as pd
import numpy as np
from datetime import datetime

stores = pd.read_csv('outputs/indian_stores.csv')
cats = pd.read_csv('outputs/product_categories.csv')

festivals = {
    '2026-01-14': 'Pongal', '2026-03-06': 'Holi',
    '2026-08-25': 'Onam', '2026-10-24': 'Diwali'
}

dates = pd.date_range('2026-01-01', '2026-12-31')
data = []

for _, s in stores.iterrows():
    for _, c in cats.iterrows():
        base = c['Avg_Items_Per_Store']
        for d in dates:
            val = base * np.random.uniform(0.9, 1.1)
            fest = festivals.get(d.strftime('%Y-%m-%d'), None)
            adj = val * (2.0 if fest else 1.0)
            
            data.append({
                'Store_ID': s['Store_ID'],
                'Store_Name': s['Store_Name'],
                'State': s['State'],
                'Region': s['Region'],
                'Category': c['Category_Name'],
                'Date': d.strftime('%Y-%m-%d'),
                'Month': d.month,
                'Festival': fest,
                'FSI': 100 if fest else 0,
                'Baseline': round(val, 2),
                'Adjusted': round(adj, 2)
            })

df = pd.DataFrame(data)
df.to_csv('outputs/yearly_forecast_indian.csv', index=False)
print(f"✅ Saved {len(df):,} forecast records")