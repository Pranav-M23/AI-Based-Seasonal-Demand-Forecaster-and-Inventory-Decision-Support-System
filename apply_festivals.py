import os
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
OUT_DIR = os.path.join(BASE_DIR, "outputs")

FORECAST_FILE = os.path.join(OUT_DIR, "yearly_baseline_forecast.csv")
CAL_FILE = os.path.join(DATA_DIR, "festival_calender.csv")

OUT_CSV = os.path.join(OUT_DIR, "yearly_festival_adjusted_forecast.csv")
OUT_PNG = os.path.join(OUT_DIR, "yearly_festival_adjusted_plot.png")
OUT_BAR = os.path.join(OUT_DIR, "festival_days_bar.png")

if not os.path.exists(FORECAST_FILE):
    raise FileNotFoundError(f"Missing {FORECAST_FILE}. Run step12_year_forecast.py first.")

if not os.path.exists(CAL_FILE):
    raise FileNotFoundError(f"Missing {CAL_FILE}. Create Data/festival_calendar.csv.")

forecast = pd.read_csv(FORECAST_FILE)
cal = pd.read_csv(CAL_FILE)

forecast["Date"] = pd.to_datetime(forecast["Date"])
cal["StartDate"] = pd.to_datetime(cal["StartDate"])
cal["EndDate"] = pd.to_datetime(cal["EndDate"])
cal["Weight"] = pd.to_numeric(cal["Weight"], errors="coerce").fillna(0.0)

forecast["Festival"] = "None"
forecast["Festival_Weight"] = 0.0

# Tag festivals (keep max weight if overlap)
for _, r in cal.iterrows():
    mask = (forecast["Date"] >= r["StartDate"]) & (forecast["Date"] <= r["EndDate"])
    higher = mask & (forecast["Festival_Weight"] < float(r["Weight"]))
    forecast.loc[higher, "Festival"] = str(r["Festival"])
    forecast.loc[higher, "Festival_Weight"] = float(r["Weight"])

# Adjusted forecast
forecast["Adjusted_Forecast"] = forecast["Baseline_Forecast"] * (1 + forecast["Festival_Weight"])

# Save output CSV
forecast.to_csv(OUT_CSV, index=False)
print(f"✅ Saved: {OUT_CSV}")

# Daily totals for plotting
daily = forecast.groupby("Date")[["Baseline_Forecast", "Adjusted_Forecast"]].sum().reset_index()

plt.figure(figsize=(12, 5))
plt.plot(daily["Date"], daily["Baseline_Forecast"], label="Baseline Forecast")
plt.plot(daily["Date"], daily["Adjusted_Forecast"], label="Festival-Adjusted Forecast")
plt.title("Baseline vs Festival-Adjusted Forecast (Full Year Planning)")
plt.xlabel("Date")
plt.ylabel("Sales (Aggregated)")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(OUT_PNG, dpi=200)
plt.close()
print(f"✅ Saved: {OUT_PNG}")

# Bar chart: number of festival-affected days
festival_days = forecast[forecast["Festival"] != "None"][["Date", "Festival"]].drop_duplicates()
counts = festival_days["Festival"].value_counts().sort_values(ascending=False)

plt.figure(figsize=(10, 4))
plt.bar(counts.index.astype(str), counts.values)
plt.title("Festival Coverage (Number of Days Tagged)")
plt.xlabel("Festival")
plt.ylabel("Tagged Days")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(OUT_BAR, dpi=200)
plt.close()
print(f"Saved: {OUT_BAR}")



print("• Planning horizon dates:", forecast["Date"].nunique())
print("• Stores covered:", forecast["Store"].nunique() if "Store" in forecast.columns else "N/A")
print("• Festival-affected dates:", festival_days["Date"].nunique())
if len(counts) > 0:
    print("• Festivals integrated:", ", ".join(counts.index.astype(str).tolist()))
else:
    print("• No festivals overlapped the planning year — check festival_calendar.csv year matches PLANNING_YEAR.")
