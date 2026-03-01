import pandas as pd
import matplotlib.pyplot as plt
import os


DATA_PATH = "Data/Diwali Sales Data.csv"
OUTPUT_DIR = "outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# LOAD DATA (handle encoding)

df = pd.read_csv(DATA_PATH, encoding="latin1", low_memory=False)

print("Loaded Diwali dataset:", df.shape)


# CLEAN DATA
df = df.dropna(axis=1, how="all")        # drop fully empty columns
df = df[df["Amount"].notna()]
df = df[df["Amount"] >= 0]


# COMPUTE BASELINE & FESTIVAL SALES
# Baseline proxy = median spend per category
# Festival sales = mean spend per category

fsi_df = df.groupby("Product_Category").agg(
    baseline_sales=("Amount", "median"),
    festival_sales=("Amount", "mean"),
    total_sales=("Amount", "sum"),
    orders=("Orders", "sum")
).reset_index()


# FESTIVAL SHOCK INDEX (FSI)
#-----------------------------
# FSI = (festival_sales - baseline_sales) / baseline_sales
fsi_df["FSI"] = (
    (fsi_df["festival_sales"] - fsi_df["baseline_sales"])
    / fsi_df["baseline_sales"]
)

fsi_df = fsi_df.sort_values("FSI", ascending=False)

print("\nTop FSI Categories:")
print(fsi_df.head())


# SAVE OUTPUT
# -----------------------------
fsi_df.to_csv(f"{OUTPUT_DIR}/diwali_fsi.csv", index=False)

# -----------------------------
# PLOT

plt.figure(figsize=(10,5))
plt.bar(fsi_df["Product_Category"][:10], fsi_df["FSI"][:10])
plt.xticks(rotation=60, ha="right")
plt.title("Festival Shock Index (Diwali)")
plt.ylabel("FSI")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/diwali_fsi.png", dpi=200)
plt.show()
