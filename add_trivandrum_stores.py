"""
Add 4 Thiruvananthapuram stores to forecast and inventory CSVs
"""
import pandas as pd
import numpy as np
import os

FORECAST_FILE = 'outputs/yearly_forecast_indian.csv'
INVENTORY_FILE = 'outputs/inventory_decisions_indian.csv'

np.random.seed(42)

# ----------- Store definitions -----------
NEW_STORES = [
    {
        'Store_ID': 55,
        'Store_Name': 'Lulu Mall Hypermarket - Thiruvananthapuram',
        'Chain': 'Lulu Hypermarket',
        'Store_Type': 'Hypermarket',
        'Scope': 'Regional',
        'State': 'Kerala',
        'Region': 'South India',
        'Categories': ['Dairy & Eggs', 'Fresh Produce', 'Groceries & Staples',
                       'Snacks & Beverages', 'Personal Care', 'Home Care'],
    },
    {
        'Store_ID': 56,
        'Store_Name': 'Pothys - Thiruvananthapuram',
        'Chain': 'Pothys',
        'Store_Type': 'Specialty',
        'Scope': 'Regional',
        'State': 'Kerala',
        'Region': 'South India',
        'Categories': ['Clothing & Apparel', 'Dairy & Eggs', 'Fresh Produce',
                       'Groceries & Staples', 'Snacks & Beverages',
                       'Personal Care', 'Home Care', 'Electronics & Appliances'],
    },
    {
        'Store_ID': 57,
        'Store_Name': 'Reliance Smart - Thiruvananthapuram',
        'Chain': 'Reliance Smart',
        'Store_Type': 'Hypermarket',
        'Scope': 'National',
        'State': 'Kerala',
        'Region': 'South India',
        'Categories': ['Dairy & Eggs', 'Fresh Produce', 'Groceries & Staples',
                       'Snacks & Beverages', 'Personal Care', 'Home Care'],
    },
    {
        'Store_ID': 58,
        'Store_Name': 'Ramachandran - Thiruvananthapuram',
        'Chain': 'Ramachandran',
        'Store_Type': 'Specialty',
        'Scope': 'Regional',
        'State': 'Kerala',
        'Region': 'South India',
        'Categories': ['Clothing & Apparel', 'Dairy & Eggs', 'Fresh Produce',
                       'Groceries & Staples', 'Snacks & Beverages',
                       'Personal Care', 'Home Care', 'Electronics & Appliances'],
    },
]

# Base daily forecast ranges per category (mean, std) - realistic for mid-size Kerala stores
CATEGORY_PARAMS = {
    'Groceries & Staples':   (380, 80),
    'Fresh Produce':         (160, 45),
    'Dairy & Eggs':          (95,  30),
    'Snacks & Beverages':    (240, 60),
    'Personal Care':         (175, 50),
    'Home Care':             (130, 40),
    'Clothing & Apparel':    (200, 70),
    'Electronics & Appliances': (110, 35),
}

# Clothing gets higher weight for Ramachandran, Pothys
PRIORITY_MULTIPLIERS = {
    58: {'Clothing & Apparel': 1.6},   # Ramachandran
    56: {'Clothing & Apparel': 1.3},   # Pothys
}

# Festival calendar (date -> name, FSI boost)
FESTIVALS = {
    '2026-01-14': ('Pongal / Makar Sankranti', 1.35),
    '2026-03-25': ('Holi', 1.20),
    '2026-04-14': ('Vishu / Tamil New Year', 1.40),
    '2026-08-15': ('Onam (start)', 1.50),
    '2026-08-22': ('Onam (peak)', 1.85),
    '2026-10-02': ('Navaratri', 1.45),
    '2026-10-20': ('Diwali', 1.70),
    '2026-12-25': ('Christmas', 1.30),
}

