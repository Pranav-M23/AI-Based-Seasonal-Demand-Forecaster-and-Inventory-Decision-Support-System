import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error,r2_score
import numpy as np

# Load datasets
train = pd.read_csv("Data/train.csv")
store = pd.read_csv("Data/store.csv")

#print(train.shape)
#print(store.shape)

#print(train.head())
#print(store.head())
#df = pd.merge(train, store, on="Store", how="left")
#print(df.shape)
#df['Date'] = pd.to_datetime(df['Date'])

#df['Month'] = df['Date'].dt.month
#df['Week'] = df['Date'].dt.isocalendar().week
#df['DayOfWeek'] = df['Date'].dt.dayofweek

#sns.boxplot(x="Promo", y="Sales", data=df)
#plt.title("Sales with and without Promotion")
#plt.show()

df = train.merge(store, on="Store", how="left")

# -----------------------------
# BASIC CLEANING
# -----------------------------
df["Date"] = pd.to_datetime(df["Date"])
df = df[df["Open"] == 1]          # only open stores
df = df[df["Sales"] > 0]          # valid sales

# -----------------------------
# FEATURE ENGINEERING
# -----------------------------
df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month
df["Day"] = df["Date"].dt.day
df["WeekOfYear"] = df["Date"].dt.isocalendar()["week"]

# Select core features
features = [
    "Store", "DayOfWeek", "Promo",
    "SchoolHoliday", "CompetitionDistance",
    "Promo2", "Year", "Month", "WeekOfYear"
]

df_model = df[features + ["Sales"]]

print("Prepared dataset shape:", df_model.shape)
print(df_model.head())
df_model = df_model.fillna(0)

# -----------------------------
# SPLIT FEATURES & TARGET
# -----------------------------
X = df_model.drop("Sales", axis=1)
y = df_model["Sales"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("Train size:", X_train.shape)
print("Test size:", X_test.shape)

# -----------------------------
# TRAIN BASELINE MODEL
# -----------------------------
rf = RandomForestRegressor(
    n_estimators=100,
    max_depth=15,
    random_state=42,
    n_jobs=-1
)

rf.fit(X_train, y_train)

# -----------------------------
# EVALUATION
# -----------------------------
y_pred = rf.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print("\nBaseline Model Performance:")
print("MAE :", round(mae, 2))
print("RMSE:", round(rmse, 2))

r2 = r2_score(y_test, y_pred)
y_test_safe = y_test.replace(0, np.nan)
mape = np.mean(np.abs((y_test_safe - y_pred) / y_test_safe)) * 100

print("\nAdditional Metrics:")
print("R2 Score:", round(r2, 4))
print("MAPE (%):", round(mape, 2))