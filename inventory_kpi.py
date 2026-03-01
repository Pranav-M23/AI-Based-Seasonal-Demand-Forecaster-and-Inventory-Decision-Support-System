import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
OUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

FORECAST_FILE = os.path.join(OUT_DIR, "yearly_festival_adjusted_region.csv")   # Step 13.1
DISCOUNT_FILE = os.path.join(OUT_DIR, "region_discount_recommendations.csv")   # Step 13.2

OUT_STORE_LEVEL = os.path.join(OUT_DIR, "inventory_kpi_store_level.csv")
OUT_STORE_CATEGORY = os.path.join(OUT_DIR, "inventory_kpi_store_category.csv")
OUT_REGION_SUMMARY = os.path.join(OUT_DIR, "inventory_kpi_region_summary.csv")
OUT_REGION_CAT_SUMMARY = os.path.join(OUT_DIR, "inventory_kpi_region_category_summary.csv")

OUT_TOP2_PER_REGION = os.path.join(OUT_DIR, "top2_risk_categories_per_region.png")
OUT_MAX_RISK_REGION = os.path.join(OUT_DIR, "max_stockout_risk_by_region.png")
OUT_INVENTORY_DIST = os.path.join(OUT_DIR, "inventory_action_distribution.png")


def log(msg: str):
    print(f"👉 {msg}", flush=True)


def safe_float(x, default=np.nan):
    try:
        if pd.isna(x):
            return default
        s = str(x).strip().replace(" ", "").replace("%", "")
        return float(s)
    except:
        return default


def norm_region(x: str) -> str:
    if pd.isna(x):
        return "Pan-India"
    s = str(x).strip().replace("_", " ").replace("-", " ")
    s = " ".join(s.split())
    mapping = {
        "pan india": "Pan-India",
        "panindia": "Pan-India",
        "north india": "North-India",
        "north": "North-India",
        "west india": "West-India",
        "west": "West-India",
        "east india": "East-India",
        "east": "East-India",
        "tamilnadu": "Tamil Nadu",
        "tamil nadu": "Tamil Nadu",
        "kerala": "Kerala",
    }
    return mapping.get(s.lower(), s)


def compute_z(service_level: float) -> float:
    table = {0.90: 1.28, 0.95: 1.65, 0.97: 1.88, 0.98: 2.05, 0.99: 2.33}
    return table.get(service_level, 1.65)


def pick_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols = list(df.columns)
    lower_map = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def find_discount_column(disc: pd.DataFrame) -> str | None:
    candidates = [
        "Recommended_Discount", "RecommendedDiscount",
        "Discount", "DiscountPercent", "Discount_%", "DiscountPct", "Discount_Pct",
        "Avg_Recommended_Discount", "Region_Avg_Discount",
        "DiscountRate", "Rec_Discount", "recommended_discount"
    ]
    col = pick_column(disc, candidates)
    if col:
        return col

    for c in disc.columns:
        if "discount" in str(c).lower():
            return c

    return None


def find_week_column(disc: pd.DataFrame) -> str | None:
    candidates = ["Week", "WeekStart", "week_start", "Week_Start", "StartOfWeek", "Date"]
    col = pick_column(disc, candidates)
    if col:
        return col

    for c in disc.columns:
        if "week" in str(c).lower():
            return c

    for c in disc.columns:
        if str(c).lower() == "region":
            continue
        parsed = pd.to_datetime(disc[c], errors="coerce")
        if parsed.notna().mean() > 0.8:
            return c

    return None


def week_start_monday(dt_series: pd.Series) -> pd.Series:
    """
    Fast week start: Monday for each date.
    """
    d = pd.to_datetime(dt_series, errors="coerce")
    return (d - pd.to_timedelta(d.dt.weekday, unit="D")).dt.normalize()


# ============================================================================
# IMPROVED INVENTORY SIMULATION
# ============================================================================

