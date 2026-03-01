import pandas as pd


# -----------------------------
FSI_FILE = "outputs/diwali_fsi.csv"

# Thresholds 
HIGH_DEMAND_THRESHOLD = 0.05     # strong festival uplift
LOW_DEMAND_THRESHOLD = 0.00      # neutral or negative

# -----------------------------
# LOAD FSI DATA
# -----------------------------
fsi_df = pd.read_csv(FSI_FILE)

# -----------------------------
# DISCOUNT SIGNAL LOGIC
# -----------------------------
def discount_signal(fsi):
    if fsi >= HIGH_DEMAND_THRESHOLD:
        return "NO_DISCOUNT (High Demand)"
    elif fsi <= LOW_DEMAND_THRESHOLD:
        return "APPLY_DISCOUNT"
    else:
        return "OPTIONAL_DISCOUNT"

fsi_df["Discount_Signal"] = fsi_df["FSI"].apply(discount_signal)

# -----------------------------
# OUTPUT

print("\nDiscount Recommendations:")
print(fsi_df[["Product_Category", "FSI", "Discount_Signal"]].head(10))

fsi_df.to_csv("outputs/diwali_discount_signals.csv", index=False)