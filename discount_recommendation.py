"""
Convert discount signals to proper region-week discount recommendations
Fixes the discount=0 issue in the API
"""

import pandas as pd
import numpy as np

print("=" * 70)
print("GENERATING PROPER DISCOUNT RECOMMENDATIONS")
print("=" * 70)

# Load the forecast file (which has Discount_Signal)
forecast_file = "outputs/yearly_festival_adjusted_region.csv"
print(f"\nLoading: {forecast_file}")

df = pd.read_csv(forecast_file)
print(f"✅ Loaded: {len(df):,} rows")

# Check columns
print(f"Columns: {list(df.columns)}")

# Ensure Date column
df['Date'] = pd.to_datetime(df['Date'])

# Ensure Discount_Pct exists
if 'Discount_Pct' not in df.columns:
    print("\n⚠️  Discount_Pct column missing, creating from Discount_Signal...")
    
    # Map signal to percentage
    discount_map = {
        'APPLY_DISCOUNT_SMALL': 10.0,
        'OPTIONAL_DISCOUNT': 5.0,
        'NO_DISCOUNT': 0.0
    }
    
    df['Discount_Pct'] = df['Discount_Signal'].map(discount_map).fillna(0.0)
    print("✅ Created Discount_Pct column")

# Create Week column (Monday of each week)
df['Week'] = df['Date'] - pd.to_timedelta(df['Date'].dt.weekday, unit='D')
df['Week'] = df['Week'].dt.normalize()

print(f"\n📊 Discount Signal Distribution:")
print(df['Discount_Signal'].value_counts())

print(f"\n📊 Discount Percentage Distribution:")
print(df['Discount_Pct'].value_counts())

# Aggregate to Region-Week level
print(f"\n🔄 Aggregating to Region-Week level...")

region_week = df.groupby(['Region', 'Week'], as_index=False).agg({
    'Discount_Pct': 'mean',  # Average discount for the week
    'Discount_Signal': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'NO_DISCOUNT'  # Most common signal
}).round(2)

region_week = region_week.rename(columns={
    'Discount_Pct': 'RecommendedDiscount'
})

print(f"✅ Aggregated to {len(region_week):,} rows")

# Show sample
print(f"\n📋 Sample recommendations:")
print(region_week.head(20))

# Check stats
print(f"\n📊 Discount Statistics:")
print(region_week['RecommendedDiscount'].describe())

zero_count = (region_week['RecommendedDiscount'] == 0).sum()
non_zero = (region_week['RecommendedDiscount'] > 0).sum()

print(f"\nZero discounts: {zero_count} ({zero_count/len(region_week)*100:.1f}%)")
print(f"Non-zero discounts: {non_zero} ({non_zero/len(region_week)*100:.1f}%)")

# Save
output_file = "outputs/region_discount_recommendations.csv"
region_week[['Region', 'Week', 'RecommendedDiscount']].to_csv(output_file, index=False)

print(f"\n✅ Saved to: {output_file}")

# Verify
verify = pd.read_csv(output_file)
print(f"\n🔍 Verification:")
print(f"   Rows: {len(verify):,}")
print(f"   Columns: {list(verify.columns)}")
print(f"   Non-zero discounts: {(verify['RecommendedDiscount'] > 0).sum()}")

print("\n" + "=" * 70)
print("COMPLETE!")
print("=" * 70)
