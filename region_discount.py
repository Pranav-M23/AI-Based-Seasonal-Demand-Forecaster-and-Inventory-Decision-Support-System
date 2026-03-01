import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
OUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

IN_FILE = os.path.join(OUT_DIR, "yearly_festival_adjusted_region.csv")
OUT_CSV = os.path.join(OUT_DIR, "region_discount_recommendations.csv")
OUT_PNG = os.path.join(OUT_DIR, "region_discount_avg_over_time.png")


#  Step 13.2.1: Decision rules 
def discount_signal(uplift: float) -> str:
    # uplift is fraction (0.10 = 10%)
    if uplift >= 0.08:
        return "NO_DISCOUNT"
    elif uplift >= 0.03:
        return "OPTIONAL_DISCOUNT"
    elif uplift >= 0.0:
        return "APPLY_DISCOUNT_SMALL"
    else:
        return "APPLY_DISCOUNT_HIGH"


SIGNAL_TO_PCT = {
    "NO_DISCOUNT": 0,
    "OPTIONAL_DISCOUNT": 5,
    "APPLY_DISCOUNT_SMALL": 10,
    "APPLY_DISCOUNT_HIGH": 20
}

# Region sensitivity multiplier to apply region effect
REGION_MULT = {
    "Kerala": 1.00,
    "North-India": 1.10,
    "West-India": 1.05,
    "East-India": 1.05,
    "Tamil Nadu": 1.00,
    "Pan-India": 1.00
}


def safe_uplift(baseline, adjusted) -> float:
    if baseline is None or baseline == 0 or pd.isna(baseline):
        return 0.0
    if pd.isna(adjusted):
        return 0.0
    return (adjusted - baseline) / baseline


def main():
    # ---------- Step 13.2.2: Read Step 13.1 output ----------
    if not os.path.exists(IN_FILE):
        raise FileNotFoundError(f"Missing input: {IN_FILE} (Run Step 13.1 first)")

    df = pd.read_csv(IN_FILE)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # ---------- Step 13.2.3: Validate required columns ----------
    required_cols = ["Baseline_Forecast", "Adjusted_Forecast", "Region", "Store", "Date"]
    for c in required_cols:
        if c not in df.columns:
            raise ValueError(f"Missing required column in {IN_FILE}: {c}")

    # ---------- Step 13.2.4: Compute uplift% ----------
    df["Uplift_Pct"] = df.apply(
        lambda r: safe_uplift(r["Baseline_Forecast"], r["Adjusted_Forecast"]),
        axis=1
    )

    # ---------- Step 13.2.5: Convert uplift → signal ----------
    df["Discount_Signal"] = df["Uplift_Pct"].apply(discount_signal)

    # ---------- Step 13.2.6: Convert signal → discount% ----------
    df["Base_Discount_Pct"] = df["Discount_Signal"].map(SIGNAL_TO_PCT).fillna(0)

    # ---------- Step 13.2.7: Region multiplier → final discount% ----------
    df["Region_Multiplier"] = df["Region"].map(REGION_MULT).fillna(1.0)
    df["Discount_Pct"] = (df["Base_Discount_Pct"] * df["Region_Multiplier"]).clip(0, 30)

    # ---------- Step 13.2.8: Save output CSV ----------
    keep_cols = [
        "Date", "Store", "Region",
        "Baseline_Forecast", "Adjusted_Forecast",
        "Uplift_Pct",
        "Festival_List" if "Festival_List" in df.columns else None,
        "Discount_Signal", "Discount_Pct"
    ]
    keep_cols = [c for c in keep_cols if c is not None]

    df[keep_cols].to_csv(OUT_CSV, index=False)
    print(f"✅ Saved: {OUT_CSV}")

    # Step 13.2.9: Create plot (weekly average discount per region) 
    plot_df = df.copy()
    plot_df["Week"] = plot_df["Date"].dt.to_period("W").apply(lambda x: x.start_time)

    weekly = plot_df.groupby(["Week", "Region"])["Discount_Pct"].mean().reset_index()

    # show top 5 regions by rows
    top_regions = df["Region"].value_counts().head(5).index.tolist()

    plt.figure(figsize=(12, 5))
    for reg in top_regions:
        sub = weekly[weekly["Region"] == reg]
        plt.plot(sub["Week"], sub["Discount_Pct"], label=reg)

    plt.title("Region-wise Average Recommended Discount (Weekly)")
    plt.xlabel("Week")
    plt.ylabel("Discount (%)")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=200)
    plt.close()
    print(f"✅ Saved: {OUT_PNG}")

    
    print("• Rows processed:", len(df))
    print("• Regions covered:", df["Region"].nunique())
    print("• Discount signals used:", ", ".join(sorted(df["Discount_Signal"].unique().tolist())))


if __name__ == "__main__":
    main()
