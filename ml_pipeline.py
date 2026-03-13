"""
ML Pipeline — Seasonal Demand Forecaster
==========================================
Orchestrates the full ML-powered pipeline:
  1. Train all models (RF + XGBoost)
  2. Generate ML-based demand forecasts for Indian stores
  3. Apply ML-predicted festival uplift
  4. Generate ML-based discount recommendations
  5. Generate ML-based inventory decisions + stockout risk
  6. Export all CSVs (compatible with existing backend)
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
import joblib
from datetime import datetime

warnings.filterwarnings("ignore", category=FutureWarning)

from ml_models import (
    train_all_models,
    predict_demand,
    DEMAND_FEATURES, DISCOUNT_TIERS, INVENTORY_ACTIONS,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
OUT_DIR = os.path.join(BASE_DIR, "outputs")
MODEL_DIR = os.path.join(BASE_DIR, "models")

os.makedirs(OUT_DIR, exist_ok=True)

PLANNING_YEAR = 2026

# ============================================================================
# HELPERS
# ============================================================================

def norm_region(x):
    if pd.isna(x):
        return "Pan-India"
    s = str(x).strip().replace("_", " ").replace("-", " ")
    s = " ".join(s.split())
    mapping = {
        "pan india": "Pan-India", "panindia": "Pan-India",
        "north india": "North-India", "north": "North-India",
        "west india": "West-India", "west": "West-India",
        "east india": "East-India", "east": "East-India",
        "tamilnadu": "Tamil Nadu", "tamil nadu": "Tamil Nadu",
        "kerala": "Kerala",
    }
    return mapping.get(s.lower(), s)


def load_regional_festival_calendar():
    calendar_path = os.path.join(DATA_DIR, "festival_calendar_regional.json")
    if not os.path.exists(calendar_path):
        raise FileNotFoundError(f"Regional festival file not found: {calendar_path}")
    with open(calendar_path, "r", encoding="utf-8") as fp:
        return json.load(fp)


def load_state_festival_calendar():
    calendar_path = os.path.join(DATA_DIR, "festival_calendar_state.json")
    if not os.path.exists(calendar_path):
        return {}
    with open(calendar_path, "r", encoding="utf-8") as fp:
        return json.load(fp)


def build_regional_festival_events(calendar_obj):
    rows = []
    for region_name, region_data in (calendar_obj or {}).items():
        for fest in region_data.get("festivals", []):
            start = pd.to_datetime(fest["date"])
            duration = max(1, int(fest.get("duration_days", 1)))
            end = start + pd.Timedelta(days=duration - 1)
            rows.append({
                "Region": region_name,
                "Festival": fest.get("name"),
                "StartDate": start,
                "EndDate": end,
                "Weight": float(max(0.0, float(fest.get("impact_multiplier", 1.0)) - 1.0)),
                "Type": fest.get("type", "local"),
            })
    return pd.DataFrame(rows)


def build_state_festival_events(state_calendar_obj, state_to_region_map):
    rows = []
    for state_name, festivals in (state_calendar_obj or {}).items():
        region_name = state_to_region_map.get(state_name)
        for fest in festivals:
            start = pd.to_datetime(fest["date"])
            duration = max(1, int(fest.get("duration_days", 1)))
            end = start + pd.Timedelta(days=duration - 1)
            rows.append({
                "Region": region_name,
                "State": state_name,
                "Festival": fest.get("name"),
                "StartDate": start,
                "EndDate": end,
                "Weight": float(max(0.0, float(fest.get("impact_multiplier", 1.0)) - 1.0)),
                "Type": "state-local",
            })
    return pd.DataFrame(rows)


# ============================================================================
# STEP 1: GENERATE INDIAN STORES (reuse existing logic)
# ============================================================================

def ensure_indian_stores():
    """Ensure indian_stores.csv and product_categories.csv exist."""
    stores_file = os.path.join(OUT_DIR, "indian_stores.csv")
    cats_file = os.path.join(OUT_DIR, "product_categories.csv")

    if os.path.exists(stores_file) and os.path.exists(cats_file):
        stores = pd.read_csv(stores_file)
        cats = pd.read_csv(cats_file)
        print(f"  Indian stores: {len(stores)} stores, {len(cats)} categories (cached)")
        return stores, cats

    # Generate fresh
    print("  Generating Indian store data...")
    np.random.seed(42)
    
    indian_regions = {
        'North India': ['Delhi', 'Punjab', 'Haryana', 'Uttar Pradesh', 'Himachal Pradesh'],
        'South India': ['Karnataka', 'Tamil Nadu', 'Kerala', 'Andhra Pradesh', 'Telangana'],
        'West India': ['Maharashtra', 'Gujarat', 'Rajasthan', 'Goa'],
        'East India': ['West Bengal', 'Odisha', 'Bihar', 'Jharkhand'],
        'Central India': ['Madhya Pradesh', 'Chhattisgarh'],
        'Northeast India': ['Assam', 'Meghalaya', 'Manipur']
    }

    store_chains = [
        'Reliance Smart', 'DMart', 'Big Bazaar', 'More Megastore',
        "Spencer's", 'Star Bazaar', 'HyperCity', 'Metro Cash & Carry',
        'Vishal Mega Mart', 'V-Mart', 'Ratnadeep', 'Heritage Fresh',
        'Nilgiris', 'Foodworld', 'Aadhaar', 'Kirana King'
    ]

    product_categories = [
        'Groceries & Staples', 'Fresh Produce', 'Dairy & Eggs',
        'Snacks & Beverages', 'Personal Care', 'Home Care',
        'Clothing & Apparel', 'Electronics & Appliances',
        'Kitchen & Dining', 'Health & Wellness'
    ]

    stores_data = []
    store_id = 1

    for region, states in indian_regions.items():
        if region in ['North India', 'South India', 'West India']:
            stores_per_region = 60
        elif region == 'East India':
            stores_per_region = 40
        else:
            stores_per_region = 20

        for state in states:
            stores_in_state = stores_per_region // len(states)
            for i in range(stores_in_state):
                chain = np.random.choice(store_chains)
                stores_data.append({
                    'Store_ID': store_id,
                    'Store_Name': f"{chain} - {state} #{i+1}",
                    'Chain': chain,
                    'State': state,
                    'Region': region,
                    'Store_Type': np.random.choice(['Hypermarket', 'Supermarket', 'Convenience'], p=[0.3, 0.5, 0.2]),
                    'Area_SqFt': np.random.randint(5000, 50000),
                    'Competition_Distance_KM': round(np.random.uniform(0.5, 10), 1),
                })
                store_id += 1

    stores = pd.DataFrame(stores_data)
    stores.to_csv(stores_file, index=False)

    cats_df = pd.DataFrame({
        'Category_ID': range(1, len(product_categories) + 1),
        'Category_Name': product_categories,
        'Avg_Items_Per_Store': [500, 150, 80, 300, 200, 150, 100, 50, 120, 80]
    })
    cats_df.to_csv(cats_file, index=False)

    print(f"  Generated {len(stores)} stores, {len(cats_df)} categories")
    return stores, cats_df


# ============================================================================
# STEP 2: ML-POWERED DEMAND FORECAST
# ============================================================================

def generate_ml_forecast(models, stores_df, cats_df):
    """
    Generate demand forecasts using RF+XGBoost ensemble.
    Maps Rossmann-trained models onto Indian stores.
    """
    print("\n" + "=" * 70)
    print("STEP 2: ML-POWERED DEMAND FORECASTING (RF + XGBoost Ensemble)")
    print("=" * 70)

    rf = models["demand_rf"]
    xgb = models["demand_xgb"]

    # Load store metadata for feature encoding
    store_csv = pd.read_csv(os.path.join(DATA_DIR, "store.csv"))
    store_region = pd.read_csv(os.path.join(DATA_DIR, "store_region.csv"))

    le_st = joblib.load(os.path.join(MODEL_DIR, "le_store_type.pkl"))
    le_as = joblib.load(os.path.join(MODEL_DIR, "le_assortment.pkl"))

    dates = pd.date_range(start=f"{PLANNING_YEAR}-01-01", end=f"{PLANNING_YEAR}-12-31", freq="D")
    regional_calendar = load_regional_festival_calendar()
    state_calendar = load_state_festival_calendar()
    state_to_region = stores_df.set_index("State")["Region"].to_dict()
    regional_events = build_regional_festival_events(regional_calendar)
    state_events = build_state_festival_events(state_calendar, state_to_region)
    festival_events = pd.concat([state_events, regional_events], ignore_index=True)

    # Map Indian stores to Rossmann store IDs for feature compatibility
    # Each Indian store maps to a Rossmann store proportionally
    n_rossmann = len(store_csv)
    indian_to_rossmann = {}
    for idx, s in stores_df.iterrows():
        rmid = (s["Store_ID"] % n_rossmann) + 1
        indian_to_rossmann[s["Store_ID"]] = rmid

    print(f"  Building forecast for {len(stores_df)} stores × {len(cats_df)} categories × {len(dates)} days...")

    all_frames = []

    for _, cat_row in cats_df.iterrows():
        cat_name = cat_row["Category_Name"]
        cat_base = cat_row["Avg_Items_Per_Store"]

        # Build prediction frame for all stores × all dates for this category
        frames = []
        for _, s in stores_df.iterrows():
            sid = s["Store_ID"]
            rmid = indian_to_rossmann[sid]
            rm_store = store_csv[store_csv["Store"] == rmid].iloc[0]

            store_frame = pd.DataFrame({"Date": dates})
            store_frame["Store"] = rmid
            store_frame["DayOfWeek"] = store_frame["Date"].dt.dayofweek + 1
            store_frame["Year"] = PLANNING_YEAR
            store_frame["Month"] = store_frame["Date"].dt.month
            store_frame["WeekOfYear"] = store_frame["Date"].dt.isocalendar()["week"].astype(int)
            store_frame["Promo"] = 0
            store_frame["SchoolHoliday"] = 0
            store_frame["CompetitionDistance"] = float(rm_store.get("CompetitionDistance", 0)) if pd.notna(rm_store.get("CompetitionDistance")) else 0
            store_frame["Promo2"] = int(rm_store.get("Promo2", 0)) if pd.notna(rm_store.get("Promo2")) else 0

            st_val = rm_store.get("StoreType", "a")
            as_val = rm_store.get("Assortment", "a")
            store_frame["StoreType_enc"] = le_st.transform([st_val if pd.notna(st_val) else "unknown"])[0]
            store_frame["Assortment_enc"] = le_as.transform([as_val if pd.notna(as_val) else "unknown"])[0]

            store_frame["_Store_ID"] = sid
            store_frame["_Store_Name"] = s["Store_Name"]
            store_frame["_State"] = s["State"]
            store_frame["_Region"] = s["Region"]
            store_frame["_Category"] = cat_name
            store_frame["_CatBase"] = cat_base

            frames.append(store_frame)

        big_frame = pd.concat(frames, ignore_index=True)
        big_frame = big_frame.fillna(0)

        # ML ensemble prediction
        raw_pred = predict_demand(rf, xgb, big_frame)

        # Scale to category-appropriate range
        # Rossmann sales are store-level (thousands); scale to item counts
        scale_factor = cat_base / max(raw_pred.mean(), 1)
        scaled_pred = raw_pred * scale_factor

        # Ensure positive + add slight variance
        rng = np.random.default_rng(hash(cat_name) % (2**31))
        noise = rng.normal(1.0, 0.03, size=len(scaled_pred))
        baseline = np.maximum(scaled_pred * noise, cat_base * 0.1)

        big_frame["Baseline"] = np.round(baseline, 2)

        # Festival tagging & ML-predicted uplift
        big_frame["Festival"] = None
        big_frame["Festival_Weight"] = 0.0

        for _, fest in festival_events.iterrows():
            fest_name = fest["Festival"]
            fest_region = fest.get("Region", "")
            fest_type = (fest.get("Type") or "local").lower()
            start = fest["StartDate"]
            end = fest["EndDate"]
            fest_name_l = str(fest_name).lower()
            is_diwali = "diwali" in fest_name_l

            # Temporal profile: pre-festival, core festival, post-festival
            pre_days = 7
            post_days = 2
            pre_factor = 0.35
            core_factor = 1.0
            post_factor = 0.45

            # Diwali should peak in the core window (not only lead-up)
            if is_diwali:
                pre_days = 5
                post_days = 3
                pre_factor = 0.45
                core_factor = 1.25
                post_factor = 0.60

            core_mask = (big_frame["Date"] >= start) & (big_frame["Date"] <= end)
            pre_mask = (big_frame["Date"] >= (start - pd.Timedelta(days=pre_days))) & (big_frame["Date"] < start)
            post_mask = (big_frame["Date"] > end) & (big_frame["Date"] <= (end + pd.Timedelta(days=post_days)))

            if fest_type == "pan-indian":
                region_mask = pd.Series(True, index=big_frame.index)
            elif fest_type == "state-local":
                region_mask = (big_frame["_State"].astype(str) == str(fest.get("State", "")))
            else:
                region_mask = (big_frame["_Region"].astype(str) == str(fest_region))

            base_weight = float(fest["Weight"])

            pre_weight = base_weight * pre_factor
            core_weight = base_weight * core_factor
            post_weight = base_weight * post_factor

            pre_apply_mask = pre_mask & region_mask
            core_apply_mask = core_mask & region_mask
            post_apply_mask = post_mask & region_mask

            if pre_apply_mask.any():
                big_frame.loc[pre_apply_mask, "Festival_Weight"] = np.maximum(
                    big_frame.loc[pre_apply_mask, "Festival_Weight"].values,
                    pre_weight
                )

            if core_apply_mask.any():
                core_updated_idx = []

                if is_diwali:
                    south_rows = big_frame["_Region"].astype(str) == "South India"
                    core_apply_south = core_apply_mask & south_rows
                    core_apply_non_south = core_apply_mask & (~south_rows)

                    if core_apply_non_south.any():
                        non_south_core_weight = max(core_weight, 1.65)
                        prev_non_south = big_frame.loc[core_apply_non_south, "Festival_Weight"].values
                        new_non_south = np.maximum(prev_non_south, non_south_core_weight)
                        write_non_south = new_non_south > prev_non_south
                        big_frame.loc[core_apply_non_south, "Festival_Weight"] = new_non_south
                        idx_non_south = big_frame.loc[core_apply_non_south].index
                        core_updated_idx.extend(idx_non_south[write_non_south].tolist())

                    if core_apply_south.any():
                        south_core_weight = max(core_weight, 1.15)
                        prev_south = big_frame.loc[core_apply_south, "Festival_Weight"].values
                        new_south = np.maximum(prev_south, south_core_weight)
                        write_south = new_south > prev_south
                        big_frame.loc[core_apply_south, "Festival_Weight"] = new_south
                        idx_south = big_frame.loc[core_apply_south].index
                        core_updated_idx.extend(idx_south[write_south].tolist())
                else:
                    prev_core_weights = big_frame.loc[core_apply_mask, "Festival_Weight"].values
                    new_core_weights = np.maximum(prev_core_weights, core_weight)
                    write_core = new_core_weights > prev_core_weights
                    big_frame.loc[core_apply_mask, "Festival_Weight"] = new_core_weights
                    core_idx = big_frame.loc[core_apply_mask].index
                    core_updated_idx.extend(core_idx[write_core].tolist())

                if core_updated_idx:
                    big_frame.loc[core_updated_idx, "Festival"] = fest_name

            if post_apply_mask.any():
                big_frame.loc[post_apply_mask, "Festival_Weight"] = np.maximum(
                    big_frame.loc[post_apply_mask, "Festival_Weight"].values,
                    post_weight
                )

        # Use festival impact model for uplift prediction
        festival_model = models["festival_uplift"]
        fest_rows = big_frame["Festival_Weight"] > 0
        if fest_rows.any():
            fest_features = pd.DataFrame({
                "Store": big_frame.loc[fest_rows, "Store"],
                "Month": big_frame.loc[fest_rows, "Month"],
                "StoreType_enc": big_frame.loc[fest_rows, "StoreType_enc"],
                "Assortment_enc": big_frame.loc[fest_rows, "Assortment_enc"],
                "CompetitionDistance": big_frame.loc[fest_rows, "CompetitionDistance"],
                "Promo2": big_frame.loc[fest_rows, "Promo2"],
            })
            ml_uplift = festival_model.predict(fest_features)
            # Blend ML uplift with calendar weight: 60% ML, 40% calendar
            calendar_weight = big_frame.loc[fest_rows, "Festival_Weight"].values
            blended_uplift = 0.6 * np.clip(ml_uplift, 0, 0.5) + 0.4 * calendar_weight

            fest_names = big_frame.loc[fest_rows, "Festival"].fillna("").astype(str).str.lower()
            fest_regions = big_frame.loc[fest_rows, "_Region"].astype(str)
            fest_states = big_frame.loc[fest_rows, "_State"].astype(str)

            diwali_mask = fest_names.str.contains("diwali", regex=False)
            if diwali_mask.any():
                diwali_floor = np.where(
                    (fest_regions == "South India").values,
                    1.15,
                    1.65
                )
                blended_uplift = np.where(diwali_mask.values, np.maximum(blended_uplift, diwali_floor), blended_uplift)

            # East realism: Durga core in West Bengal can outshine Diwali
            durga_wb_mask = fest_names.str.contains("durga", regex=False) & (fest_states.str.lower() == "west bengal")
            if durga_wb_mask.any():
                blended_uplift = np.where(durga_wb_mask.values, np.maximum(blended_uplift, 2.0), blended_uplift)

            big_frame.loc[fest_rows, "Festival_Weight"] = np.round(blended_uplift, 4)

        # Adjusted forecast
        big_frame["Adjusted"] = np.round(big_frame["Baseline"] * (1 + big_frame["Festival_Weight"]), 2)
        big_frame["FSI"] = np.where(big_frame["Festival"].notna(), np.round(big_frame["Festival_Weight"] * 100, 1), 0)

        # Collect as DataFrame slice (vectorized, no row-by-row loop)
        chunk = pd.DataFrame({
            "Store_ID": big_frame["_Store_ID"].astype(int),
            "Store_Name": big_frame["_Store_Name"],
            "State": big_frame["_State"],
            "Region": big_frame["_Region"],
            "Category": big_frame["_Category"],
            "Date": big_frame["Date"].dt.strftime("%Y-%m-%d"),
            "Month": big_frame["Month"].astype(int),
            "Festival": big_frame["Festival"],
            "Festival_Weight": big_frame["Festival_Weight"].astype(float),
            "FSI": big_frame["FSI"].astype(float),
            "Baseline": big_frame["Baseline"].astype(float),
            "Adjusted": big_frame["Adjusted"].astype(float),
        })
        all_frames.append(chunk)
        print(f"    {cat_name}: {len(chunk):,} rows")

    forecast_df = pd.concat(all_frames, ignore_index=True)

    out_path = os.path.join(OUT_DIR, "yearly_forecast_indian.csv")
    forecast_df.to_csv(out_path, index=False)
    print(f"\n  Saved: {out_path} ({len(forecast_df):,} rows)")
    return forecast_df


# ============================================================================
# STEP 3: ML-POWERED DISCOUNT RECOMMENDATIONS
# ============================================================================

def generate_ml_discounts(models, forecast_df):
    """Generate discount recommendations using XGBoost classifier."""
    print("\n" + "=" * 70)
    print("STEP 3: ML-POWERED DISCOUNT OPTIMIZATION (XGBoost)")
    print("=" * 70)

    discount_model = models["discount_clf"]
    le_tier = models["discount_le"]

    store_csv = pd.read_csv(os.path.join(DATA_DIR, "store.csv"))
    le_rg = joblib.load(os.path.join(MODEL_DIR, "le_region_discount.pkl"))

    # Build aggregated features per store × category × month
    agg = forecast_df.groupby(["Store_ID", "Store_Name", "State", "Region", "Category", "Month"]).agg(
        Avg_Adjusted=("Adjusted", "mean"),
        Std_Adjusted=("Adjusted", "std"),
        Avg_FSI=("FSI", "mean"),
        Has_Festival=("Festival", lambda x: x.notna().any()),
    ).reset_index()
    agg["Std_Adjusted"] = agg["Std_Adjusted"].fillna(0)

    # Map to Rossmann store features
    n_rossmann = len(store_csv)
    le_st = joblib.load(os.path.join(MODEL_DIR, "le_store_type.pkl"))
    le_as = joblib.load(os.path.join(MODEL_DIR, "le_assortment.pkl"))

    rmids = ((agg["Store_ID"] % n_rossmann) + 1).values
    rm_lookup = store_csv.set_index("Store")

    # Build features matching training scale
    # Scale adjusted values to approximate Rossmann Sales scale (mean ~5500)
    overall_mean = agg["Avg_Adjusted"].mean()
    rossmann_mean = 5500.0
    scale = rossmann_mean / max(overall_mean, 1.0)

    agg["Avg_Sales"] = agg["Avg_Adjusted"] * scale
    agg["Std_Sales"] = agg["Std_Adjusted"] * scale
    agg["Avg_Customers"] = agg["Avg_Sales"] * 0.105  # approximate Rossmann ratio

    st_types, as_types, comp_dists, promo2s = [], [], [], []
    for rmid in rmids:
        if rmid in rm_lookup.index:
            rm = rm_lookup.loc[rmid]
            st_val = rm["StoreType"] if pd.notna(rm.get("StoreType")) else "a"
            as_val = rm["Assortment"] if pd.notna(rm.get("Assortment")) else "a"
            cd = float(rm.get("CompetitionDistance", 0)) if pd.notna(rm.get("CompetitionDistance")) else 0
            p2 = int(rm.get("Promo2", 0)) if pd.notna(rm.get("Promo2")) else 0
        else:
            st_val, as_val, cd, p2 = "a", "a", 5000, 0
        st_types.append(st_val)
        as_types.append(as_val)
        comp_dists.append(cd)
        promo2s.append(p2)

    agg["StoreType_enc"] = le_st.transform(st_types)
    agg["Assortment_enc"] = le_as.transform(as_types)
    agg["CompetitionDistance"] = comp_dists
    agg["Promo2"] = promo2s

    def safe_rg_enc(r):
        try:
            return le_rg.transform([r])[0]
        except ValueError:
            return 0
    agg["Region_enc"] = agg["Region"].apply(safe_rg_enc)

    agg["Promo_Ratio"] = 0.3
    agg["Holiday_Ratio"] = agg["Has_Festival"].astype(float)
    agg["Store_rm"] = rmids

    # Predict in batch
    features_df = agg[["Store_rm", "Month", "Avg_Sales", "Std_Sales", "Avg_Customers",
                        "Promo_Ratio", "Holiday_Ratio", "StoreType_enc", "Assortment_enc",
                        "Region_enc", "CompetitionDistance", "Promo2"]].copy()
    features_df.columns = ["Store", "Month", "Avg_Sales", "Std_Sales", "Avg_Customers",
                           "Promo_Ratio", "Holiday_Ratio", "StoreType_enc", "Assortment_enc",
                           "Region_enc", "CompetitionDistance", "Promo2"]

    tier_indices = discount_model.predict(features_df)
    tiers = le_tier.inverse_transform(tier_indices)

    # Convert tiers to percentages
    tier_to_pct = {
        "NO_DISCOUNT": 0.0, "SMALL_5": 5.0, "MEDIUM_10": 10.0,
        "HIGH_15": 15.0, "CLEARANCE_20": 20.0
    }

    def tier_reason(tier, has_fest, fest_name=None):
        if tier == "NO_DISCOUNT":
            return f"High demand — ML confidence" + (f" ({fest_name})" if fest_name else "")
        elif tier == "SMALL_5":
            return "Moderate demand — ML suggests light promotion"
        elif tier == "MEDIUM_10":
            return "Average demand period — ML optimized discount"
        elif tier == "HIGH_15":
            return "Below-average demand — ML recommends promotion"
        else:
            return "Low demand / off-season — ML clearance recommendation"

    discount_data = []
    for i, row in agg.iterrows():
        tier = tiers[i]
        discount_data.append({
            "Store_ID": int(row["Store_ID"]),
            "Store_Name": row["Store_Name"],
            "State": row["State"],
            "Region": row["Region"],
            "Category": row["Category"],
            "Month": int(row["Month"]),
            "Year": PLANNING_YEAR,
            "Recommended_Discount_%": round(tier_to_pct.get(tier, 5.0), 1),
            "ML_Tier": tier,
            "Reason": tier_reason(tier, row["Has_Festival"]),
            "Avg_FSI": round(row["Avg_FSI"], 1),
        })

    discount_df = pd.DataFrame(discount_data)
    out_path = os.path.join(OUT_DIR, "discount_recommendations_enhanced.csv")
    discount_df.to_csv(out_path, index=False)
    print(f"  Saved: {out_path} ({len(discount_df):,} rows)")
    print(f"  ML Tier breakdown:")
    print(discount_df["ML_Tier"].value_counts().to_string())

    # Also generate weekly region-level discount for backend compatibility
    weekly_data = []
    for (region, month), grp in discount_df.groupby(["Region", "Month"]):
        avg_disc = grp["Recommended_Discount_%"].mean()
        month_start = pd.Timestamp(year=PLANNING_YEAR, month=month, day=1)
        for week in range(4):
            week_date = month_start + pd.DateOffset(weeks=week)
            weekly_data.append({
                "Region": region,
                "Week": week_date.strftime("%Y-%m-%d"),
                "Recommended_Discount": round(avg_disc, 1),
            })

    weekly_df = pd.DataFrame(weekly_data)
    weekly_path = os.path.join(OUT_DIR, "region_discount_recommendations.csv")
    weekly_df.to_csv(weekly_path, index=False)
    print(f"  Saved: {weekly_path} ({len(weekly_df):,} rows)")

    return discount_df


# ============================================================================
# STEP 4: ML-POWERED INVENTORY DECISIONS
# ============================================================================

def generate_ml_inventory(models, forecast_df, discount_df):
    """Generate inventory decisions using RF classifier + XGBoost priority scorer + stockout model."""
    print("\n" + "=" * 70)
    print("STEP 4: ML-POWERED INVENTORY DECISIONS (RF + XGBoost)")
    print("=" * 70)

    inv_clf = models["inventory_clf"]
    inv_priority_xgb = models["inventory_priority"]
    inv_le = models["inventory_le"]
    stockout_model = models["stockout_clf"]

    # Region encoding
    region_list = sorted(forecast_df["Region"].unique())
    region_to_enc = {r: i for i, r in enumerate(region_list)}
    cat_list = sorted(forecast_df["Category"].unique())
    cat_to_enc = {c: i for i, c in enumerate(cat_list)}

    # Compute demand stats per store × category
    stats = forecast_df.groupby(["Store_ID", "Store_Name", "State", "Region", "Category"]).agg(
        Avg_Daily_Demand=("Adjusted", "mean"),
        Std_Daily_Demand=("Adjusted", "std"),
    ).reset_index()
    stats["Std_Daily_Demand"] = stats["Std_Daily_Demand"].fillna(0)

    # Safety stock + reorder point (statistical foundation)
    LEAD_TIME = 7
    Z = 1.65  # 95% service level
    stats["Safety_Stock"] = Z * stats["Std_Daily_Demand"] * np.sqrt(LEAD_TIME)
    stats["Reorder_Point"] = stats["Avg_Daily_Demand"] * LEAD_TIME + stats["Safety_Stock"]

    # Simulate current inventory (realistic distribution)
    rng = np.random.default_rng(42)

    def sim_inventory(row):
        rop = row["Reorder_Point"]
        cat = row["Category"]
        high_cats = ["Electronics & Appliances", "Clothing & Apparel", "Snacks & Beverages"]
        if cat in high_cats:
            r = rng.random()
            if r < 0.6:
                return rop * rng.uniform(1.2, 2.0)
            elif r < 0.9:
                return rop * rng.uniform(0.85, 1.2)
            else:
                return rop * rng.uniform(0.5, 0.85)
        else:
            r = rng.random()
            if r < 0.4:
                return rop * rng.uniform(1.0, 1.8)
            elif r < 0.75:
                return rop * rng.uniform(0.7, 1.0)
            else:
                return rop * rng.uniform(0.3, 0.7)

    stats["Current_Stock"] = stats.apply(sim_inventory, axis=1).round(2)
    stats["Days_Supply"] = (stats["Current_Stock"] / stats["Avg_Daily_Demand"]).round(1)
    stats["Inventory_Position"] = stats["Current_Stock"] / stats["Reorder_Point"]

    # Check upcoming festivals (next 30 days from "today") by region
    today = pd.Timestamp(f"{PLANNING_YEAR}-03-03")  # simulation date
    regional_calendar = load_regional_festival_calendar()
    state_calendar = load_state_festival_calendar()
    state_to_region = forecast_df[["State", "Region"]].drop_duplicates().set_index("State")["Region"].to_dict()
    regional_events = build_regional_festival_events(regional_calendar)
    state_events = build_state_festival_events(state_calendar, state_to_region)
    festival_events = pd.concat([state_events, regional_events], ignore_index=True)
    upcoming = festival_events[
        (festival_events["StartDate"] >= today) &
        (festival_events["StartDate"] <= today + pd.Timedelta(days=30))
    ]
    upcoming_regions = set(upcoming["Region"].astype(str).tolist())
    upcoming_states = set(upcoming["State"].astype(str).tolist()) if "State" in upcoming.columns else set()
    has_upcoming_pan = (upcoming["Type"].str.lower() == "pan-indian").any() if not upcoming.empty else False

    # Prepare ML features
    stats["Festival_Upcoming"] = stats.apply(
        lambda row: 1 if (
            has_upcoming_pan
            or str(row["Region"]) in upcoming_regions
            or str(row["State"]) in upcoming_states
        ) else 0,
        axis=1
    )
    stats["Month"] = today.month
    stats["Region_enc"] = stats["Region"].map(region_to_enc).fillna(0).astype(int)
    stats["Category_enc"] = stats["Category"].map(cat_to_enc).fillna(0).astype(int)

    inv_features = stats[[
        "Avg_Daily_Demand", "Std_Daily_Demand", "Current_Stock",
        "Reorder_Point", "Safety_Stock", "Days_Supply",
        "Inventory_Position", "Festival_Upcoming", "Month",
        "Region_enc", "Category_enc"
    ]].copy()
    inv_features.columns = [
        "Avg_Daily_Demand", "Std_Daily_Demand", "Current_Inventory",
        "Reorder_Point", "Safety_Stock", "Days_Of_Supply",
        "Inventory_Position", "Festival_Upcoming", "Month",
        "Region_enc", "Category_enc"
    ]

    # ML predictions
    print("  Predicting inventory actions with RF classifier...")
    action_encoded = inv_clf.predict(inv_features)
    stats["Decision"] = inv_le.inverse_transform(action_encoded)

    print("  Predicting priority scores with XGBoost...")
    stats["Priority_Score"] = np.clip(inv_priority_xgb.predict(inv_features), 0, 100).round(1)

    # Stockout risk from XGBoost
    print("  Predicting stockout risk with XGBoost...")
    stockout_features = pd.DataFrame({
        "Current_Inventory": stats["Current_Stock"],
        "Avg_Daily_Demand": stats["Avg_Daily_Demand"],
        "Demand_Volatility": (stats["Std_Daily_Demand"] / stats["Avg_Daily_Demand"]).clip(0, 1),
        "Days_Of_Supply": stats["Days_Supply"],
        "Lead_Time": LEAD_TIME,
        "Days_Since_Reorder": rng.integers(0, 14, size=len(stats)),
        "Festival_In_7d": stats["Festival_Upcoming"],
        "Month": stats["Month"],
        "Region_enc": stats["Region_enc"],
        "Category_enc": stats["Category_enc"],
    })
    stockout_proba = stockout_model.predict_proba(stockout_features)[:, 1]
    stats["Stockout_Risk"] = np.round(stockout_proba, 4)

    # Recommended order quantities
    TARGET_DAYS = 21
    stats["Target_Level"] = stats["Avg_Daily_Demand"] * TARGET_DAYS + stats["Safety_Stock"]
    stats["Recommended_Order_Qty"] = np.maximum(0, stats["Target_Level"] - stats["Current_Stock"]).round(0).astype(int)

    # Save inventory decisions (compatible with backend)
    inv_out = stats[[
        "Store_ID", "Store_Name", "State", "Region", "Category",
        "Current_Stock", "Reorder_Point", "Safety_Stock", "Decision",
        "Days_Supply", "Stockout_Risk", "Priority_Score",
        "Recommended_Order_Qty", "Avg_Daily_Demand", "Std_Daily_Demand"
    ]].copy()

    inv_path = os.path.join(OUT_DIR, "inventory_decisions_indian.csv")
    inv_out.to_csv(inv_path, index=False)
    print(f"  Saved: {inv_path} ({len(inv_out):,} rows)")

    # Executive summary
    dec_counts = inv_out["Decision"].value_counts().to_dict()
    exec_df = pd.DataFrame([{
        "Total_Items": len(inv_out),
        "OK": dec_counts.get("OK", 0),
        "MONITOR": dec_counts.get("MONITOR", 0),
        "WATCHLIST": dec_counts.get("WATCHLIST", 0),
        "REORDER_SOON": dec_counts.get("REORDER SOON", 0),
        "REORDER_NOW": dec_counts.get("REORDER NOW", 0),
        "Avg_Stockout_Risk": round(inv_out["Stockout_Risk"].mean(), 4),
        "Avg_Priority_Score": round(inv_out["Priority_Score"].mean(), 2),
    }])
    exec_path = os.path.join(OUT_DIR, "inventory_decision_executive_summary.csv")
    exec_df.to_csv(exec_path, index=False)
    print(f"  Saved: {exec_path}")

    # KPI region summaries (for /kpi/region-summary endpoint)
    region_kpi = inv_out.groupby("Region").agg(
        Stores=("Store_ID", "nunique"),
        Avg_Stockout_Risk=("Stockout_Risk", "mean"),
        Max_Stockout_Risk=("Stockout_Risk", "max"),
        Avg_Reorder_Point=("Reorder_Point", "mean"),
        Total_Safety_Stock=("Safety_Stock", "sum"),
    ).reset_index()
    kpi_path = os.path.join(OUT_DIR, "inventory_kpi_region_summary.csv")
    region_kpi.to_csv(kpi_path, index=False)
    print(f"  Saved: {kpi_path}")

    return inv_out


# ============================================================================
# STEP 5: ACTION RECOMMENDATIONS
# ============================================================================

def generate_action_recommendations(forecast_df, inventory_df, discount_df):
    """Generate enhanced action recommendations combining all ML outputs."""
    print("\n" + "=" * 70)
    print("STEP 5: GENERATING ACTION RECOMMENDATIONS")
    print("=" * 70)

    action_data = []

    for _, inv in inventory_df.iterrows():
        actions = []

        # ML-predicted reorder actions
        if inv["Decision"] == "REORDER NOW":
            actions.append({
                "priority": "CRITICAL",
                "type": "Reorder",
                "message": f"ML predicts stockout risk {inv['Stockout_Risk']:.0%} — Order {inv['Recommended_Order_Qty']:.0f} units of {inv['Category']} immediately"
            })
        elif inv["Decision"] == "REORDER SOON":
            actions.append({
                "priority": "HIGH",
                "type": "Reorder",
                "message": f"Stock dropping (risk: {inv['Stockout_Risk']:.0%}) — Plan order of {inv['Recommended_Order_Qty']:.0f} units within 3 days"
            })
        elif inv["Decision"] == "WATCHLIST":
            actions.append({
                "priority": "MEDIUM",
                "type": "Monitor",
                "message": f"Inventory watchlist — {inv['Days_Supply']:.0f} days supply remaining, monitor closely"
            })

        # Overstock alert
        if inv["Days_Supply"] > 45:
            actions.append({
                "priority": "MEDIUM",
                "type": "Overstock",
                "message": f"High inventory ({inv['Days_Supply']:.0f} days supply). Consider promotion to reduce excess"
            })

        # Discount recommendation
        disc_row = discount_df[
            (discount_df["Store_ID"] == inv["Store_ID"]) &
            (discount_df["Category"] == inv["Category"]) &
            (discount_df["Month"] == 3)  # current month
        ]
        if not disc_row.empty:
            d = disc_row.iloc[0]
            if d["Recommended_Discount_%"] > 0:
                actions.append({
                    "priority": "MEDIUM",
                    "type": "Discount",
                    "message": f"XGBoost recommends {d['Recommended_Discount_%']:.0f}% discount — {d['Reason']}"
                })

        # Category tips
        category_tips = {
            'Groceries & Staples': "Fast-moving — maintain 15-20 day buffer",
            'Fresh Produce': "Perishable — order frequently (5-7 day max)",
            'Dairy & Eggs': "Short shelf-life — daily restocking recommended",
            'Snacks & Beverages': "Weekend peaks — increase Thu-Fri stock",
            'Personal Care': "Steady demand — maintain 30-day inventory",
            'Home Care': "Festival peaks — pre-stock 2 weeks before festivals",
            'Clothing & Apparel': "Seasonal — clearance for off-season items",
            'Electronics & Appliances': "Festival-driven — stock up 1 month before Diwali",
            'Kitchen & Dining': "Wedding season (Nov-Feb) — increase stock 20%",
            'Health & Wellness': "Growing category — review weekly trends"
        }
        if inv["Category"] in category_tips:
            actions.append({
                "priority": "INFO",
                "type": "Category Insight",
                "message": category_tips[inv["Category"]]
            })

        for act in actions:
            action_data.append({
                "Store_ID": inv["Store_ID"],
                "Store_Name": inv["Store_Name"],
                "State": inv["State"],
                "Region": inv["Region"],
                "Category": inv["Category"],
                "Priority": act["priority"],
                "Action_Type": act["type"],
                "Recommendation": act["message"],
                "Current_Stock": inv["Current_Stock"],
                "Days_Supply": inv["Days_Supply"],
                "Decision": inv["Decision"],
            })

    action_df = pd.DataFrame(action_data)
    out_path = os.path.join(OUT_DIR, "action_recommendations_enhanced.csv")
    action_df.to_csv(out_path, index=False)
    print(f"  Saved: {out_path} ({len(action_df):,} rows)")
    return action_df


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def run_pipeline(force_retrain=False):
    """Run the complete ML pipeline."""
    start_time = datetime.now()

    print("\n" + "=" * 70)
    print("  SEASONAL DEMAND FORECASTER — ML PIPELINE")
    print("  Models: Random Forest + XGBoost")
    print("=" * 70)

    # Step 0: Ensure Indian stores exist
    print("\n[Step 0] Checking Indian store data...")
    stores_df, cats_df = ensure_indian_stores()

    # Step 1: Train all ML models
    print("\n[Step 1] Training ML models...")
    models = train_all_models(force_retrain=force_retrain)

    # Step 2: Generate ML-powered forecast
    forecast_df = generate_ml_forecast(models, stores_df, cats_df)

    # Step 3: Generate ML-powered discounts
    discount_df = generate_ml_discounts(models, forecast_df)

    # Step 4: Generate ML-powered inventory decisions
    inventory_df = generate_ml_inventory(models, forecast_df, discount_df)

    # Step 5: Generate action recommendations
    action_df = generate_action_recommendations(forecast_df, inventory_df, discount_df)

    elapsed = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 70)
    print("  ML PIPELINE COMPLETE")
    print("=" * 70)
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Forecast:    {len(forecast_df):>10,} rows")
    print(f"  Discounts:   {len(discount_df):>10,} rows")
    print(f"  Inventory:   {len(inventory_df):>10,} rows")
    print(f"  Actions:     {len(action_df):>10,} rows")
    print(f"\n  All outputs saved to: {OUT_DIR}/")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline(force_retrain=True)
