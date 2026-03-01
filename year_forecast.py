import os
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
OUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

TRAIN_FILE = os.path.join(DATA_DIR, "train.csv")
STORE_FILE = os.path.join(DATA_DIR, "store.csv")

MODEL_FILE = os.path.join(OUT_DIR, "rf_baseline_model.pkl")
OUT_FORECAST = os.path.join(OUT_DIR, "yearly_baseline_forecast.csv")


PLANNING_YEAR = 2026   #  set  2026 as your planning year for the full-year forecast 
PROMO_DEFAULT = 0
SCHOOL_HOLIDAY_DEFAULT = 0


FEATURES = [
    "Store", "DayOfWeek", "Promo",
    "SchoolHoliday", "CompetitionDistance",
    "Promo2", "Year", "Month", "WeekOfYear"
]

def train_model():
    train = pd.read_csv(TRAIN_FILE)
    store = pd.read_csv(STORE_FILE)

    df = train.merge(store, on="Store", how="left")
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[df["Open"] == 1]
    df = df[df["Sales"] > 0]

    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["WeekOfYear"] = df["Date"].dt.isocalendar()["week"].astype(int)

    df_model = df[FEATURES + ["Sales"]].copy().fillna(0)

    X = df_model[FEATURES]
    y = df_model["Sales"]

    rf = RandomForestRegressor(
        n_estimators=120,
        max_depth=15,
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X, y)

    joblib.dump(rf, MODEL_FILE)
    print(f"✅ Model saved: {MODEL_FILE}")
    return rf

def build_planning_frame():
    store = pd.read_csv(STORE_FILE)

    # Create one full year of dates (planning horizon)
    dates = pd.date_range(start=f"{PLANNING_YEAR}-01-01", end=f"{PLANNING_YEAR}-12-31", freq="D")

    # Cross join: all stores x all dates
    stores = store[["Store", "CompetitionDistance", "Promo2"]].copy()
    dates_df = pd.DataFrame({"Date": dates})
    dates_df["key"] = 1
    stores["key"] = 1

    plan = stores.merge(dates_df, on="key").drop("key", axis=1)

    # Date features
    plan["DayOfWeek"] = plan["Date"].dt.dayofweek + 1  # Rossmann DayOfWeek is 1–7
    plan["Year"] = plan["Date"].dt.year
    plan["Month"] = plan["Date"].dt.month
    plan["WeekOfYear"] = plan["Date"].dt.isocalendar()["week"].astype(int)

    # Unknown future inputs → simple defaults (acceptable for decision-support prototype)
    plan["Promo"] = PROMO_DEFAULT
    plan["SchoolHoliday"] = SCHOOL_HOLIDAY_DEFAULT

    plan = plan.fillna(0)
    return plan

def main():
    # Load or train model
    if os.path.exists(MODEL_FILE):
        rf = joblib.load(MODEL_FILE)
        print(f"✅ Loaded model: {MODEL_FILE}")
    else:
        rf = train_model()

    plan = build_planning_frame()

    # Predict baseline forecast for the whole year
    X_plan = plan[FEATURES]
    plan["Baseline_Forecast"] = rf.predict(X_plan)

    
    plan.to_csv(OUT_FORECAST, index=False)
    print(f"✅ Yearly baseline forecast saved: {OUT_FORECAST}")
    print("Rows:", len(plan), "| Unique dates:", plan["Date"].nunique(), "| Stores:", plan["Store"].nunique())

if __name__ == "__main__":
    main()
