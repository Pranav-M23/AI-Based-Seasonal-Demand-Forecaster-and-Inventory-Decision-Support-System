"""
Step 1.1: Regionalized Indian Retail Store Ecosystem
─────────────────────────────────────────────────────
4 Regions: North India, South India, West India, East India

National Chains (60 % per region):
  Reliance Smart, DMart, Star Bazaar, Decathlon,
  Zudio, Max Fashion, Reliance Digital, Croma

Regional Specialists (40 % per region):
  South: Lulu Hypermarket, Pothys, Saravana Stores,
         Nilgiris, Vasanth & Co, Sangeetha Mobiles
  North: Vishal Mega Mart, V-Mart, 24SEVEN,
         Fabindia, Liberty Shoes, Modern Bazaar
  West:  Vijay Sales, Sahakari Bhandar, Nature's Basket,
         Bombay Dyeing, Jade Blue, Tirumala Sweets
  East:  Spencer's Retail, Style Baazar, Bazaar Kolkata, Khadims

Category Constraints:
  Specialty stores carry ONLY their relevant categories
  (e.g. Decathlon → sports/activewear only, Croma → electronics only)
"""

import pandas as pd
import numpy as np

np.random.seed(42)

# ===========================================================
# STORE CHAIN CONFIGURATION
# ===========================================================
STORE_CHAIN_CONFIG = {
    # ── NATIONAL CHAINS (appear in every region) ──────────
    "Reliance Smart": {
        "scope": "National", "type": "Hypermarket",
        "categories": ["Groceries & Staples", "Fresh Produce", "Dairy & Eggs",
                       "Snacks & Beverages", "Home Care", "Personal Care"],
    },
    "DMart": {
        "scope": "National", "type": "Hypermarket",
        "categories": ["Groceries & Staples", "Snacks & Beverages",
                       "Home Care", "Personal Care", "Kitchen & Dining"],
    },
    "Star Bazaar": {
        "scope": "National", "type": "Hypermarket",
        "categories": ["Groceries & Staples", "Fresh Produce", "Dairy & Eggs",
                       "Snacks & Beverages", "Home Care", "Kitchen & Dining"],
    },
    "Decathlon": {
        "scope": "National", "type": "Sports Store",
        "categories": ["Clothing & Apparel", "Health & Wellness"],
    },
    "Zudio": {
        "scope": "National", "type": "Fashion Retail",
        "categories": ["Clothing & Apparel"],
    },
    "Max Fashion": {
        "scope": "National", "type": "Fashion Retail",
        "categories": ["Clothing & Apparel"],
    },
    "Reliance Digital": {
        "scope": "National", "type": "Electronics",
        "categories": ["Electronics & Appliances"],
    },
    "Croma": {
        "scope": "National", "type": "Electronics",
        "categories": ["Electronics & Appliances"],
    },

    # ── SOUTH INDIA REGIONALS ──────────────────────────────
    "Lulu Hypermarket": {
        "scope": "South", "type": "Hypermarket",
        "categories": ["Groceries & Staples", "Fresh Produce", "Dairy & Eggs",
                       "Snacks & Beverages", "Personal Care"],
    },
    "Pothys": {
        "scope": "South", "type": "Traditional Textile",
        "categories": ["Clothing & Apparel"],
    },
    "Saravana Stores": {
        "scope": "South", "type": "General Retail",
        "categories": ["Kitchen & Dining", "Personal Care"],
    },
    "Nilgiris": {
        "scope": "South", "type": "Specialty Grocery",
        "categories": ["Dairy & Eggs", "Snacks & Beverages", "Fresh Produce"],
    },
    "Vasanth & Co": {
        "scope": "South", "type": "Home Appliances",
        "categories": ["Electronics & Appliances", "Kitchen & Dining"],
    },
    "Sangeetha Mobiles": {
        "scope": "South", "type": "Electronics",
        "categories": ["Electronics & Appliances"],
    },

    # ── NORTH INDIA REGIONALS ─────────────────────────────
    "Vishal Mega Mart": {
        "scope": "North", "type": "Discount Retail",
        "categories": ["Clothing & Apparel", "Groceries & Staples"],
    },
    "V-Mart": {
        "scope": "North", "type": "Fashion Retail",
        "categories": ["Clothing & Apparel"],
    },
    "24SEVEN": {
        "scope": "North", "type": "Convenience Store",
        "categories": ["Snacks & Beverages", "Dairy & Eggs"],
    },
    "Fabindia": {
        "scope": "North", "type": "Premium Handloom",
        "categories": ["Clothing & Apparel", "Health & Wellness"],
    },
    "Liberty Shoes": {
        "scope": "North", "type": "Footwear",
        "categories": ["Clothing & Apparel"],
    },
    "Modern Bazaar": {
        "scope": "North", "type": "Premium Grocery",
        "categories": ["Fresh Produce", "Snacks & Beverages", "Dairy & Eggs"],
    },

    # ── WEST INDIA REGIONALS ──────────────────────────────
    "Vijay Sales": {
        "scope": "West", "type": "Electronics",
        "categories": ["Electronics & Appliances", "Kitchen & Dining"],
    },
    "Sahakari Bhandar": {
        "scope": "West", "type": "Cooperative Grocery",
        "categories": ["Groceries & Staples", "Fresh Produce"],
    },
    "Nature's Basket": {
        "scope": "West", "type": "Premium Grocery",
        "categories": ["Fresh Produce", "Dairy & Eggs", "Snacks & Beverages"],
    },
    "Bombay Dyeing": {
        "scope": "West", "type": "Home Textiles",
        "categories": ["Home Care", "Kitchen & Dining"],
    },
    "Jade Blue": {
        "scope": "West", "type": "Men's Fashion",
        "categories": ["Clothing & Apparel"],
    },
    "Tirumala Sweets": {
        "scope": "West", "type": "Specialty Food",
        "categories": ["Snacks & Beverages"],
    },

    # ── EAST INDIA REGIONALS ──────────────────────────────
    "Spencer's Retail": {
        "scope": "East", "type": "Hypermarket",
        "categories": ["Fresh Produce", "Groceries & Staples",
                       "Dairy & Eggs", "Snacks & Beverages"],
    },
    "Style Baazar": {
        "scope": "East", "type": "Fashion Retail",
        "categories": ["Clothing & Apparel"],
    },
    "Bazaar Kolkata": {
        "scope": "East", "type": "Discount Retail",
        "categories": ["Clothing & Apparel"],
    },
    "Khadims": {
        "scope": "East", "type": "Footwear",
        "categories": ["Clothing & Apparel"],
    },
}

