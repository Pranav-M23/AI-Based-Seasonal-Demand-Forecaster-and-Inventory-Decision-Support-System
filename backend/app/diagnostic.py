"""
BACKEND ENDPOINT DIAGNOSTIC - Project Root Version
Run from: S:\Pnav College\S6\MiniProject\Seasonal Demand Forecaster
"""

import sys
import os
import pandas as pd

# Add backend to Python path
BACKEND_PATH = os.path.join(os.getcwd(), "backend")
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

print("=" * 70)
print("BACKEND ENDPOINT DIAGNOSTIC")
print("=" * 70)
print(f"Running from: {os.getcwd()}")
print(f"Backend path: {BACKEND_PATH}")

# Import store
print("\n[1] Importing data_loader...")
try:
    from app.data_loader import store
    print("✅ Import successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("\nPossible fixes:")
    print("1. Run from project root: cd 'S:\\Pnav College\\S6\\MiniProject\\Seasonal Demand Forecaster'")
    print("2. Or run from backend: cd backend && python diagnose_endpoints.py")
    sys.exit(1)

# Try to load data
print("\n[2] Loading data...")
try:
    store.load()
    print("✅ Data loaded successfully")
except Exception as e:
    print(f"❌ Error loading data: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check forecast
print("\n[3] Checking forecast data...")
if store.forecast is None:
    print("❌ Forecast is None!")
elif store.forecast.empty:
    print("❌ Forecast is empty!")
else:
    print(f"✅ Forecast loaded: {len(store.forecast):,} rows")
    print(f"   Columns: {list(store.forecast.columns)}")
    print(f"   Date range: {store.forecast['Date'].min()} to {store.forecast['Date'].max()}")
    print(f"   Sample row:\n{store.forecast.head(1).to_dict('records')[0]}")

# Check discount
print("\n[4] Checking discount data...")
if store.discount is None:
    print("❌ Discount is None!")
elif store.discount.empty:
    print("⚠️  Discount is empty (file might not exist)")
else:
    print(f"✅ Discount loaded: {len(store.discount):,} rows")
    print(f"   Columns: {list(store.discount.columns)}")
    if len(store.discount) > 0:
        print(f"   Sample row:\n{store.discount.head(1).to_dict('records')[0]}")

# Check decisions
print("\n[5] Checking decisions data...")
if store.decisions_store_category is None:
    print("❌ Decisions is None!")
elif store.decisions_store_category.empty:
    print("⚠️  Decisions is empty")
else:
    print(f"✅ Decisions loaded: {len(store.decisions_store_category):,} rows")
    print(f"   Columns: {list(store.decisions_store_category.columns)}")
    if len(store.decisions_store_category) > 0:
        print(f"   Sample row:\n{store.decisions_store_category.head(1).to_dict('records')[0]}")

# Check KPI
print("\n[6] Checking KPI region summary...")
kpi_file = "outputs/inventory_kpi_region_summary.csv"
print(f"   Looking for: {kpi_file}")
print(f"   File exists: {os.path.exists(kpi_file)}")

if store.kpi_region_summary is None:
    print("❌ KPI region summary is None!")
elif store.kpi_region_summary.empty:
    print("⚠️  KPI region summary is empty")
else:
    print(f"✅ KPI loaded: {len(store.kpi_region_summary):,} rows")
    print(f"   Columns: {list(store.kpi_region_summary.columns)}")
    print(f"\n   Full data:")
    print(store.kpi_region_summary.to_string())

# Test @property methods
print("\n[7] Testing @property methods...")
try:
    regions = store.regions
    print(f"✅ store.regions ({len(regions)} regions): {regions}")
except Exception as e:
    print(f"❌ store.regions failed: {e}")

try:
    stores_list = store.stores
    print(f"✅ store.stores ({len(stores_list)} stores): {stores_list[:10]}..." if len(stores_list) > 10 else f"✅ store.stores: {stores_list}")
except Exception as e:
    print(f"❌ store.stores failed: {e}")

try:
    categories = store.categories
    print(f"✅ store.categories ({len(categories)} categories): {categories}")
except Exception as e:
    print(f"❌ store.categories failed: {e}")

# Simulate /meta endpoint
print("\n[8] Simulating /meta endpoint...")
try:
    fc = store.forecast
    min_date = None
    max_date = None
    
    if fc is not None and not fc.empty:
        min_date = pd.to_datetime(fc["Date"]).min().date()
        max_date = pd.to_datetime(fc["Date"]).max().date()
    
    meta_result = {
        "forecast_rows": 0 if fc is None else len(fc),
        "discount_rows": 0 if store.discount is None else len(store.discount),
        "min_date": str(min_date),
        "max_date": str(max_date),
        "regions": store.regions,
        "stores_count": len(store.stores),
        "categories": store.categories,
    }
    
    print("✅ /meta would return:")
    for key, value in meta_result.items():
        print(f"   {key}: {value}")
    
except Exception as e:
    print(f"❌ /meta simulation failed: {e}")
    import traceback
    traceback.print_exc()

# Simulate /kpi/region-summary endpoint
print("\n[9] Simulating /kpi/region-summary endpoint...")
try:
    df = store.kpi_region_summary
    
    if df is None:
        print("❌ Would return 404: KPI data is None")
    elif df.empty:
        print("❌ Would return 404: KPI data is empty")
    else:
        print(f"✅ Processing {len(df)} rows...")
        
        # Check if required columns exist
        required_cols = ["Region", "Stores", "Avg_Stockout_Risk", "Max_Stockout_Risk", "Avg_Reorder_Point", "Total_Safety_Stock"]
        missing = [col for col in required_cols if col not in df.columns]
        
        if missing:
            print(f"❌ Missing columns: {missing}")
            print(f"   Available columns: {list(df.columns)}")
        else:
            rows = []
            for idx, r in df.iterrows():
                row_data = {
                    "region": str(r.get("Region", "")),
                    "stores": int(r.get("Stores", 0)),
                    "avg_stockout_risk": float(r.get("Avg_Stockout_Risk", 0.0)),
                    "max_stockout_risk": float(r.get("Max_Stockout_Risk", 0.0)),
                    "avg_reorder_point": float(r.get("Avg_Reorder_Point", 0.0)),
                    "total_safety_stock": float(r.get("Total_Safety_Stock", 0.0)),
                }
                rows.append(row_data)
                print(f"   Row {idx+1}: {row_data['region']} - {row_data['stores']} stores")
            
            print(f"\n✅ Would return {len(rows)} regions")
        
except Exception as e:
    print(f"❌ /kpi/region-summary simulation failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)

print("\n📝 SUMMARY:")
print(f"   Forecast: {'✅' if store.forecast is not None and not store.forecast.empty else '❌'}")
print(f"   Discount: {'✅' if store.discount is not None and not store.discount.empty else '⚠️'}")
print(f"   Decisions: {'✅' if store.decisions_store_category is not None and not store.decisions_store_category.empty else '❌'}")
print(f"   KPI: {'✅' if store.kpi_region_summary is not None and not store.kpi_region_summary.empty else '❌'}")

if store.kpi_region_summary is None or store.kpi_region_summary.empty:
    print("\n⚠️  ACTION REQUIRED:")
    print("   KPI file is missing or empty!")
    print("   Run: python inventory_kpi.py")