def generate_forecast_rows(store):
    rows = []
    dates = pd.date_range('2026-01-01', '2026-12-31', freq='D')
    store_id = store['Store_ID']

    for cat in store['Categories']:
        mu, sigma = CATEGORY_PARAMS[cat]
        # Apply priority multiplier if any
        mult = PRIORITY_MULTIPLIERS.get(store_id, {}).get(cat, 1.0)
        mu = mu * mult

        for dt in dates:
            ds = dt.strftime('%Y-%m-%d')
            festival_name = None
            fsi = 0.0

            # Check festival
            if ds in FESTIVALS:
                festival_name, fsi_mult = FESTIVALS[ds]
                fsi = round((fsi_mult - 1) * 100, 1)
                base = max(0, np.random.normal(mu * fsi_mult, sigma * 0.8))
            else:
                # Weekend boost
                weekend_mult = 1.15 if dt.dayofweek >= 5 else 1.0
                base = max(0, np.random.normal(mu * weekend_mult, sigma))

            baseline = round(base, 2)
            adjusted = round(base * (1 + fsi / 200), 2)  # FSI adjustment

            rows.append({
                'Store_ID': store_id,
                'Store': store_id,
                'Store_Name': store['Store_Name'],
                'StoreName': store['Store_Name'],
                'Chain': store['Chain'],
                'State': store['State'],
                'Region': store['Region'],
                'Category': cat,
                'Product_Category': cat,
                'Date': ds,
                'Month': dt.month,
                'Year': dt.year,
                'Festival': festival_name if festival_name else None,
                'Festival_Name': festival_name if festival_name else None,
                'FSI': fsi,
                'Baseline': baseline,
                'Baseline_Forecast': baseline,
                'Adjusted': adjusted,
                'ForecastValue': adjusted,
            })
    return rows


# Inventory decision rules
def inventory_decision(cat, store_id):
    np.random.seed(store_id * 7 + hash(cat) % 100)
    base_stock = {
        'Groceries & Staples': (800, 2200),
        'Fresh Produce': (300, 900),
        'Dairy & Eggs': (150, 500),
        'Snacks & Beverages': (400, 1200),
        'Personal Care': (250, 800),
        'Home Care': (200, 700),
        'Clothing & Apparel': (350, 1000),
        'Electronics & Appliances': (80, 300),
    }
    lo, hi = base_stock.get(cat, (200, 800))
    current = round(np.random.uniform(lo, hi), 2)
    reorder_point = round(lo * 1.2, 0)
    days_supply = round(np.random.uniform(1.0, 12.0), 1)
    priority = round(np.random.uniform(10, 90), 1)
    stockout = round(np.random.uniform(5, 85), 1)

    if days_supply <= 2:
        decision = 'REORDER NOW'
    elif days_supply <= 5:
        decision = 'REORDER SOON'
    else:
        decision = 'OK'

    return {
        'Current_Stock': current,
        'Reorder_Point': reorder_point,
        'Decision': decision,
        'Days_Of_Supply': days_supply,
        'Priority_Score': priority,
        'Stockout_Risk': stockout,
        'Num_SKUs': int(np.random.randint(10, 30)),
    }


# ----------- Load existing CSVs -----------
fc = pd.read_csv(FORECAST_FILE)
inv = pd.read_csv(INVENTORY_FILE)

print(f"Existing forecast rows: {len(fc)}, existing inventory rows: {len(inv)}")

# Remove these stores if they already exist (re-run safe)
fc = fc[~fc['Store_ID'].isin([55, 56, 57, 58])]
inv = inv[~inv['Store_ID'].isin([55, 56, 57, 58])]

# ----------- Generate new forecast rows -----------
new_fc_rows = []
for s in NEW_STORES:
    new_fc_rows.extend(generate_forecast_rows(s))

new_fc = pd.DataFrame(new_fc_rows)
fc_combined = pd.concat([fc, new_fc], ignore_index=True)
fc_combined.to_csv(FORECAST_FILE, index=False)
print(f"Forecast: added {len(new_fc)} rows → total {len(fc_combined)}")

# ----------- Generate new inventory rows -----------
new_inv_rows = []
for s in NEW_STORES:
    for cat in s['Categories']:
        inv_data = inventory_decision(cat, s['Store_ID'])
        new_inv_rows.append({
            'Store_ID': s['Store_ID'],
            'Store_Name': s['Store_Name'],
            'Chain': s['Chain'],
            'Store_Type': s['Store_Type'],
            'Scope': s['Scope'],
            'State': s['State'],
            'Region': s['Region'],
            'Category': cat,
            **inv_data,
        })

new_inv = pd.DataFrame(new_inv_rows)
inv_combined = pd.concat([inv, new_inv], ignore_index=True)
inv_combined.to_csv(INVENTORY_FILE, index=False)
print(f"Inventory: added {len(new_inv)} rows → total {len(inv_combined)}")
print("\nDone! New stores:")
for s in NEW_STORES:
    print(f"  Store {s['Store_ID']}: {s['Store_Name']} ({len(s['Categories'])} categories)")
