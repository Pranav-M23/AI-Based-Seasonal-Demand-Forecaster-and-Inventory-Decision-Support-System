import pandas as pd
import numpy as np

stores = pd.read_csv('outputs/indian_stores.csv')
cats = pd.read_csv('outputs/product_categories.csv')

data = []
for _, s in stores.iterrows():
    for _, c in cats.iterrows():
        demand = c['Avg_Items_Per_Store']
        reorder = demand * 7
        stock = np.random.uniform(0, reorder * 1.5)
        
        if stock < reorder * 0.5:
            decision = 'REORDER NOW'
        elif stock < reorder:
            decision = 'REORDER SOON'
        else:
            decision = 'OK'
        
        data.append({
            'Store_ID': s['Store_ID'],
            'Store_Name': s['Store_Name'],
            'State': s['State'],
            'Region': s['Region'],
            'Category': c['Category_Name'],
            'Current_Stock': round(stock, 2),
            'Reorder_Point': round(reorder, 2),
            'Decision': decision,
            'Days_Supply': round(stock / demand, 1) if demand > 0 else 999
        })

df = pd.DataFrame(data)
df.to_csv('outputs/inventory_decisions_indian.csv', index=False)
print(f"✅ Saved {len(df):,} inventory records")