def simulate_realistic_inventory(stats: pd.DataFrame, rng) -> pd.DataFrame:
    """
    Create more realistic inventory levels with category-based behavior.
    
    Strategy:
    - High-demand categories (Games & Toys, Electronics): 60% well-stocked, 30% watchlist, 10% critical
    - Medium categories: 40% well-stocked, 40% watchlist, 20% critical  
    - Low-demand categories: 30% well-stocked, 40% watchlist, 30% critical
    """
    
    # Define category risk profiles
    HIGH_DEMAND_CATS = ["Games & Toys", "Electronics & Gadgets", "Clothing & Apparel"]
    MEDIUM_DEMAND_CATS = ["Food", "Home Decor", "Footwear & Shoes"]
    LOW_DEMAND_CATS = ["Tupperware", "Furniture", "Pet Care", "Sports Products"]
    
    inventory_levels = []
    
    for idx, row in stats.iterrows():
        category = row["Product_Category"]
        rop = row["Reorder_Point"]
        
        # Determine inventory level based on category
        if category in HIGH_DEMAND_CATS:
            # Better managed inventory
            rand = rng.random()
            if rand < 0.60:  # 60% well-stocked
                level = rop * rng.uniform(1.2, 2.0)  # Above ROP
            elif rand < 0.90:  # 30% watchlist
                level = rop * rng.uniform(0.85, 1.2)  # Near ROP
            else:  # 10% critical
                level = rop * rng.uniform(0.5, 0.85)  # Below ROP
                
        elif category in MEDIUM_DEMAND_CATS:
            rand = rng.random()
            if rand < 0.40:  # 40% well-stocked
                level = rop * rng.uniform(1.1, 1.8)
            elif rand < 0.80:  # 40% watchlist
                level = rop * rng.uniform(0.8, 1.1)
            else:  # 20% critical
                level = rop * rng.uniform(0.4, 0.8)
                
        else:  # LOW_DEMAND_CATS or unknown
            rand = rng.random()
            if rand < 0.30:  # 30% well-stocked
                level = rop * rng.uniform(1.0, 1.5)
            elif rand < 0.70:  # 40% watchlist
                level = rop * rng.uniform(0.75, 1.0)
            else:  # 30% critical
                level = rop * rng.uniform(0.3, 0.75)
        
        inventory_levels.append(level)
    
    stats["Current_Inventory"] = inventory_levels
    return stats


