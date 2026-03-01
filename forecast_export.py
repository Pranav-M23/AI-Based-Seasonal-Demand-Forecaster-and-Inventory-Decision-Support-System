import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
OUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

# ✅ Choose a window that contains Indian festivals within dataset timeline
TEST_START = pd.Timestamp("2015-03-01")
TEST_END   = pd.Timestamp("2015-04-30")

train = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
store = pd.read_csv(os.path.join(DATA_DIR, "store.csv"))
df = train.merge(store, on="Store", how="left")

df["Date"] = pd.to_datetime(df["Date"])
df = df[df["Open"] == 1]
df = df[df["Sales"] > 0]

df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month
df["WeekOfYear"] = df["Date"].dt.isocalendar()["week"].astype(int)

features = [
    "Store", "DayOfWeek", "Promo",
    "SchoolHoliday", "CompetitionDistance",
    "Promo2", "Year", "Month", "WeekOfYear"
]

df_model = df[["Date", "Store", "Sales"] + features].copy().fillna(0)

# Train on dates BEFORE the test window (no new dataset, same model type)
train_df = df_model[df_model["Date"] < TEST_START]
test_df  = df_model[(df_model["Date"] >= TEST_START) & (df_model["Date"] <= TEST_END)]

X_train, y_train = train_df[features], train_df["Sales"]
X_test, y_test   = test_df[features], test_df["Sales"]

rf = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)

y_pred = rf.predict(X_test)

out_df = test_df[["Date", "Store", "Sales"]].copy()
out_df["Predicted_Sales"] = y_pred
out_df = out_df.sort_values("Date")

# Overwrite the same file that multi_festival.py reads
out_path = os.path.join(OUT_DIR, "forecast_output.csv")
out_df.to_csv(out_path, index=False)
print(f"✅ Saved forecast window output: {out_path}")

# Optional plot for sanity (Step 11 style)
daily = out_df.groupby("Date")[["Sales", "Predicted_Sales"]].sum().reset_index()
plt.figure(figsize=(10,5))
plt.plot(daily["Date"], daily["Sales"], label="Actual")
plt.plot(daily["Date"], daily["Predicted_Sales"], label="Predicted")
plt.title("Forecast vs Actual (Window: Mar–Apr 2015)")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "forecast_vs_actual_window.png"), dpi=200)
plt.close()
print("✅ Saved: outputs/forecast_vs_actual_window.png")

