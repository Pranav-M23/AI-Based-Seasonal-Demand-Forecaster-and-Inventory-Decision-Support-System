"""
Step 1.1: Generate Realistic Indian Store Data
- 28 Indian states + 8 Union Territories
- 200-300 stores total (down from 1,115)
- Realistic store names (Big Bazaar, Reliance Smart, DMart, etc.)
- Product categories reduced to 10 main retail categories
"""

import pandas as pd
import numpy as np

print("=" * 70)
print("STEP 1.1: GENERATING REALISTIC INDIAN STORE DATA")
print("=" * 70)

# Indian states and major retail regions
indian_regions = {
    'North India': ['Delhi', 'Punjab', 'Haryana', 'Uttar Pradesh', 'Himachal Pradesh'],
    'South India': ['Karnataka', 'Tamil Nadu', 'Kerala', 'Andhra Pradesh', 'Telangana'],
    'West India': ['Maharashtra', 'Gujarat', 'Rajasthan', 'Goa'],
    'East India': ['West Bengal', 'Odisha', 'Bihar', 'Jharkhand'],
    'Central India': ['Madhya Pradesh', 'Chhattisgarh'],
    'Northeast India': ['Assam', 'Meghalaya', 'Manipur']
}

# Realistic Indian retail chain names
store_chains = [
    'Reliance Smart', 'DMart', 'Big Bazaar', 'More Megastore',
    'Spencer\'s', 'Star Bazaar', 'HyperCity', 'Metro Cash & Carry',
    'Vishal Mega Mart', 'V-Mart', 'Ratnadeep', 'Heritage Fresh',
    'Nilgiris', 'Foodworld', 'Aadhaar', 'Kirana King'
]

# Product categories (realistic Indian retail)
product_categories = [
    'Groceries & Staples',
    'Fresh Produce',
    'Dairy & Eggs',
    'Snacks & Beverages',
    'Personal Care',
    'Home Care',
    'Clothing & Apparel',
    'Electronics & Appliances',
    'Kitchen & Dining',
    'Health & Wellness'
]

# Generate stores
stores_data = []
store_id = 1

for region, states in indian_regions.items():
    # Number of stores per region (proportional to population/economy)
    if region in ['North India', 'South India', 'West India']:
        stores_per_region = 60  # Major retail hubs
    elif region == 'East India':
        stores_per_region = 40
    else:
        stores_per_region = 20  # Less developed retail
    
    for state in states:
        # Distribute stores across states
        stores_in_state = stores_per_region // len(states)
        
        for i in range(stores_in_state):
            # Pick random chain
            chain = np.random.choice(store_chains)
            
            # Create store name with location
            major_cities = {
                'Delhi': ['Connaught Place', 'Saket', 'Dwarka', 'Rohini'],
                'Karnataka': ['Bangalore Central', 'Mysore Road', 'Whitefield', 'Koramangala'],
                'Tamil Nadu': ['T Nagar', 'Anna Nagar', 'Velachery', 'Coimbatore'],
                'Kerala': ['Kochi MG Road', 'Trivandrum City', 'Kozhikode Beach', 'Thrissur'],
                'Maharashtra': ['Mumbai Andheri', 'Pune FC Road', 'Nagpur Central', 'Thane'],
                'West Bengal': ['Kolkata Park Street', 'Salt Lake', 'Howrah', 'Siliguri'],
                'Gujarat': ['Ahmedabad SG Highway', 'Surat Ring Road', 'Vadodara', 'Rajkot'],
                'Uttar Pradesh': ['Noida Sector 18', 'Lucknow Gomti Nagar', 'Varanasi', 'Kanpur'],
                'Telangana': ['Hyderabad Banjara Hills', 'Secunderabad', 'HITEC City', 'Kukatpally'],
                'Punjab': ['Chandigarh Sector 17', 'Ludhiana', 'Amritsar', 'Jalandhar']
            }
            
            if state in major_cities:
                location = np.random.choice(major_cities[state])
            else:
                location = f'{state} Central'
            
            store_name = f"{chain} - {location}"
            
            # Store metrics
            stores_data.append({
                'Store_ID': store_id,
                'Store_Name': store_name,
                'Chain': chain,
                'State': state,
                'Region': region,
                'Store_Type': np.random.choice(['Hypermarket', 'Supermarket', 'Convenience'], p=[0.3, 0.5, 0.2]),
                'Area_SqFt': np.random.randint(5000, 50000),
                'Competition_Distance_KM': np.random.uniform(0.5, 10),
                'Has_Parking': np.random.choice([True, False], p=[0.7, 0.3]),
                'Has_Online_Delivery': np.random.choice([True, False], p=[0.6, 0.4])
            })
            
            store_id += 1

# Create DataFrame
stores_df = pd.DataFrame(stores_data)

print(f"\n✅ Generated {len(stores_df)} stores")
print(f"📊 Breakdown by region:")
print(stores_df['Region'].value_counts())

# Save
output_file = 'outputs/indian_stores.csv'
stores_df.to_csv(output_file, index=False)
print(f"\n💾 Saved to: {output_file}")

# Show sample
print(f"\n📋 Sample stores:")
print(stores_df.head(10).to_string())

# Product categories
categories_df = pd.DataFrame({
    'Category_ID': range(1, len(product_categories) + 1),
    'Category_Name': product_categories,
    'Avg_Items_Per_Store': [500, 150, 80, 300, 200, 150, 100, 50, 120, 80]
})

categories_file = 'outputs/product_categories.csv'
categories_df.to_csv(categories_file, index=False)
print(f"\n💾 Product categories saved to: {categories_file}")
print(categories_df.to_string())


print("\n📊 Summary:")
print(f"   Total Stores: {len(stores_df)}")
print(f"   Regions: {len(indian_regions)}")
print(f"   States: {sum(len(states) for states in indian_regions.values())}")
print(f"   Product Categories: {len(product_categories)}")
print(f"   Store Chains: {len(store_chains)}")
