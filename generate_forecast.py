"""
Generate Yearly Forecast - Store-Category Constrained (2026)
─────────────────────────────────────────────────────────────
• Each store forecasts ONLY its allowed product categories
• Festival boosts are regionally targeted (Onam → South only, etc.)
• Outputs yearly_forecast_indian.csv consumed by the backend
"""

import pandas as pd
import numpy as np
from datetime import datetime

np.random.seed(42)

stores = pd.read_csv('outputs/indian_stores.csv')
cats   = pd.read_csv('outputs/product_categories.csv')

cat_lookup = dict(zip(cats['Category_Name'], cats['Avg_Items_Per_Store']))

# 2026 Festival calendar with regional targeting
FESTIVALS = {
    '2026-01-14': {'name': 'Pongal',          'boost': 2.2, 'regions': ['South India']},
    '2026-01-26': {'name': 'Republic Day',     'boost': 1.3, 'regions': 'All'},
    '2026-03-06': {'name': 'Holi',             'boost': 1.8, 'regions': ['North India', 'West India']},
    '2026-03-30': {'name': 'Eid-ul-Fitr',      'boost': 1.9, 'regions': 'All'},
    '2026-04-14': {'name': 'Baisakhi',         'boost': 1.6, 'regions': ['North India']},
    '2026-05-01': {'name': 'Labour Day',       'boost': 1.2, 'regions': 'All'},
    '2026-08-15': {'name': 'Independence Day', 'boost': 1.4, 'regions': 'All'},
    '2026-08-25': {'name': 'Onam',             'boost': 2.5, 'regions': ['South India']},
    '2026-10-02': {'name': 'Gandhi Jayanti',   'boost': 1.2, 'regions': 'All'},
    '2026-10-12': {'name': 'Durga Puja',       'boost': 2.3, 'regions': ['East India']},
    '2026-10-24': {'name': 'Diwali',           'boost': {'default': 2.8, 'South India': 2.4}, 'regions': 'All'},
    '2026-11-05': {'name': 'Diwali Sales',     'boost': 1.6, 'regions': 'All'},
    '2026-12-25': {'name': 'Christmas',        'boost': 1.5, 'regions': 'All'},
    '2026-12-31': {'name': "New Year's Eve",   'boost': 1.4, 'regions': 'All'},
}

dates = pd.date_range('2026-01-01', '2026-12-31')
data  = []

for _, s in stores.iterrows():
    allowed_cats = s['Categories'].split('|')
    region       = s['Region']

    for cat_name in allowed_cats:
        base = cat_lookup.get(cat_name, 100)

        for d in dates:
            ds        = d.strftime('%Y-%m-%d')
            val       = base * np.random.uniform(0.88, 1.12)
            boost     = 1.0
            fest_name = None
            fsi       = 0

            fest_info = FESTIVALS.get(ds)
            if fest_info:
                fest_regions = fest_info['regions']
                if fest_regions == 'All' or region in fest_regions:
                    fest_name = fest_info['name']
                    boost_info = fest_info['boost']
                    if isinstance(boost_info, dict):
                        boost = boost_info.get(region, boost_info.get('default', 1.0))
                    else:
                        boost = boost_info
                    fsi       = round((boost - 1.0) * 100, 1)

            adj = round(val * boost, 2)

            data.append({
                'Store_ID':         s['Store_ID'],
                'Store':            s['Store_ID'],        # alias for backend
                'Store_Name':       s['Store_Name'],
                'StoreName':        s['Store_Name'],       # alias for backend
                'Chain':            s['Chain'],
                'State':            s['State'],
                'Region':           region,
                'Category':         cat_name,
                'Product_Category': cat_name,             # alias for backend
                'Date':             ds,
                'Month':            d.month,
                'Year':             d.year,
                'Festival':         fest_name,
                'Festival_Name':    fest_name,
                'FSI':              fsi,
                'Baseline':         round(val, 2),
                'Baseline_Forecast':round(val, 2),        # alias for backend
                'Adjusted':         adj,
                'ForecastValue':    adj,                  # alias for backend
            })

df = pd.DataFrame(data)
df.to_csv('outputs/yearly_forecast_indian.csv', index=False)

print(f"✅ Saved {len(df):,} forecast records")
print(f"   Stores           : {df['Store_ID'].nunique()}")
print(f"   Categories unique: {df['Category'].nunique()}")
print(f"   Date range       : {df['Date'].min()} → {df['Date'].max()}")
festival_rows = df[df['Festival_Name'].notna()]
print(f"   Festival-boosted : {len(festival_rows):,} rows")
print(f"\n📊 Records per region:")
print(df.groupby('Region').size().to_string())