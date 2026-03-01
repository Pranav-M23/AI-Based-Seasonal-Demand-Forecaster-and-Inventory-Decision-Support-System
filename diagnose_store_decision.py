"""
Diagnose why /inventory/store-decisions returns empty rows
"""

import pandas as pd
import os
import sys
import traceback

try:
    print("=" * 70)
    print("STORE DECISIONS DIAGNOSTIC")
    print("=" * 70)

    # Check if file exists
    decisions_file = "outputs/inventory_decisions_store_category.csv"
    print(f"\nLooking for: {decisions_file}")
    
    if not os.path.exists(decisions_file):
        print(f"❌ File not found: {decisions_file}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Files in outputs/:")
        if os.path.exists("outputs"):
            for f in os.listdir("outputs"):
                if "decision" in f.lower():
                    print(f"   - {f}")
        sys.exit(1)

    # Load file
    print(f"\n✅ File found, loading...")
    df = pd.read_csv(decisions_file)
    print(f"✅ File loaded: {len(df)} rows")
    print(f"\nColumns: {list(df.columns)}")

    # Check Store 1 specifically
    print("\n" + "=" * 70)
    print("CHECKING STORE 1")
    print("=" * 70)

    # Check Store column type first
    print(f"\nStore column type: {df['Store'].dtype}")
    print(f"Sample Store values: {df['Store'].head(10).tolist()}")

    # Try to filter for Store 1
    store_1 = df[df["Store"] == 1]
    print(f"\nRows for Store 1: {len(store_1)}")

    if len(store_1) == 0:
        print("❌ No data for Store 1!")
        print("\n📊 Stores that DO have data:")
        store_counts = df["Store"].value_counts().head(20)
        print(store_counts)
        print(f"\nTotal unique stores: {df['Store'].nunique()}")
    else:
        print("\n✅ Store 1 data found:")
        print(store_1.to_string())

    # Check for NaN in Store column
    nan_count = df['Store'].isna().sum()
    if nan_count > 0:
        print(f"\n⚠️  WARNING: {nan_count} rows have NaN in Store column!")

    # Check Decision/Action column
    print("\n" + "=" * 70)
    print("DECISION COLUMN CHECK")
    print("=" * 70)
    
    decision_col = None
    for col in ['Decision', 'Action']:
        if col in df.columns:
            decision_col = col
            break

    if decision_col:
        print(f"✅ Decision column found: '{decision_col}'")
        print(f"\nDecision value counts:")
        print(df[decision_col].value_counts())
    else:
        print("❌ No Decision/Action column found!")
        print(f"Available columns: {list(df.columns)}")

    # Check Category column
    print("\n" + "=" * 70)
    print("CATEGORY COLUMN CHECK")
    print("=" * 70)
    
    category_col = None
    for col in ['Category', 'Product_Category']:
        if col in df.columns:
            category_col = col
            break

    if category_col:
        print(f"✅ Category column found: '{category_col}'")
        print(f"\nCategory value counts:")
        print(df[category_col].value_counts())
    else:
        print("❌ No Category column found!")

    # Check Region column
    if 'Region' in df.columns:
        print(f"\n✅ Region column found")
        print(f"Unique regions: {df['Region'].unique()}")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total rows: {len(df)}")
    print(f"Unique stores: {df['Store'].nunique()}")
    print(f"Has Store 1: {'Yes' if len(store_1) > 0 else 'No'}")
    
except Exception as e:
    print("\n" + "=" * 70)
    print("❌ ERROR OCCURRED")
    print("=" * 70)
    print(f"Error: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()