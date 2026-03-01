"""
Generate Region-Week Discount Recommendations
Creates proper discount file for the API from forecast data
"""

import pandas as pd
import numpy as np

print("=" * 70)
print("GENERATING DISCOUNT RECOMMENDATIONS FROM SCRATCH")
print("=" * 70)

# Load forecast
forecast_file = "outputs/yearly_festival_adjusted_region.csv"
print(f"\nLoading: {forecast_file}")

df = pd.read_csv(forecast_file)
print(f"✅ Loaded: {len(df):,} rows")
print(f"Columns: {list(df.columns)}")

# Ensure Date column
df['Date'] = pd.to_datetime(df['Date'])

# Calculate discount logic based on demand patterns
print(f"\n🔄 Calculating discount recommendations...")

# Logic: Discount when baseline demand is low or to clear inventory
# Higher discount when adjusted < baseline (post-festival slump)
# Lower discount when adjusted > baseline (festival period - no discount needed)

df['Uplift_Pct'] = ((df['Adjusted_Forecast'] - df['Baseline_Forecast']) / df['Baseline_Forecast'] * 100).fillna(0)

# Discount rules:
# 1. If uplift < -5%: Apply 15% discount (significant slump)
# 2. If uplift -5% to 0%: Apply 10% discount (minor slump)
# 3. If uplift 0% to 5%: Apply 5% discount (optional, competitive)
# 4. If uplift > 5%: No discount (high demand period)

def assign_discount(uplift):
    if uplift < -5:
        return 15.0
    elif uplift < 0:
        return 10.0
    elif uplift <= 5:
        return 5.0
    else:
        return 0.0

df['Discount_Pct'] = df['Uplift_Pct'].apply(assign_discount)

# Add discount signal for reference
def assign_signal(discount):
    if discount >= 15:
        return 'APPLY_DISCOUNT_LARGE'
    elif discount >= 10:
        return 'APPLY_DISCOUNT_MEDIUM'
    elif discount >= 5:
        return 'APPLY_DISCOUNT_SMALL'
    else:
        return 'NO_DISCOUNT'

df['Discount_Signal'] = df['Discount_Pct'].apply(assign_signal)

print(f"\n📊 Uplift Distribution:")
print(df['Uplift_Pct'].describe())

print(f"\n📊 Discount Signal Distribution:")
print(df['Discount_Signal'].value_counts())

print(f"\n📊 Discount Percentage Distribution:")
print(df['Discount_Pct'].value_counts())

# Create Week column (Monday of each week)
df['Week'] = df['Date'] - pd.to_timedelta(df['Date'].dt.weekday, unit='D')
df['Week'] = df['Week'].dt.normalize()

# Aggregate to Region-Week level
print(f"\n🔄 Aggregating to Region-Week level...")

region_week = df.groupby(['Region', 'Week'], as_index=False).agg({
    'Discount_Pct': 'mean',  # Average discount for the week
    'Uplift_Pct': 'mean',     # Average uplift
    'Discount_Signal': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'NO_DISCOUNT'
}).round(2)

region_week = region_week.rename(columns={
    'Discount_Pct': 'RecommendedDiscount'
})

# Sort by Region and Week
region_week = region_week.sort_values(['Region', 'Week']).reset_index(drop=True)

print(f"✅ Aggregated to {len(region_week):,} rows")

# Show sample
print(f"\n📋 Sample recommendations (first 20 rows):")
print(region_week.head(20).to_string())

# Show sample for Kerala specifically
print(f"\n📋 Kerala recommendations (first 10 weeks):")
kerala = region_week[region_week['Region'] == 'Kerala'].head(10)
print(kerala.to_string())

# Check stats
print(f"\n📊 Discount Statistics:")
print(region_week['RecommendedDiscount'].describe())

zero_count = (region_week['RecommendedDiscount'] == 0).sum()
small_count = ((region_week['RecommendedDiscount'] > 0) & (region_week['RecommendedDiscount'] <= 5)).sum()
medium_count = ((region_week['RecommendedDiscount'] > 5) & (region_week['RecommendedDiscount'] <= 10)).sum()
large_count = (region_week['RecommendedDiscount'] > 10).sum()

print(f"\nDiscount breakdown:")
print(f"   0% (NO_DISCOUNT): {zero_count} weeks ({zero_count/len(region_week)*100:.1f}%)")
print(f"   1-5% (SMALL): {small_count} weeks ({small_count/len(region_week)*100:.1f}%)")
print(f"   6-10% (MEDIUM): {medium_count} weeks ({medium_count/len(region_week)*100:.1f}%)")
print(f"   >10% (LARGE): {large_count} weeks ({large_count/len(region_week)*100:.1f}%)")

# By region
print(f"\n📊 Discount by Region:")
for region in sorted(region_week['Region'].unique()):
    region_data = region_week[region_week['Region'] == region]
    avg_disc = region_data['RecommendedDiscount'].mean()
    non_zero = (region_data['RecommendedDiscount'] > 0).sum()
    print(f"   {region:15s}: {len(region_data):3d} weeks, avg={avg_disc:5.2f}%, non-zero={non_zero:3d}")

# Save main output (just Region, Week, RecommendedDiscount for API)
output_file = "outputs/region_discount_recommendations.csv"
region_week[['Region', 'Week', 'RecommendedDiscount']].to_csv(output_file, index=False)
print(f"\n✅ Saved API file to: {output_file}")

# Save detailed version with signals for analysis
detailed_file = "outputs/region_discount_detailed.csv"
region_week.to_csv(detailed_file, index=False)
print(f"✅ Saved detailed file to: {detailed_file}")

# Verify
verify = pd.read_csv(output_file)
print(f"\n🔍 Verification:")
print(f"   Rows: {len(verify):,}")
print(f"   Columns: {list(verify.columns)}")
print(f"   Non-zero discounts: {(verify['RecommendedDiscount'] > 0).sum()}")
print(f"   Date range: {verify['Week'].min()} to {verify['Week'].max()}")

print("\n" + "=" * 70)
print("COMPLETE!")