# ===========================================================
# SPECIFIC CITY LOCATION PER CHAIN PER REGION
# ===========================================================
REGION_LOCATIONS = {
    "North India": {
        "Reliance Smart":   "Connaught Place, New Delhi",
        "DMart":            "Sector 18, Noida",
        "Star Bazaar":      "Gomti Nagar, Lucknow",
        "Decathlon":        "Sector 17, Chandigarh",
        "Zudio":            "Saket, New Delhi",
        "Max Fashion":      "Ludhiana, Punjab",
        "Reliance Digital": "Lajpat Nagar, New Delhi",
        "Croma":            "Cyber Hub, Gurgaon",
        "Vishal Mega Mart": "Karol Bagh, New Delhi",
        "V-Mart":           "Gomti Nagar, Lucknow",
        "24SEVEN":          "Hauz Khas, New Delhi",
        "Fabindia":         "Khan Market, New Delhi",
        "Liberty Shoes":    "Amritsar, Punjab",
        "Modern Bazaar":    "Greater Kailash, New Delhi",
    },
    "South India": {
        "Reliance Smart":   "Whitefield, Bengaluru",
        "DMart":            "Velachery, Chennai",
        "Star Bazaar":      "Banjara Hills, Hyderabad",
        "Decathlon":        "Koramangala, Bengaluru",
        "Zudio":            "T Nagar, Chennai",
        "Max Fashion":      "Thrissur, Kerala",
        "Reliance Digital": "HITEC City, Hyderabad",
        "Croma":            "Indiranagar, Bengaluru",
        "Lulu Hypermarket": "MG Road, Kochi",
        "Pothys":           "T Nagar, Chennai",
        "Saravana Stores":  "Anna Nagar, Chennai",
        "Nilgiris":         "Jubilee Hills, Hyderabad",
        "Vasanth & Co":     "Coimbatore, Tamil Nadu",
        "Sangeetha Mobiles":"Jayanagar, Bengaluru",
    },
    "West India": {
        "Reliance Smart":   "Andheri, Mumbai",
        "DMart":            "SG Highway, Ahmedabad",
        "Star Bazaar":      "FC Road, Pune",
        "Decathlon":        "Thane, Mumbai MMR",
        "Zudio":            "Surat Ring Road, Surat",
        "Max Fashion":      "Vadodara, Gujarat",
        "Reliance Digital": "Bandra, Mumbai",
        "Croma":            "Vashi, Navi Mumbai",
        "Vijay Sales":      "Dadar, Mumbai",
        "Sahakari Bhandar": "Prabhadevi, Mumbai",
        "Nature's Basket":  "Bandra, Mumbai",
        "Bombay Dyeing":    "Lower Parel, Mumbai",
        "Jade Blue":        "CG Road, Ahmedabad",
        "Tirumala Sweets":  "Chembur, Mumbai",
    },
    "East India": {
        "Reliance Smart":   "Park Street, Kolkata",
        "DMart":            "Salt Lake, Kolkata",
        "Star Bazaar":      "Janpath, Bhubaneswar",
        "Decathlon":        "New Town, Kolkata",
        "Zudio":            "Boring Road, Patna",
        "Max Fashion":      "GS Road, Guwahati",
        "Reliance Digital": "South City Mall, Kolkata",
        "Croma":            "Hill Cart Road, Siliguri",
        "Spencer's Retail": "Forum Mall, Kolkata",
        "Style Baazar":     "Fancy Bazar, Guwahati",
        "Bazaar Kolkata":   "Esplanade, Kolkata",
        "Khadims":          "Hatibagan, Kolkata",
    },
}

