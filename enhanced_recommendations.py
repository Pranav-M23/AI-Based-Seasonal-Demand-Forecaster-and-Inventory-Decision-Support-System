"""
Step 1.4: Generate Enhanced Action Recommendations
- Discount recommendations by month/category
- Stock management tips (overstock/understock warnings)
- Category-specific insights
- Seasonal recommendations
"""

import pandas as pd
import numpy as np

print("="*70)
print("STEP 1.4: GENERATING ENHANCED RECOMMENDATIONS")
print("="*70)

# Load data
forecast_df = pd.read_csv('outputs/yearly_forecast_indian.csv')
inventory_df = pd.read_csv('outputs/inventory_decisions_indian.csv')

print(f"✅ Loaded forecast: {len(forecast_df):,} records")
print(f"✅ Loaded inventory: {len(inventory_df):,} records")

# 1. DISCOUNT RECOMMENDATIONS BY MONTH/CATEGORY
print("\n🔄 Generating discount recommendations...")

discount_data = []

for (store_id, cat, month), group in forecast_df.groupby(['Store_ID', 'Category', 'Month']):
    avg_fsi = group['FSI'].mean()
    has_festival = group['Festival'].notna().any()
    
    # Discount logic:
    # - High FSI (festival period): Lower discount (2-3%)
    # - Low FSI (off-season): Higher discount (8-12%)
    # - Mid FSI: Medium discount (5-7%)
    
    if avg_fsi > 50:
        discount = np.random.uniform(2, 3)
        reason = f"Festival season ({group['Festival'].mode()[0] if has_festival else 'Peak demand'})"
    elif avg_fsi > 20:
        discount = np.random.uniform(5, 7)
        reason = "Moderate demand period"
    else:
        discount = np.random.uniform(8, 12)
        reason = "Off-season clearance"
    
    store_info = forecast_df[forecast_df['Store_ID'] == store_id].iloc[0]
    
    discount_data.append({
        'Store_ID': store_id,
        'Store_Name': store_info['Store_Name'],
        'State': store_info['State'],
        'Region': store_info['Region'],
        'Category': cat,
        'Month': month,
        'Year': 2026,
        'Recommended_Discount_%': round(discount, 1),
        'Reason': reason,
        'Avg_FSI': round(avg_fsi, 1)
    })

discount_df = pd.DataFrame(discount_data)
discount_df.to_csv('outputs/discount_recommendations_enhanced.csv', index=False)
print(f"✅ Generated {len(discount_df):,} discount recommendations")

# 2. STOCK MANAGEMENT RECOMMENDATIONS
print("\n🔄 Generating stock management recommendations...")

action_data = []

for _, inv in inventory_df.iterrows():
    actions = []
    
    # Critical stock situations
    if inv['Decision'] == 'REORDER NOW':
        actions.append({
            'priority': 'CRITICAL',
            'type': 'Reorder',
            'message': f"Order {int(inv['Reorder_Point'] - inv['Current_Stock'])} units immediately - only {inv['Days_Supply']:.0f} days of stock left"
        })
    
    elif inv['Decision'] == 'REORDER SOON':
        actions.append({
            'priority': 'HIGH',
            'type': 'Reorder',
            'message': f"Plan order for {int(inv['Reorder_Point'] * 1.2 - inv['Current_Stock'])} units within next week"
        })
    
    # Overstock warning
    if inv['Days_Supply'] > 45:
        actions.append({
            'priority': 'MEDIUM',
            'type': 'Overstock',
            'message': f"High inventory ({inv['Days_Supply']:.0f} days). Consider discount promotion to clear excess stock"
        })
    
    # Category-specific recommendations
    category_tips = {
        'Groceries & Staples': "Fast-moving category - maintain 15-20 days buffer stock",
        'Fresh Produce': "Perishable items - order frequently in smaller batches (5-7 days max)",
        'Dairy & Eggs': "Short shelf-life - daily restocking recommended",
        'Snacks & Beverages': "High demand on weekends - increase stock Thu-Fri",
        'Personal Care': "Steady demand - maintain 30-day inventory",
        'Home Care': "Seasonal peaks during festivals - increase stock 2 weeks before",
        'Clothing & Apparel': "Seasonal category - clearance sales for off-season inventory",
        'Electronics & Appliances': "Festival-driven sales - stock up 1 month before Diwali/Onam",
        'Kitchen & Dining': "Wedding season demand (Nov-Feb) - increase stock 20%",
        'Health & Wellness': "Growing category - monitor trends and adjust weekly"
    }
    
    if inv['Category'] in category_tips:
        actions.append({
            'priority': 'INFO',
            'type': 'Category Insight',
            'message': category_tips[inv['Category']]
        })
    
    # Get relevant discount
    month = pd.Timestamp.now().month
    discount_rec = discount_df[
        (discount_df['Store_ID'] == inv['Store_ID']) & 
        (discount_df['Category'] == inv['Category']) & 
        (discount_df['Month'] == month)
    ]
    
    if not discount_rec.empty:
        disc = discount_rec.iloc[0]
        actions.append({
            'priority': 'MEDIUM',
            'type': 'Discount',
            'message': f"Apply {disc['Recommended_Discount_%']:.0f}% discount this month - {disc['Reason']}"
        })
    
    # Seasonal recommendation
    month = pd.Timestamp.now().month
    if month in [10, 11]:  # Festival season
        actions.append({
            'priority': 'HIGH',
            'type': 'Seasonal',
            'message': "Festival season peak - ensure adequate stock and staff"
        })
    elif month in [7, 8]:  # Monsoon
        actions.append({
            'priority': 'INFO',
            'type': 'Seasonal',
            'message': "Monsoon season - slight dip in footfall expected"
        })
    
    # Save all actions for this item
    for action in actions:
        action_data.append({
            'Store_ID': inv['Store_ID'],
            'Store_Name': inv['Store_Name'],
            'State': inv['State'],
            'Region': inv['Region'],
            'Category': inv['Category'],
            'Priority': action['priority'],
            'Action_Type': action['type'],
            'Recommendation': action['message'],
            'Current_Stock': inv['Current_Stock'],
            'Days_Supply': inv['Days_Supply'],
            'Decision': inv['Decision']
        })

action_df = pd.DataFrame(action_data)
action_df.to_csv('outputs/action_recommendations_enhanced.csv', index=False)
print(f"✅ Generated {len(action_df):,} action recommendations")

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

print(f"\n📊 Discount Recommendations:")
print(f"   Total: {len(discount_df):,}")
print(f"   Avg discount: {discount_df['Recommended_Discount_%'].mean():.1f}%")
print(f"   By range:")
print(f"      0-5%: {len(discount_df[discount_df['Recommended_Discount_%'] <= 5])} (Festival season)")
print(f"      5-10%: {len(discount_df[(discount_df['Recommended_Discount_%'] > 5) & (discount_df['Recommended_Discount_%'] <= 10)])} (Normal)")
print(f"      10%+: {len(discount_df[discount_df['Recommended_Discount_%'] > 10])} (Clearance)")

print(f"\n💡 Action Recommendations:")
print(f"   Total: {len(action_df):,}")
print(f"   By priority:")
print(action_df['Priority'].value_counts())
print(f"\n   By type:")
print(action_df['Action_Type'].value_counts())

print("\n" + "="*70)
print("STEP 15 Enhancements in csv files:")
print("="*70)
print("\n✅ Created files:")
print("   - outputs/discount_recommendations_enhanced.csv")
print("   - outputs/action_recommendations_enhanced.csv")
print("\n🔄 Next: Run Steps 2.1-2.3 to update backend")