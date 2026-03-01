
import os
import pandas as pd
import matplotlib.pyplot as plt


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
OUT_DIR = os.path.join(BASE_DIR, "outputs")

FORECAST_FILE = os.path.join(OUT_DIR, "forecast_output.csv")
CAL_FILE = os.path.join(DATA_DIR, "festival_calender.csv")

OUT_CSV = os.path.join(OUT_DIR, "festival_adjusted_forecast.csv")
OUT_PNG = os.path.join(OUT_DIR, "festival_adjusted_forecast_plot.png")

os.makedirs(OUT_DIR, exist_ok=True)


if not os.path.exists(FORECAST_FILE):
    raise FileNotFoundError(f"Missing: {FORECAST_FILE} (Run Step 10/11 to generate forecast_output.csv)")

if not os.path.exists(CAL_FILE):
    raise FileNotFoundError(f"Missing: {CAL_FILE} (Create Data/festival_calendar.csv)")

forecast = pd.read_csv(FORECAST_FILE)
cal = pd.read_csv(CAL_FILE)


required_cols = {"Date", "Sales", "Predicted_Sales"}
missing = required_cols - set(forecast.columns)
if missing:
    raise ValueError(
        f"forecast_output.csv missing columns: {missing}\n"
        f"Found columns: {list(forecast.columns)}"
    )

cal_required = {"Festival", "StartDate", "EndDate", "Weight"}
cal_missing = cal_required - set(cal.columns)
if cal_missing:
    raise ValueError(
        f"festival_calendar.csv missing columns: {cal_missing}\n"
        f"Found columns: {list(cal.columns)}"
    )


forecast["Date"] = pd.to_datetime(forecast["Date"], errors="coerce")
if forecast["Date"].isna().any():
    bad = forecast[forecast["Date"].isna()].head(5)
    raise ValueError(f"Some Date values could not be parsed. Sample bad rows:\n{bad}")

cal["StartDate"] = pd.to_datetime(cal["StartDate"], errors="coerce")
cal["EndDate"] = pd.to_datetime(cal["EndDate"], errors="coerce")
if cal["StartDate"].isna().any() or cal["EndDate"].isna().any():
    bad = cal[cal["StartDate"].isna() | cal["EndDate"].isna()]
    raise ValueError(f"Some festival calendar dates could not be parsed:\n{bad}")


cal["Weight"] = pd.to_numeric(cal["Weight"], errors="coerce").fillna(0.0)


# FESTIVAL TAGGING (calendar layer)
# If multiple festivals overlap, keep the maximum Weight.
# -----------------------------
forecast["Festival"] = "None"
forecast["Festival_Weight"] = 0.0

for _, r in cal.iterrows():
    mask = (forecast["Date"] >= r["StartDate"]) & (forecast["Date"] <= r["EndDate"])
    higher = mask & (forecast["Festival_Weight"] < float(r["Weight"]))
    forecast.loc[higher, "Festival"] = str(r["Festival"])
    forecast.loc[higher, "Festival_Weight"] = float(r["Weight"])

# -----------------------------
# FESTIVAL-ADJUSTED FORECAST (simple & explainable)
# Adjusted_Forecast = Predicted_Sales * (1 + Festival_Weight)
# -----------------------------
forecast["Adjusted_Forecast"] = forecast["Predicted_Sales"] * (1 + forecast["Festival_Weight"])

# -----------------------------
# SAVE OUTPUT CSV
# -----------------------------
forecast.to_csv(OUT_CSV, index=False)
print(f"✅ Saved: {OUT_CSV}")


# VISUALIZATION (Aggregated daily totals)

daily = (
    forecast.groupby("Date")[["Sales", "Predicted_Sales", "Adjusted_Forecast"]]
    .sum()
    .reset_index()
    .sort_values("Date")
)

plt.figure(figsize=(10, 5))
plt.plot(daily["Date"], daily["Sales"], label="Actual Sales")
plt.plot(daily["Date"], daily["Predicted_Sales"], label="Baseline Forecast")
plt.plot(daily["Date"], daily["Adjusted_Forecast"], label="Festival-Adjusted Forecast")
plt.title("Baseline vs Festival-Adjusted Forecast (Daily Total)")
plt.xlabel("Date")
plt.ylabel("Sales")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(OUT_PNG, dpi=200)
plt.close()

print(f"✅ Saved: {OUT_PNG}")

# -----------------------------
# INVENTORY / DISCOUNT INSIGHTS 
# -----------------------------
def calendar_discount_rule(w: float) -> str:
   
    if w >= 0.06:
        return "NO_DISCOUNT (Festival High Demand)"
    elif w >= 0.03:
        return "OPTIONAL_DISCOUNT (Festival Medium Demand)"
    else:
        return "NORMAL_POLICY"

forecast["Calendar_Discount_Guidance"] = forecast["Festival_Weight"].apply(calendar_discount_rule)

festival_days = forecast[forecast["Festival"] != "None"][["Date", "Festival", "Festival_Weight"]].drop_duplicates()
high_days = festival_days[festival_days["Festival_Weight"] >= 0.06]

print("\n=== Step 12 Summary (PPT-ready) ===")
print(f"• Total unique dates analysed: {forecast['Date'].nunique()}")
print(f"• Festival-affected dates: {festival_days['Date'].nunique()}")

if len(high_days) > 0:
    print(f"• Stock-up recommended on {high_days['Date'].nunique()} high-impact festival dates (Weight ≥ 0.06)")