NATIONAL_CHAINS = [
    "Reliance Smart", "DMart", "Star Bazaar", "Decathlon",
    "Zudio", "Max Fashion", "Reliance Digital", "Croma",
]

REGIONAL_SPECIALISTS = {
    "North India": ["Vishal Mega Mart", "V-Mart", "24SEVEN",
                    "Fabindia", "Liberty Shoes", "Modern Bazaar"],
    "South India": ["Lulu Hypermarket", "Pothys", "Saravana Stores",
                    "Nilgiris", "Vasanth & Co", "Sangeetha Mobiles"],
    "West India":  ["Vijay Sales", "Sahakari Bhandar", "Nature's Basket",
                    "Bombay Dyeing", "Jade Blue", "Tirumala Sweets"],
    "East India":  ["Spencer's Retail", "Style Baazar",
                    "Bazaar Kolkata", "Khadims"],
}

REGION_STATE_MAP = {
    "North India": "Delhi / NCR",
    "South India": "Karnataka / Tamil Nadu",
    "West India":  "Maharashtra / Gujarat",
    "East India":  "West Bengal / Assam",
}

# ===========================================================
# BUILD STORE LIST
# ===========================================================
stores_data = []
store_id = 1

for region, specialists in REGIONAL_SPECIALISTS.items():
    chains_in_region = NATIONAL_CHAINS + specialists
    locations        = REGION_LOCATIONS[region]
    state            = REGION_STATE_MAP[region]

    for chain in chains_in_region:
        location = locations.get(chain, f"{region} Central")
        cfg      = STORE_CHAIN_CONFIG[chain]

        stores_data.append({
            "Store_ID":                store_id,
            "Store_Name":              f"{chain} - {location}",
            "Chain":                   chain,
            "Store_Type":              cfg["type"],
            "Scope":                   cfg["scope"],
            "State":                   state,
            "Region":                  region,
            "Categories":              "|".join(cfg["categories"]),
            "Num_Categories":          len(cfg["categories"]),
            "Area_SqFt":               np.random.randint(3000, 60000),
            "Competition_Distance_KM": round(np.random.uniform(0.5, 8.0), 1),
            "Has_Parking":             np.random.choice([True, False], p=[0.75, 0.25]),
            "Has_Online_Delivery":     np.random.choice([True, False], p=[0.65, 0.35]),
        })
        store_id += 1

stores_df = pd.DataFrame(stores_data)

print("=" * 70)
print("STEP 1.1: REGIONALIZED INDIAN RETAIL STORE ECOSYSTEM")
print("=" * 70)
print(f"\n✅ Generated {len(stores_df)} stores")
print(f"\n📊 Breakdown by region:")
print(stores_df['Region'].value_counts().to_string())
print(f"\n📊 Scope split (National vs Regional):")
print(stores_df['Scope'].value_counts().to_string())
print(f"\n📊 Store types:")
print(stores_df['Store_Type'].value_counts().to_string())
print(f"\n📋 Full store roster:")
print(stores_df[['Store_ID', 'Store_Name', 'Store_Type', 'Region',
                  'Num_Categories']].to_string(index=False))

stores_df.to_csv('outputs/indian_stores.csv', index=False)
print(f"\n💾 Saved to: outputs/indian_stores.csv")

# ===========================================================
# PRODUCT CATEGORIES MASTER
# ===========================================================
product_categories = [
    'Groceries & Staples', 'Fresh Produce', 'Dairy & Eggs',
    'Snacks & Beverages', 'Personal Care', 'Home Care',
    'Clothing & Apparel', 'Electronics & Appliances',
    'Kitchen & Dining', 'Health & Wellness',
]
# Average DAILY sales units per category (forecast baseline)
avg_daily_sales = [400, 150, 80, 250, 180, 120, 60, 30, 100, 70]

categories_df = pd.DataFrame({
    'Category_ID':         range(1, len(product_categories) + 1),
    'Category_Name':       product_categories,
    'Avg_Items_Per_Store': avg_daily_sales,
})
categories_df.to_csv('outputs/product_categories.csv', index=False)
print(f"\n💾 Product categories saved to: outputs/product_categories.csv")
print(categories_df.to_string(index=False))

print("\n📊 Summary:")
print(f"   Total Stores     : {len(stores_df)}")
print(f"   National Stores  : {(stores_df['Scope'] == 'National').sum()}")
print(f"   Regional Stores  : {(stores_df['Scope'] != 'National').sum()}")
print(f"   Regions          : 4 (North, South, West, East India)")
print(f"   Product Categories: {len(product_categories)}")
