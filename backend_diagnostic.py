"""
BACKEND DIAGNOSTIC SCRIPT
Run this to see what's wrong with your endpoints
"""

import os
import pandas as pd

# Check paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(ROOT_DIR, "outputs")

print("=" * 70)
print("BACKEND DIAGNOSTIC REPORT")
print("=" * 70)

print(f"\nProject Root: {ROOT_DIR}")
print(f"Outputs Directory: {OUTPUTS_DIR}")
print(f"Outputs Directory Exists: {os.path.exists(OUTPUTS_DIR)}")

# Check all required files
files_to_check = {
    "Forecast": "yearly_festival_adjusted_region.csv",
    "Discount": "region_discount_recommendations.csv",
    "KPI Region Summary": "inventory_kpi_region_summary.csv",
    "KPI Region Category": "inventory_kpi_region_category_summary.csv",
    "KPI Store Level": "inventory_kpi_store_level.csv",
    "KPI Store Category": "inventory_kpi_store_category.csv",
    "Decisions": "inventory_decisions_store_category.csv",
    "Exec Summary": "inventory_decision_executive_summary.csv",
}

print("\n--- FILE CHECK ---")
for name, filename in files_to_check.items():
    filepath = os.path.join(OUTPUTS_DIR, filename)
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    
    if exists:
        try:
            df = pd.read_csv(filepath)
            print(f"{status} {name:25s}: {len(df):6,} rows | {filepath}")
        except Exception as e:
            print(f"⚠️  {name:25s}: EXISTS but can't read | {str(e)[:50]}")
    else:
        print(f"{status} {name:25s}: NOT FOUND | {filepath}")

# Check decisions file specifically
decisions_path = os.path.join(OUTPUTS_DIR, "inventory_decisions_store_category.csv")
if os.path.exists(decisions_path):
    print("\n--- DECISIONS FILE ANALYSIS ---")
    df = pd.read_csv(decisions_path)
    print(f"Columns: {list(df.columns)}")
    print(f"Rows: {len(df)}")
    
    # Check for Action/Decision column
    action_col = None
    for col in df.columns:
        if 'action' in col.lower() or 'decision' in col.lower():
            action_col = col
            break
    
    if action_col:
        print(f"\nAction column: '{action_col}'")
        print(f"Action counts:")
        print(df[action_col].value_counts())
    else:
        print("\n⚠️  No Action/Decision column found!")
        print(f"Available columns: {list(df.columns)}")

print("\n" + "=" * 70)
print("NEXT STEPS:")
print("=" * 70)

if not os.path.exists(OUTPUTS_DIR):
    print("❌ outputs/ directory doesn't exist!")
    print("   Run your forecasting scripts (Steps 13.1-13.4) first")
elif not os.path.exists(decisions_path):
    print("❌ Decision file missing!")
    print("   Run: python inventory_decision_engine.py")
else:
    print("✅ Files exist - issue is in the backend code")
    print("   Check your main.py endpoint logic")