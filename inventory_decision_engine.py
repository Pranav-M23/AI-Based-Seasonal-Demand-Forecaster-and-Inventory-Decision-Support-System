import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "outputs")

IN_KPI = os.path.join(OUT_DIR, "inventory_kpi_store_category.csv")

OUT_DECISIONS = os.path.join(OUT_DIR, "inventory_decisions_store_category.csv")
OUT_EXEC = os.path.join(OUT_DIR, "inventory_decision_executive_summary.csv")
OUT_PNG = os.path.join(OUT_DIR, "inventory_actions_by_region.png")
OUT_PRIORITY = os.path.join(OUT_DIR, "top_priority_reorders.csv")


def main():
    if not os.path.exists(IN_KPI):
        raise FileNotFoundError("Run Step 13.3 first (inventory_kpi.py)")

    df = pd.read_csv(IN_KPI)

    required = ["Store", "Region", "Product_Category", "Days_Of_Supply", "Current_Inventory", "Reorder_Point", "Stockout_Risk"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing columns in KPI file: {missing}")

    # ============================================================================
    # IMPROVED ACTION LOGIC (more granular)
    # ============================================================================
    
    # Calculate inventory position relative to ROP
    df["Inventory_Position"] = df["Current_Inventory"] / df["Reorder_Point"]
    
    # Multi-tier action system
    def classify_action(row):
        inv_pos = row["Inventory_Position"]
        dos = row["Days_Of_Supply"]
        
        if inv_pos >= 1.2:
            return "OK"  # Well-stocked
        elif inv_pos >= 0.85:
            return "MONITOR"  # Adequate but watch
        elif inv_pos >= 0.70:
            return "WATCHLIST"  # Getting low
        elif inv_pos >= 0.50:
            return "REORDER SOON"  # Below threshold
        else:
            return "REORDER NOW"  # Critical
    
    df["Action"] = df.apply(classify_action, axis=1)
    
    # Priority score (0-100) for reordering
    # Higher score = more urgent
    df["Priority_Score"] = np.clip(
        100 * (1 - df["Inventory_Position"]) + 
        20 * (1 / (df["Days_Of_Supply"] + 0.1)),  # Urgency from low DOS
        0, 100
    ).round(1)

    # Recommended Order Quantity (order up to 21 days demand + safety stock)
    TARGET_DAYS = 21
    df["Target_Level"] = df["Avg_Daily_Demand"] * TARGET_DAYS + df["Safety_Stock"]
    df["Recommended_Order_Qty"] = np.maximum(0, df["Target_Level"] - df["Current_Inventory"]).round(0).astype(int)
    
    # Order urgency (days until stockout)
    df["Days_Until_Stockout"] = np.where(
        df["Avg_Daily_Demand"] > 0,
        (df["Current_Inventory"] / df["Avg_Daily_Demand"]).round(1),
        999.0
    )

    df.to_csv(OUT_DECISIONS, index=False)
    print("✅ Saved:", OUT_DECISIONS)

    # ============================================================================
    # EXECUTIVE SUMMARY (improved metrics)
    # ============================================================================
    action_counts = df["Action"].value_counts().to_dict()
    
    exec_df = pd.DataFrame([{
        "Total_Items": len(df),
        "OK": action_counts.get("OK", 0),
        "MONITOR": action_counts.get("MONITOR", 0),
        "WATCHLIST": action_counts.get("WATCHLIST", 0),
        "REORDER_SOON": action_counts.get("REORDER SOON", 0),
        "REORDER_NOW": action_counts.get("REORDER NOW", 0),
        "Avg_Priority_Score": df["Priority_Score"].mean().round(2),
        "Critical_Items_Pct": ((df["Action"] == "REORDER NOW").sum() / len(df) * 100).round(2)
    }])
    exec_df.to_csv(OUT_EXEC, index=False)
    print("✅ Saved:", OUT_EXEC)
    
    # ============================================================================
    # TOP PRIORITY REORDERS (new output for immediate action)
    # ============================================================================
    critical = df[df["Action"].isin(["REORDER NOW", "REORDER SOON"])].copy()
    critical = critical.sort_values("Priority_Score", ascending=False).head(50)
    
    priority_out = critical[[
        "Store", "Region", "Product_Category", "Action", "Priority_Score",
        "Current_Inventory", "Reorder_Point", "Days_Until_Stockout",
        "Recommended_Order_Qty"
    ]].copy()
    
    priority_out.to_csv(OUT_PRIORITY, index=False)
    print("✅ Saved:", OUT_PRIORITY)

    # ============================================================================
    # VISUALIZATION 1: Stacked actions per region
    # ============================================================================
    action_order = ["OK", "MONITOR", "WATCHLIST", "REORDER SOON", "REORDER NOW"]
    pivot = df.groupby(["Region", "Action"]).size().unstack(fill_value=0)
    
    # Reorder columns
    pivot = pivot.reindex(columns=action_order, fill_value=0)

    plt.figure(figsize=(12, 6))
    colors = ['#2ecc71', '#3498db', '#f39c12', '#e67e22', '#e74c3c']
    pivot.plot(kind="bar", stacked=True, ax=plt.gca(), color=colors)
    plt.title("Inventory Actions by Region (Step 13.4 - Improved)", fontsize=14, fontweight='bold')
    plt.xlabel("Region")
    plt.ylabel("Count (Store×Category)")
    plt.legend(title="Action", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=200, bbox_inches='tight')
    plt.close()
    print("✅ Saved:", OUT_PNG)

   
    print("\n=== Step 13.4 Summary  ===")
    print(f"• Total items analyzed: {len(df):,}")
    print("\n--- Action Distribution ---")
    for action in action_order:
        count = action_counts.get(action, 0)
        pct = (count / len(df)) * 100
        print(f"  {action:15s}: {count:4d} ({pct:5.1f}%)")
    
    print(f"\n• Average Priority Score: {df['Priority_Score'].mean():.1f}/100")
    print(f"• Items needing immediate action: {(df['Action'] == 'REORDER NOW').sum()}")
    print(f"• Total reorder quantity needed: {df['Recommended_Order_Qty'].sum():,.0f} units")
    
    # Region-wise critical items
    print("\n--- Critical Items by Region ---")
    critical_by_region = df[df["Action"] == "REORDER NOW"].groupby("Region").size().sort_values(ascending=False)
    for region, count in critical_by_region.items():
        print(f"  {region}: {count} items")


if __name__ == "__main__":
    main()