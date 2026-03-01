import pandas as pd
import matplotlib.pyplot as plt

# Load Diwali dataset

df = pd.read_csv("Data/Diwali Sales Data.csv",encoding="latin1")

print("=== DIWALI DATASET ===")
print("Shape:", df.shape)
print("\nColumns:\n", list(df.columns))
print("\nSample rows:")
print(df.head())

print("\nMissing values (top 15):")
print(df.isnull().sum().sort_values(ascending=False).head(15))

# Identify purchase column

# Common names in Diwali datasets: "Amount", "Purchase", "Purchase Amount"
possible_amount_cols = ["Amount", "Purchase", "Purchase Amount", "Purchase_Amount", "PurchaseAmount"]
amount_col = None

for c in possible_amount_cols:
    if c in df.columns:
        amount_col = c
        break

if amount_col is None:
    # fallback: try to detect a numeric column that looks like purchase amount
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    # choose a likely candidate (largest mean)
    if numeric_cols:
        amount_col = df[numeric_cols].mean().sort_values(ascending=False).index[0]

print(f"\nUsing purchase column: {amount_col}")

# Clean amount column (remove negatives / NaNs)
df = df[df[amount_col].notna()]
df = df[df[amount_col] >= 0]


print("\nPurchase amount summary:")
print(df[amount_col].describe())


#  Category-wise purchase analysis
# Product category columns can vary; commonly Product_Category or Product_Category_1 etc.
category_cols = [c for c in df.columns if "Product_Category" in c or "Product Category" in c]

print("\nDetected category columns:", category_cols)

if category_cols:
    cat = category_cols[0]  # use first category column
    top_cat = (
        df.groupby(cat)[amount_col]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    print(f"\nTop 10 categories by total {amount_col}:")
    print(top_cat)

    top_cat.plot(kind="bar")
    plt.title(f"Top 10 Categories by Total {amount_col} (Diwali)")
    plt.xlabel("Category")
    plt.ylabel(f"Total {amount_col}")
    plt.tight_layout()
    plt.show()
else:
    print("\nNo product category column found. Skipping category plot.")

#  Segment analysis 

# Useful columns often: Gender, Age Group, Marital_Status, City_Category, Occupation
segment_candidates = ["Gender", "Age Group", "Age", "Marital_Status", "City_Category", "Occupation"]

for seg in segment_candidates:
    if seg in df.columns:
        seg_stats = df.groupby(seg)[amount_col].mean().sort_values(ascending=False).head(10)
        print(f"\nAverage {amount_col} by {seg} (top 10):")
        print(seg_stats)

        seg_stats.plot(kind="bar")
        plt.title(f"Average {amount_col} by {seg} (Diwali)")
        plt.xlabel(seg)
        plt.ylabel(f"Average {amount_col}")
        plt.tight_layout()
        plt.show()



print("This dataset provides festival-period purchase patterns by category and customer segment.")
print("We will use it as contextual evidence to define Festival Shock Index (FSI) behavior during Diwali.")
