
import os
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================================
# PATHS
# ============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
OUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

FORECAST_FILE = os.path.join(OUT_DIR, "yearly_baseline_forecast.csv")
CAL_FILE = os.path.join(DATA_DIR, "festival_calender.csv")
STORE_REGION_FILE = os.path.join(DATA_DIR, "store_region.csv")

OUT_CSV = os.path.join(OUT_DIR, "yearly_festival_adjusted_region.csv")
OUT_PNG = os.path.join(OUT_DIR, "region_festival_adjusted_avg_per_store.png")
OUT_BAR_CAL = os.path.join(OUT_DIR, "festival_calendar_days_all.png")
OUT_BAR_IMPACT = os.path.join(OUT_DIR, "festival_tagged_days_all.png")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def norm_region(x):
    """Normalize region names to standard format"""
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


def safe_float(x, default=0.0):
    """Safely convert to float"""
    if pd.isna(x):
        return default
    s = str(x).strip().replace(" ", "")
    try:
        return float(s)
    except:
        return default


def combine_weights(weights):
    """
    Combine multiple festival weights using probabilistic formula.
    Formula: W = 1 - Π(1 - w_i)
    """
    w = 0.0
    for wi in weights:
        wi = max(0.0, float(wi))
        w = 1 - (1 - w) * (1 - wi)
    return w


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("\n=== STEP 13.1: Region-Aware Festival Adjustment ===\n")
    
    # Validate input files exist
    if not os.path.exists(FORECAST_FILE):
        raise FileNotFoundError(f"Missing: {FORECAST_FILE} (Run year_forecast.py first)")
    if not os.path.exists(CAL_FILE):
        raise FileNotFoundError(f"Missing: {CAL_FILE}")
    if not os.path.exists(STORE_REGION_FILE):
        raise FileNotFoundError(f"Missing: {STORE_REGION_FILE} (Run generating_store_region.py)")
    
    # Load data
    forecast = pd.read_csv(FORECAST_FILE)
    cal = pd.read_csv(CAL_FILE)
    sr = pd.read_csv(STORE_REGION_FILE)
    
    print(f"Loaded: {len(forecast):,} forecast rows, {len(cal)} festivals, {len(sr)} stores")
    
    # Parse dates
    forecast["Date"] = pd.to_datetime(forecast["Date"])
    cal["StartDate"] = pd.to_datetime(cal["StartDate"])
    cal["EndDate"] = pd.to_datetime(cal["EndDate"])
    
    # Handle Region column (add if missing)
    if "Region" not in cal.columns:
        print("  WARNING: No Region column in festival calendar!")
        print("    All festivals will be treated as Pan-India.")
        print("    Use festival_calender_enhanced.csv for region-aware behavior.")
        cal["Region"] = "Pan-India"
    
    # Normalize regions and weights
    cal["Region"] = cal["Region"].fillna("Pan-India").apply(norm_region)
    cal["Weight"] = cal["Weight"].apply(safe_float)
    sr["Region"] = sr["Region"].apply(norm_region)
    
    # Merge store-region mapping into forecast
    forecast = forecast.merge(sr, on="Store", how="left")
    forecast["Region"] = forecast["Region"].fillna("Pan-India").apply(norm_region)
    
    print(f"Regions: {sorted(forecast['Region'].unique())}")
    
    # Get festival order for consistent output
    festival_order = sorted(cal["Festival"].astype(str).unique().tolist())
    
    # Initialize tracking lists for each forecast row
    weights_per_row = [[] for _ in range(len(forecast))]
    festivals_per_row = [[] for _ in range(len(forecast))]
    
    # Apply region-aware festival logic
    for _, r in cal.iterrows():
        fest = str(r["Festival"]).strip()
        fest_region = str(r["Region"]).strip()
        w = float(r["Weight"])
        
        # Create date mask (rows within festival dates)
        date_mask = (forecast["Date"] >= r["StartDate"]) & (forecast["Date"] <= r["EndDate"])
        
        # Create region mask (rows in festival's region)
        if fest_region == "Pan-India":
            region_mask = pd.Series([True] * len(forecast), index=forecast.index)
        else:
            region_mask = (forecast["Region"] == fest_region)
        
        # Apply to matching rows
        mask = date_mask & region_mask
        idxs = forecast.index[mask].tolist()
        
        for i in idxs:
            weights_per_row[i].append(w)
            festivals_per_row[i].append(fest)
    
    # Build combined weight + festival list (EXACT match to original logic)
    combined = []
    festlist = []
    
    for wlist, flist in zip(weights_per_row, festivals_per_row):
        if not wlist:
            combined.append(0.0)
            festlist.append("None")
        else:
            combined.append(combine_weights(wlist))
            # Deduplicate while preserving order (same as original)
            seen = set()
            uniq = []
            for f in flist:
                if f not in seen:
                    uniq.append(f)
                    seen.add(f)
            festlist.append(";".join(uniq))
    
    # Add new columns to forecast (EXACT column names as original)
    forecast["Festival_Weight"] = combined
    forecast["Festival_List"] = festlist
    forecast["Adjusted_Forecast"] = forecast["Baseline_Forecast"] * (1 + forecast["Festival_Weight"])
    
    # Save main output CSV (SAME STRUCTURE as original)
    forecast.to_csv(OUT_CSV, index=False)
    print(f"\n✅ Saved: {OUT_CSV}")
    print(f"   Columns: {list(forecast.columns)}")
    
    # ---------- Generate visualizations ----------
    
    # Explode festival list for charts
    exploded = forecast[forecast["Festival_List"] != "None"][["Date", "Festival_List"]].drop_duplicates()
    if len(exploded):
        exploded = exploded.assign(Festival=exploded["Festival_List"].str.split(";")).explode("Festival")
    else:
        exploded = pd.DataFrame(columns=["Date", "Festival_List", "Festival"])
    
    # Chart 1: Calendar coverage (ALL festivals visible)
    cal_days = cal.copy()
    cal_days["CalendarDays"] = (cal_days["EndDate"] - cal_days["StartDate"]).dt.days + 1
    cal_days = cal_days.groupby("Festival")["CalendarDays"].sum().reindex(festival_order, fill_value=0)
    
    plt.figure(figsize=(10, 4))
    plt.bar(cal_days.index.astype(str), cal_days.values)
    plt.title("Festival Coverage (Calendar): Days per Festival (All Festivals)")
    plt.xlabel("Festival")
    plt.ylabel("Calendar Days")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_BAR_CAL, dpi=200)
    plt.close()
    
    # Chart 2: Actual impact (region-aware tagged days)
    if len(exploded):
        impact_days = exploded.groupby("Festival")["Date"].nunique()
    else:
        impact_days = pd.Series(dtype=int)
    impact_days = impact_days.reindex(festival_order, fill_value=0)
    
    plt.figure(figsize=(10, 4))
    plt.bar(impact_days.index.astype(str), impact_days.values)
    plt.title("Festival Coverage (Region-Aware): Tagged Days per Festival (All Festivals)")
    plt.xlabel("Festival")
    plt.ylabel("Tagged Days (Unique Dates)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_BAR_IMPACT, dpi=200)
    plt.close()
    
    # Chart 3: Time series by region (avg per store)
    region_store_counts = forecast.groupby("Region")["Store"].nunique().sort_values(ascending=False)
    top_regions = region_store_counts.head(4).index.tolist()
    
    plt.figure(figsize=(12, 5))
    for reg in top_regions:
        sub = forecast[forecast["Region"] == reg]
        daily = sub.groupby("Date")[["Adjusted_Forecast"]].sum().reset_index()
        store_count = sub["Store"].nunique()
        daily["Adj_Avg_Per_Store"] = daily["Adjusted_Forecast"] / max(store_count, 1)
        plt.plot(daily["Date"], daily["Adj_Avg_Per_Store"], label=f"{reg}")
    
    plt.title("Region-Based Festival-Adjusted Forecast (Average per Store)")
    plt.xlabel("Date")
    plt.ylabel("Sales (Avg per Store)")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=200)
    plt.close()
    
    print(f" Saved: {OUT_BAR_CAL}")
    print(f" Saved: {OUT_BAR_IMPACT}")
    print(f" Saved: {OUT_PNG}")
    
    # ---------- Summary statistics ----------
    affected_dates = exploded["Date"].nunique() if len(exploded) else 0
    impact_festivals = sorted(exploded["Festival"].astype(str).unique().tolist()) if len(exploded) else []
    
    n_affected = (forecast["Festival_Weight"] > 0).sum()
    total_baseline = forecast["Baseline_Forecast"].sum()
    total_adjusted = forecast["Adjusted_Forecast"].sum()
    total_incremental = total_adjusted - total_baseline
    
    print("\n=== Step 13.1 Summary (PPT-ready) ===")
    print(f"• Planning horizon dates: {forecast['Date'].nunique()}")
    print(f"• Stores covered: {forecast['Store'].nunique()}")
    print(f"• Regions present: {forecast['Region'].nunique()}")
    print(f"• Festival-affected dates: {affected_dates}")
    print(f"• Festivals in calendar (ALL): {', '.join(festival_order)}")
    print(f"• Festivals impacting forecast (within year + region): {', '.join(impact_festivals) if impact_festivals else 'None'}")
    
    print(f"\n--- Store distribution by Region ---")
    region_store_counts = forecast.groupby("Region")["Store"].nunique().sort_values(ascending=False)
    print(region_store_counts.to_string())
    
    print(f"\n--- Demand Impact ---")
    print(f"• Festival-affected rows: {n_affected:,} ({n_affected/len(forecast)*100:.1f}%)")
    print(f"• Total baseline demand: {total_baseline/1e6:.1f}M units")
    print(f"• Total adjusted demand: {total_adjusted/1e6:.1f}M units")
    print(f"• Incremental demand: {total_incremental/1e6:.1f}M units ({total_incremental/total_baseline*100:.1f}%)")
    
    print("\nStep 13.1 ")

if __name__ == "__main__":
    main()