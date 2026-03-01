"""
Diagnose why all discounts are 0 - FIXED VERSION
"""

import pandas as pd
import os
import sys
import traceback

try:
    print("=" * 70)
    print("DISCOUNT DIAGNOSTIC - FIXED")
    print("=" * 70)

    # Check for the CORRECT discount file
    discount_file = "outputs/region_discount_recommendations.csv"
    print(f"\nLooking for: {discount_file}")
    
    if not os.path.exists(discount_file):
        print(f"❌ Discount file not found!")
        print(f"Current directory: {os.getcwd()}")
        print(f"\nFiles in outputs/ that contain 'discount':")
        if os.path.exists("outputs"):
            for f in os.listdir("outputs"):
                if "discount" in f.lower():
                    print(f"   - {f}")
        sys.exit(1)

    # Load file
    print(f"✅ File found, loading...")
    df = pd.read_csv(discount_file)
    print(f"✅ File loaded: {len(df)} rows")
    print(f"\nColumns: {list(df.columns)}")

    # Verify this is the DISCOUNT file (should have Region, Week, RecommendedDiscount)
    expected_cols = ['Region', 'Week', 'RecommendedDiscount']
    has_expected = all(col in df.columns for col in expected_cols)
    
    if not has_expected:
        print(f"\n⚠️  WARNING: This doesn't look like the discount file!")
        print(f"Expected columns: {expected_cols}")
        print(f"Actual columns: {list(df.columns)}")
        print("\nThis might be the forecast file instead!")
    else:
        print(f"✅ Correct file structure confirmed")

    # Find discount column
    disc_col = None
    for col in df.columns:
        if 'discount' in col.lower() and 'recommended' in col.lower():
            disc_col = col
            break
    
    if not disc_col:
        # Try any column with 'discount'
        for col in df.columns:
            if 'discount' in col.lower():
                disc_col = col
                break

    if not disc_col:
        print("\n❌ No discount column found!")
        print(f"Available columns: {list(df.columns)}")
        sys.exit(1)

    print(f"\n✅ Using discount column: '{disc_col}'")

    # Check discount values
    print(f"\n" + "=" * 70)
    print("DISCOUNT VALUE ANALYSIS")
    print("=" * 70)
    
    print(f"\nDiscount statistics:")
    print(df[disc_col].describe())

    print(f"\nUnique discount values:")
    unique_vals = df[disc_col].value_counts().head(20)
    print(unique_vals)

    # Count zeros
    zero_count = (df[disc_col] == 0).sum()
    non_zero_count = (df[disc_col] != 0).sum()

    print(f"\nZero discounts: {zero_count} ({zero_count/len(df)*100:.1f}%)")
    print(f"Non-zero discounts: {non_zero_count} ({non_zero_count/len(df)*100:.1f}%)")

    if zero_count == len(df):
        print("\n🔴 PROBLEM: ALL DISCOUNTS ARE ZERO!")
    elif zero_count > len(df) * 0.9:
        print(f"\n⚠️  WARNING: {zero_count/len(df)*100:.1f}% of discounts are zero")

    # Sample rows
    print(f"\n" + "=" * 70)
    print("SAMPLE ROWS")
    print("=" * 70)
    print(df.head(10))

    # Check by region
    if 'Region' in df.columns:
        print(f"\n" + "=" * 70)
        print("DISCOUNT BY REGION")
        print("=" * 70)
        for region in sorted(df['Region'].unique()):
            region_data = df[df['Region'] == region][disc_col]
            mean_disc = region_data.mean()
            non_zero = (region_data != 0).sum()
            print(f"  {region:15s}: {len(region_data):3d} rows, {non_zero:3d} non-zero, avg={mean_disc:.2f}%")

    # Check date range if Week column exists
    if 'Week' in df.columns:
        print(f"\n" + "=" * 70)
        print("DATE RANGE")
        print("=" * 70)
        df['Week'] = pd.to_datetime(df['Week'])
        print(f"From: {df['Week'].min().date()}")
        print(f"To:   {df['Week'].max().date()}")
        print(f"Span: {(df['Week'].max() - df['Week'].min()).days} days")

    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    
    if zero_count == len(df):
        print("🔴 ALL DISCOUNTS ARE ZERO")
        print("   The discount generation logic didn't flag any periods for discounts.")
        print("   This is because your forecast only has positive uplifts (festivals).")
        print("   Recommendation: Regenerate with adjusted logic.")
    else:
        print(f"✅ Discounts generated successfully")
        print(f"   {non_zero_count} periods have non-zero discounts")

except Exception as e:
    print("\n" + "=" * 70)
    print("❌ ERROR OCCURRED")
    print("=" * 70)
    print(f"Error: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()