"""
Generate Inventory Decisions - Store-Category Constrained
──────────────────────────────────────────────────────────
Each store only carries the categories it is configured for.
Per-category SKU count: 20–30 items (realistic, not 1000+).
"""

import pandas as pd
import numpy as np

np.random.seed(42)

stores = pd.read_csv('outputs/indian_stores.csv')
cats   = pd.read_csv('outputs/product_categories.csv')

# category → average daily sales units
cat_lookup = dict(zip(cats['Category_Name'], cats['Avg_Items_Per_Store']))

# Number of SKUs to represent per category slot
ITEMS_MIN, ITEMS_MAX = 20, 30

data = []

for _, s in stores.iterrows():
    allowed_cats = s['Categories'].split('|')

    for cat_name in allowed_cats:
        avg_daily  = cat_lookup.get(cat_name, 100)
        num_skus   = np.random.randint(ITEMS_MIN, ITEMS_MAX + 1)
        reorder    = avg_daily * 7
        stock      = np.random.uniform(0, reorder * 1.5)

        if stock < reorder * 0.5:
            decision = 'REORDER NOW'
        elif stock < reorder:
            decision = 'REORDER SOON'
        else:
            decision = 'OK'

        priority_score = round(max(0.0, min(100.0,
                            (1.0 - stock / (reorder * 1.5)) * 100)), 1)

        data.append({
            'Store_ID':       s['Store_ID'],
            'Store_Name':     s['Store_Name'],
            'Chain':          s['Chain'],
            'Store_Type':     s['Store_Type'],
            'Scope':          s['Scope'],
            'State':          s['State'],
            'Region':         s['Region'],
            'Category':       cat_name,
            'Num_SKUs':        num_skus,
            'Current_Stock':   round(stock, 2),
            'Reorder_Point':   round(reorder, 2),
            'Decision':        decision,
            'Days_Of_Supply':  round(stock / avg_daily, 1) if avg_daily > 0 else 999,
            'Priority_Score':  priority_score,
            'Stockout_Risk':   round(max(0.0, 1.0 - stock / (reorder * 1.5)) * 100, 1),
        })

df = pd.DataFrame(data)
df.to_csv('outputs/inventory_decisions_indian.csv', index=False)

print(f"✅ Saved {len(df):,} inventory records")
print(f"   Stores with data       : {df['Store_ID'].nunique()}")
print(f"   Avg categories/store   : {df.groupby('Store_ID').size().mean():.1f}")
print(f"   Total SKUs (all stores): {df['Num_SKUs'].sum():,}")
print(f"\n📊 Decision breakdown:")
print(df['Decision'].value_counts().to_string())
print(f"\n📊 Records per region:")
print(df.groupby('Region').size().to_string())