def main():
    if not os.path.exists(FORECAST_FILE):
        raise FileNotFoundError(f"Missing: {FORECAST_FILE}")
    if not os.path.exists(DISCOUNT_FILE):
        raise FileNotFoundError(f"Missing: {DISCOUNT_FILE}")

    log("Reading forecast + discount files...")
    df = pd.read_csv(FORECAST_FILE)
    disc = pd.read_csv(DISCOUNT_FILE)

    log(f"Forecast rows: {len(df):,} | Discount rows: {len(disc):,}")

    needed = {"Date", "Store", "Region"}
    if not needed.issubset(df.columns):
        raise KeyError(f"Forecast file missing columns: {needed - set(df.columns)}")

    # Choose demand column
    demand_col = None
    for c in ["Adjusted_Forecast", "Baseline_Forecast", "Predicted_Sales", "Predicted_Sales_Total"]:
        if c in df.columns:
            demand_col = c
            break
    if demand_col is None:
        raise KeyError("No forecast demand column found. Expected Adjusted_Forecast/Baseline_Forecast/Predicted_Sales")

    # Parse + normalize
    log("Parsing dates + normalizing region...")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).copy()
    df["Region"] = df["Region"].apply(norm_region)

    # Category (if missing)
    if "Product_Category" not in df.columns:
        categories = [
            "Food", "Clothing & Apparel", "Electronics & Gadgets", "Footwear & Shoes",
            "Home Decor", "Games & Toys", "Sports Products", "Tupperware", "Furniture", "Pet Care"
        ]
        df["Product_Category"] = df["Store"].astype(int).apply(lambda s: categories[s % len(categories)])

    # Make grouping columns categorical (big speed boost)
    df["Region"] = df["Region"].astype("category")
    df["Product_Category"] = df["Product_Category"].astype("category")

    # Discount column + week column
    if "Region" not in disc.columns:
        region_col = pick_column(disc, ["Region"])
        if not region_col:
            print("❌ Discount CSV columns:", list(disc.columns))
            raise KeyError("Discount file must contain a 'Region' column.")
        disc = disc.rename(columns={region_col: "Region"})

    disc["Region"] = disc["Region"].apply(norm_region)

    disc_col = find_discount_column(disc)
    week_col = find_week_column(disc)
    if disc_col is None or week_col is None:
        print("❌ Discount CSV columns:", list(disc.columns))
        print("Detected discount column:", disc_col)
        print("Detected week/date column:", week_col)
        raise KeyError("Discount CSV must include a week/date column and a discount column.")

    log(f"Detected discount column: {disc_col} | week column: {week_col}")

    disc[week_col] = pd.to_datetime(disc[week_col], errors="coerce")
    disc = disc.dropna(subset=[week_col]).copy()
    disc[disc_col] = disc[disc_col].map(safe_float).fillna(0.0)

    # FAST week start (Monday) + prevent merge explosion by deduplicating
    disc["Week"] = week_start_monday(disc[week_col])
    disc = disc.groupby(["Region", "Week"], as_index=False)[disc_col].mean()  # one row per Region+Week

    # Weekly key for df
    df["Week"] = week_start_monday(df["Date"])

    log("Merging discount into forecast (Region+Week)...")
    before = len(df)
    df = df.merge(disc[["Region", "Week", disc_col]], on=["Region", "Week"], how="left")
    after = len(df)
    if after != before:
        log(f"⚠️ Row count changed after merge: {before:,} -> {after:,} (should NOT happen).")

    df[disc_col] = df[disc_col].fillna(0.0)

    # Demand adjustment
    alpha = 0.8
    df["Demand"] = df[demand_col].map(safe_float).fillna(0.0).astype(np.float32)
    df["Demand_With_Discount"] = (df["Demand"] * (1 + alpha * (df[disc_col].astype(np.float32) / 100.0))).astype(np.float32)

    # Inventory assumptions
    LEAD_TIME_DAYS = 7
    SERVICE_LEVEL = 0.95
    z = compute_z(SERVICE_LEVEL)

    log("Computing store-category KPIs (groupby)...")
    grp = df.groupby(["Store", "Region", "Product_Category"], observed=True)["Demand_With_Discount"]
    stats = grp.agg(Avg_Daily_Demand="mean", Std_Daily_Demand="std").reset_index()
    stats["Std_Daily_Demand"] = stats["Std_Daily_Demand"].fillna(0.0)

    stats["Safety_Stock"] = z * stats["Std_Daily_Demand"] * np.sqrt(LEAD_TIME_DAYS)
    stats["Reorder_Point"] = stats["Avg_Daily_Demand"] * LEAD_TIME_DAYS + stats["Safety_Stock"]

    # ============================================================================
    # IMPROVED INVENTORY SIMULATION (OPTION 1 FIX)
    # ============================================================================
    log("Simulating realistic inventory levels (category-based)...")
    rng = np.random.default_rng(42)
    stats = simulate_realistic_inventory(stats, rng)

    # Days of supply (needed for Step 13.4)
    stats["Days_Of_Supply"] = np.where(
        stats["Avg_Daily_Demand"] > 0,
        stats["Current_Inventory"] / stats["Avg_Daily_Demand"],
        0.0
    )

    # Risk (relative shortage vs ROP)
    rp = stats["Reorder_Point"].to_numpy()
    ci = stats["Current_Inventory"].to_numpy()
    stats["Stockout_Risk"] = np.where(
        rp > 0,
        np.clip((rp - ci) / rp, 0, 1),
        0.0
    )

    log("Saving CSV outputs...")
    stats.to_csv(OUT_STORE_CATEGORY, index=False)
    print(f"✅ Saved: {OUT_STORE_CATEGORY}")

    store_level = stats.groupby(["Store", "Region"], observed=True).agg(
        Avg_Stockout_Risk=("Stockout_Risk", "mean"),
        Max_Stockout_Risk=("Stockout_Risk", "max"),
        Avg_Reorder_Point=("Reorder_Point", "mean"),
        Total_Safety_Stock=("Safety_Stock", "sum")
    ).reset_index()
    store_level.to_csv(OUT_STORE_LEVEL, index=False)
    print(f"✅ Saved: {OUT_STORE_LEVEL}")

    region_summary = store_level.groupby("Region", observed=True).agg(
        Stores=("Store", "nunique"),
        Avg_Stockout_Risk=("Avg_Stockout_Risk", "mean"),
        Max_Stockout_Risk=("Max_Stockout_Risk", "max"),
        Avg_Reorder_Point=("Avg_Reorder_Point", "mean"),
        Total_Safety_Stock=("Total_Safety_Stock", "sum")
    ).reset_index()
    region_summary.to_csv(OUT_REGION_SUMMARY, index=False)
    print(f"✅ Saved: {OUT_REGION_SUMMARY}")

    region_cat = stats.groupby(["Region", "Product_Category"], observed=True).agg(
        Stores=("Store", "nunique"),
        Avg_Stockout_Risk=("Stockout_Risk", "mean"),
        Max_Stockout_Risk=("Stockout_Risk", "max"),
        Avg_Reorder_Point=("Reorder_Point", "mean")
    ).reset_index()
    region_cat.to_csv(OUT_REGION_CAT_SUMMARY, index=False)
    print(f"✅ Saved: {OUT_REGION_CAT_SUMMARY}")

    log("Generating charts...")
    
    # Chart 1: Top-2 categories per region
    top2 = (
        region_cat.sort_values(["Region", "Avg_Stockout_Risk"], ascending=[True, False])
        .groupby("Region", observed=True)
        .head(2)
        .copy()
    )
    top2["Label"] = top2["Region"].astype(str) + " | " + top2["Product_Category"].astype(str)

    plt.figure(figsize=(13, 5))
    plt.bar(top2["Label"], top2["Avg_Stockout_Risk"].values)
    plt.title("Top-2 Risky Categories per Region (Balanced Comparison)")
    plt.xlabel("Region | Category")
    plt.ylabel("Avg Stockout Risk (0–1)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_TOP2_PER_REGION, dpi=200)
    plt.close()
    print(f"✅ Saved: {OUT_TOP2_PER_REGION}")

    # Chart 2: Max risk by region
    rr = region_summary.sort_values("Max_Stockout_Risk", ascending=False)
    plt.figure(figsize=(10, 4))
    plt.bar(rr["Region"].astype(str), rr["Max_Stockout_Risk"].values)
    plt.title("Max Stockout Risk by Region (Executive Summary)")
    plt.xlabel("Region")
    plt.ylabel("Max Stockout Risk (0–1)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_MAX_RISK_REGION, dpi=200)
    plt.close()
    print(f"✅ Saved: {OUT_MAX_RISK_REGION}")
    
    # Chart 3: NEW - Inventory action distribution
    log("Creating inventory action distribution chart...")
    action_counts = {
        "Well-Stocked (>1.2x ROP)": int((stats["Current_Inventory"] > 1.2 * stats["Reorder_Point"]).sum()),
        "Adequate (0.85-1.2x ROP)": int(((stats["Current_Inventory"] >= 0.85 * stats["Reorder_Point"]) & 
                                         (stats["Current_Inventory"] <= 1.2 * stats["Reorder_Point"])).sum()),
        "Watchlist (0.7-0.85x ROP)": int(((stats["Current_Inventory"] >= 0.7 * stats["Reorder_Point"]) & 
                                          (stats["Current_Inventory"] < 0.85 * stats["Reorder_Point"])).sum()),
        "Critical (<0.7x ROP)": int((stats["Current_Inventory"] < 0.7 * stats["Reorder_Point"]).sum())
    }
    
    plt.figure(figsize=(10, 6))
    colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c']
    plt.bar(action_counts.keys(), action_counts.values(), color=colors)
    plt.title("Inventory Status Distribution (Improved Simulation)", fontsize=14, fontweight='bold')
    plt.ylabel("Number of Store×Category Combinations")
    plt.xticks(rotation=15, ha="right")
    
    # Add percentage labels on bars
    total = sum(action_counts.values())
    for i, (k, v) in enumerate(action_counts.items()):
        pct = (v / total) * 100
        plt.text(i, v + 10, f"{v}\n({pct:.1f}%)", ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(OUT_INVENTORY_DIST, dpi=200)
    plt.close()
    print(f"✅ Saved: {OUT_INVENTORY_DIST}")

    print("\n=== Step 13.3 Summary  ===")
    print("• Demand column:", demand_col)
    print("• Discount column:", disc_col)
    print("• Lead Time Days:", LEAD_TIME_DAYS)
    print("• Service Level:", SERVICE_LEVEL, f"(z={z})")
    print("\n--- Inventory Status Distribution ---")
    for k, v in action_counts.items():
        pct = (v / total) * 100
        print(f"  {k}: {v} ({pct:.1f}%)")


if __name__ == "__main__":
    main()