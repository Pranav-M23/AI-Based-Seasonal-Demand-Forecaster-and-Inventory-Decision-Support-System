"""
ML Models for Seasonal Demand Forecaster
=========================================
Replaces rule-based logic with XGBoost + Random Forest models for:
  1. Demand Forecasting (XGBoost + RF ensemble)
  2. Festival Impact Prediction (XGBoost regressor)
  3. Discount Optimization (XGBoost classifier)
  4. Inventory Reorder Classification (RF + XGBoost)
  5. Stockout Risk Prediction (XGBoost binary classifier)
"""

import os
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBRegressor, XGBClassifier

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
OUT_DIR = os.path.join(BASE_DIR, "outputs")
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# ============================================================================
# 1. DEMAND FORECASTING — XGBoost + RF Ensemble
# ============================================================================

DEMAND_FEATURES = [
    "Store", "DayOfWeek", "Promo", "SchoolHoliday",
    "CompetitionDistance", "Promo2", "Year", "Month",
    "WeekOfYear", "StoreType_enc", "Assortment_enc"
]


def _prepare_demand_data():
    """Load and prepare training data from Rossmann dataset."""
    train = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
    store = pd.read_csv(os.path.join(DATA_DIR, "store.csv"))

    df = train.merge(store, on="Store", how="left")
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[df["Open"] == 1]
    df = df[df["Sales"] > 0]

    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["WeekOfYear"] = df["Date"].dt.isocalendar()["week"].astype(int)

    # Encode categorical features
    le_store_type = LabelEncoder()
    le_assortment = LabelEncoder()
    df["StoreType_enc"] = le_store_type.fit_transform(df["StoreType"].fillna("unknown"))
    df["Assortment_enc"] = le_assortment.fit_transform(df["Assortment"].fillna("unknown"))

    df = df.fillna(0)

    # Save encoders
    joblib.dump(le_store_type, os.path.join(MODEL_DIR, "le_store_type.pkl"))
    joblib.dump(le_assortment, os.path.join(MODEL_DIR, "le_assortment.pkl"))

    return df


def train_demand_models(force_retrain=False):
    """Train both RF and XGBoost demand models and return them."""
    rf_path = os.path.join(MODEL_DIR, "demand_rf.pkl")
    xgb_path = os.path.join(MODEL_DIR, "demand_xgb.pkl")

    if not force_retrain and os.path.exists(rf_path) and os.path.exists(xgb_path):
        print("  Loading cached demand models...")
        rf = joblib.load(rf_path)
        xgb = joblib.load(xgb_path)
        return rf, xgb

    print("  Preparing demand data...")
    df = _prepare_demand_data()

    X = df[DEMAND_FEATURES].copy()
    y = df["Sales"]

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.15, random_state=42)

    # Random Forest
    print("  Training Random Forest demand model...")
    rf = RandomForestRegressor(
        n_estimators=150, max_depth=18, min_samples_leaf=10,
        random_state=42, n_jobs=-1
    )
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_val)
    rf_mae = mean_absolute_error(y_val, rf_pred)
    rf_r2 = r2_score(y_val, rf_pred)
    print(f"    RF — MAE: {rf_mae:.1f}, R²: {rf_r2:.4f}")

    # XGBoost
    print("  Training XGBoost demand model...")
    xgb = XGBRegressor(
        n_estimators=300, max_depth=8, learning_rate=0.08,
        subsample=0.8, colsample_bytree=0.8,
        reg_alpha=0.1, reg_lambda=1.0,
        random_state=42, n_jobs=-1, tree_method="hist"
    )
    xgb.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    xgb_pred = xgb.predict(X_val)
    xgb_mae = mean_absolute_error(y_val, xgb_pred)
    xgb_r2 = r2_score(y_val, xgb_pred)
    print(f"    XGB — MAE: {xgb_mae:.1f}, R²: {xgb_r2:.4f}")

    # Ensemble validation
    ens_pred = 0.4 * rf_pred + 0.6 * xgb_pred
    ens_mae = mean_absolute_error(y_val, ens_pred)
    ens_r2 = r2_score(y_val, ens_pred)
    print(f"    Ensemble (0.4 RF + 0.6 XGB) — MAE: {ens_mae:.1f}, R²: {ens_r2:.4f}")

    joblib.dump(rf, rf_path)
    joblib.dump(xgb, xgb_path)
    print(f"  Saved demand models to {MODEL_DIR}/")

    return rf, xgb


def predict_demand(rf, xgb, X: pd.DataFrame, rf_weight=0.4) -> np.ndarray:
    """Ensemble prediction from RF + XGBoost."""
    rf_pred = rf.predict(X[DEMAND_FEATURES])
    xgb_pred = xgb.predict(X[DEMAND_FEATURES])
    return rf_weight * rf_pred + (1 - rf_weight) * xgb_pred


# ============================================================================
# 2. FESTIVAL IMPACT PREDICTION — XGBoost
# ============================================================================

def _build_festival_training_data():
    """
    Build training data for festival uplift model.
    Uses StateHoliday from train.csv as a proxy for festival periods.
    Computes uplift = holiday_avg_sales / normal_avg_sales per store/month.
    """
    train = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
    store_df = pd.read_csv(os.path.join(DATA_DIR, "store.csv"))

    df = train.merge(store_df, on="Store", how="left")
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[df["Open"] == 1].copy()
    df = df[df["Sales"] > 0].copy()

    df["Month"] = df["Date"].dt.month
    df["DayOfWeek"] = df["DayOfWeek"]

    # Mark holiday rows (StateHoliday != '0')
    df["IsHoliday"] = df["StateHoliday"].astype(str).apply(lambda x: 0 if x == "0" else 1)

    # Encode categoricals
    le_st = LabelEncoder()
    le_as = LabelEncoder()
    df["StoreType_enc"] = le_st.fit_transform(df["StoreType"].fillna("unknown"))
    df["Assortment_enc"] = le_as.fit_transform(df["Assortment"].fillna("unknown"))

    # Compute normal avg per store-month
    normal = df[df["IsHoliday"] == 0].groupby(["Store", "Month"])["Sales"].mean().rename("Normal_Avg")
    holiday = df[df["IsHoliday"] == 1].groupby(["Store", "Month"])["Sales"].mean().rename("Holiday_Avg")

    uplift_df = pd.DataFrame({"Normal_Avg": normal, "Holiday_Avg": holiday}).dropna()
    uplift_df["Uplift"] = (uplift_df["Holiday_Avg"] - uplift_df["Normal_Avg"]) / uplift_df["Normal_Avg"]
    uplift_df = uplift_df.reset_index()

    # Merge store features
    uplift_df = uplift_df.merge(
        store_df[["Store", "StoreType", "Assortment", "CompetitionDistance", "Promo2"]],
        on="Store", how="left"
    )
    uplift_df["StoreType_enc"] = le_st.transform(uplift_df["StoreType"].fillna("unknown"))
    uplift_df["Assortment_enc"] = le_as.transform(uplift_df["Assortment"].fillna("unknown"))
    uplift_df = uplift_df.fillna(0)

    # Clip extreme outliers
    uplift_df["Uplift"] = uplift_df["Uplift"].clip(-0.5, 1.0)

    return uplift_df


def train_festival_impact_model(force_retrain=False):
    """Train XGBoost model to predict festival demand uplift."""
    model_path = os.path.join(MODEL_DIR, "festival_uplift_xgb.pkl")

    if not force_retrain and os.path.exists(model_path):
        print("  Loading cached festival impact model...")
        return joblib.load(model_path)

    print("  Building festival training data...")
    df = _build_festival_training_data()

    features = ["Store", "Month", "StoreType_enc", "Assortment_enc", "CompetitionDistance", "Promo2"]
    X = df[features]
    y = df["Uplift"]

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    print("  Training XGBoost festival uplift model...")
    model = XGBRegressor(
        n_estimators=200, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        random_state=42, n_jobs=-1, tree_method="hist"
    )
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

    pred = model.predict(X_val)
    mae = mean_absolute_error(y_val, pred)
    r2 = r2_score(y_val, pred)
    print(f"    Festival Uplift XGB — MAE: {mae:.4f}, R²: {r2:.4f}")

    joblib.dump(model, model_path)
    return model


# ============================================================================
# 3. DISCOUNT OPTIMIZATION — XGBoost Classifier
# ============================================================================

DISCOUNT_TIERS = ["NO_DISCOUNT", "SMALL_5", "MEDIUM_10", "HIGH_15", "CLEARANCE_20"]


def _build_discount_training_data():
    """
    Build training data for discount classification.
    Uses historical promo/holiday patterns to assign discount labels.
    """
    train = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
    store_df = pd.read_csv(os.path.join(DATA_DIR, "store.csv"))
    sr = pd.read_csv(os.path.join(DATA_DIR, "store_region.csv"))

    df = train.merge(store_df, on="Store", how="left")
    df = df.merge(sr, on="Store", how="left")
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[df["Open"] == 1].copy()
    df = df[df["Sales"] > 0].copy()

    df["Month"] = df["Date"].dt.month
    df["IsHoliday"] = df["StateHoliday"].astype(str).apply(lambda x: 0 if x == "0" else 1)

    # Compute store-month aggregates
    agg = df.groupby(["Store", "Month", "Region"]).agg(
        Avg_Sales=("Sales", "mean"),
        Std_Sales=("Sales", "std"),
        Avg_Customers=("Customers", "mean"),
        Promo_Ratio=("Promo", "mean"),
        Holiday_Ratio=("IsHoliday", "mean"),
    ).reset_index()
    agg = agg.fillna(0)

    # Merge store features
    agg = agg.merge(
        store_df[["Store", "StoreType", "Assortment", "CompetitionDistance", "Promo2"]],
        on="Store", how="left"
    )

    le_st = LabelEncoder()
    le_as = LabelEncoder()
    le_rg = LabelEncoder()
    agg["StoreType_enc"] = le_st.fit_transform(agg["StoreType"].fillna("unknown"))
    agg["Assortment_enc"] = le_as.fit_transform(agg["Assortment"].fillna("unknown"))
    agg["Region_enc"] = le_rg.fit_transform(agg["Region"].fillna("Pan-India"))
    agg = agg.fillna(0)

    joblib.dump(le_rg, os.path.join(MODEL_DIR, "le_region_discount.pkl"))

    # Generate labels based on demand patterns:
    # High demand (holidays + high sales) → NO_DISCOUNT
    # Low demand (low sales, no promos) → CLEARANCE_20
    agg["Demand_Score"] = (
        agg["Avg_Sales"] / agg["Avg_Sales"].quantile(0.75) * 0.4 +
        agg["Holiday_Ratio"] * 0.3 +
        agg["Avg_Customers"] / agg["Avg_Customers"].quantile(0.75) * 0.3
    )

    conditions = [
        agg["Demand_Score"] >= 0.80,
        agg["Demand_Score"] >= 0.60,
        agg["Demand_Score"] >= 0.40,
        agg["Demand_Score"] >= 0.20,
    ]
    choices = ["NO_DISCOUNT", "SMALL_5", "MEDIUM_10", "HIGH_15"]
    agg["Discount_Tier"] = np.select(conditions, choices, default="CLEARANCE_20")

    return agg


def train_discount_model(force_retrain=False):
    """Train XGBoost classifier for discount tier prediction."""
    model_path = os.path.join(MODEL_DIR, "discount_xgb.pkl")
    le_path = os.path.join(MODEL_DIR, "le_discount_tier.pkl")

    if not force_retrain and os.path.exists(model_path):
        print("  Loading cached discount model...")
        return joblib.load(model_path), joblib.load(le_path)

    print("  Building discount training data...")
    df = _build_discount_training_data()

    features = [
        "Store", "Month", "Avg_Sales", "Std_Sales", "Avg_Customers",
        "Promo_Ratio", "Holiday_Ratio", "StoreType_enc", "Assortment_enc",
        "Region_enc", "CompetitionDistance", "Promo2"
    ]

    X = df[features].copy()
    le_tier = LabelEncoder()
    y = le_tier.fit_transform(df["Discount_Tier"])

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    print("  Training XGBoost discount classifier...")
    model = XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.08,
        subsample=0.8, colsample_bytree=0.8,
        random_state=42, n_jobs=-1, tree_method="hist",
        use_label_encoder=False, eval_metric="mlogloss"
    )
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

    pred = model.predict(X_val)
    acc = accuracy_score(y_val, pred)
    print(f"    Discount XGB — Accuracy: {acc:.4f}")
    print(f"    Classes: {le_tier.classes_}")

    joblib.dump(model, model_path)
    joblib.dump(le_tier, le_path)
    return model, le_tier


# ============================================================================
# 4. INVENTORY REORDER CLASSIFICATION — RF + XGBoost
# ============================================================================

INVENTORY_ACTIONS = ["OK", "MONITOR", "WATCHLIST", "REORDER SOON", "REORDER NOW"]


def _build_inventory_training_data(n_samples=50000):
    """
    Generate synthetic training data for inventory classification.
    Uses realistic distributions based on the project's inventory KPI logic.
    """
    rng = np.random.default_rng(42)

    records = []
    for _ in range(n_samples):
        avg_daily_demand = rng.uniform(50, 2000)
        std_daily_demand = avg_daily_demand * rng.uniform(0.1, 0.5)
        lead_time = 7
        z = 1.65
        safety_stock = z * std_daily_demand * np.sqrt(lead_time)
        reorder_point = avg_daily_demand * lead_time + safety_stock

        # Simulate inventory at various levels
        inv_ratio = rng.choice(
            [rng.uniform(0.1, 0.5), rng.uniform(0.5, 0.7),
             rng.uniform(0.7, 0.85), rng.uniform(0.85, 1.2),
             rng.uniform(1.2, 2.5)],
            p=[0.15, 0.15, 0.20, 0.25, 0.25]
        )
        current_inventory = reorder_point * inv_ratio
        days_of_supply = current_inventory / avg_daily_demand if avg_daily_demand > 0 else 999

        festival_upcoming = rng.choice([0, 1], p=[0.8, 0.2])
        month = rng.integers(1, 13)
        region_enc = rng.integers(0, 6)
        category_enc = rng.integers(0, 10)

        # Assign labels (ground truth): modified thresholds accounting for festival
        inv_pos = current_inventory / reorder_point
        if festival_upcoming:
            # During festivals, be more aggressive with reordering
            if inv_pos >= 1.5:
                action = "OK"
            elif inv_pos >= 1.0:
                action = "MONITOR"
            elif inv_pos >= 0.8:
                action = "WATCHLIST"
            elif inv_pos >= 0.6:
                action = "REORDER SOON"
            else:
                action = "REORDER NOW"
        else:
            if inv_pos >= 1.2:
                action = "OK"
            elif inv_pos >= 0.85:
                action = "MONITOR"
            elif inv_pos >= 0.70:
                action = "WATCHLIST"
            elif inv_pos >= 0.50:
                action = "REORDER SOON"
            else:
                action = "REORDER NOW"

        records.append({
            "Avg_Daily_Demand": avg_daily_demand,
            "Std_Daily_Demand": std_daily_demand,
            "Current_Inventory": current_inventory,
            "Reorder_Point": reorder_point,
            "Safety_Stock": safety_stock,
            "Days_Of_Supply": days_of_supply,
            "Inventory_Position": inv_pos,
            "Festival_Upcoming": festival_upcoming,
            "Month": month,
            "Region_enc": region_enc,
            "Category_enc": category_enc,
            "Action": action,
        })

    return pd.DataFrame(records)


def train_inventory_models(force_retrain=False):
    """Train RF classifier + XGBoost priority scorer for inventory decisions."""
    clf_path = os.path.join(MODEL_DIR, "inventory_rf.pkl")
    xgb_path = os.path.join(MODEL_DIR, "inventory_priority_xgb.pkl")
    le_path = os.path.join(MODEL_DIR, "le_inventory_action.pkl")

    if not force_retrain and os.path.exists(clf_path) and os.path.exists(xgb_path):
        print("  Loading cached inventory models...")
        return joblib.load(clf_path), joblib.load(xgb_path), joblib.load(le_path)

    print("  Generating inventory training data...")
    df = _build_inventory_training_data(n_samples=60000)

    features = [
        "Avg_Daily_Demand", "Std_Daily_Demand", "Current_Inventory",
        "Reorder_Point", "Safety_Stock", "Days_Of_Supply",
        "Inventory_Position", "Festival_Upcoming", "Month",
        "Region_enc", "Category_enc"
    ]

    X = df[features]
    le_action = LabelEncoder()
    y = le_action.fit_transform(df["Action"])

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    # RF Classifier for action tier
    print("  Training RF inventory classifier...")
    clf = RandomForestClassifier(
        n_estimators=150, max_depth=15, min_samples_leaf=5,
        random_state=42, n_jobs=-1
    )
    clf.fit(X_train, y_train)
    clf_pred = clf.predict(X_val)
    acc = accuracy_score(y_val, clf_pred)
    print(f"    Inventory RF — Accuracy: {acc:.4f}")

    # XGBoost for priority score (regression)
    # Generate priority scores as target
    df["Priority_Score"] = np.clip(
        100 * (1 - df["Inventory_Position"]) + 20 * (1 / (df["Days_Of_Supply"] + 0.1)),
        0, 100
    )
    y_priority = df["Priority_Score"]
    Xp_train, Xp_val, yp_train, yp_val = train_test_split(X, y_priority, test_size=0.2, random_state=42)

    print("  Training XGBoost priority scorer...")
    xgb_priority = XGBRegressor(
        n_estimators=200, max_depth=6, learning_rate=0.08,
        random_state=42, n_jobs=-1, tree_method="hist"
    )
    xgb_priority.fit(Xp_train, yp_train, eval_set=[(Xp_val, yp_val)], verbose=False)
    pp = xgb_priority.predict(Xp_val)
    p_mae = mean_absolute_error(yp_val, pp)
    p_r2 = r2_score(yp_val, pp)
    print(f"    Priority XGB — MAE: {p_mae:.2f}, R²: {p_r2:.4f}")

    joblib.dump(clf, clf_path)
    joblib.dump(xgb_priority, xgb_path)
    joblib.dump(le_action, le_path)
    return clf, xgb_priority, le_action


# ============================================================================
# 5. STOCKOUT RISK PREDICTION — XGBoost Binary Classifier
# ============================================================================

def _build_stockout_training_data(n_samples=50000):
    """Generate synthetic data for stockout risk binary classification."""
    rng = np.random.default_rng(123)

    records = []
    for _ in range(n_samples):
        avg_daily_demand = rng.uniform(50, 2000)
        demand_volatility = rng.uniform(0.1, 0.6)
        std_daily_demand = avg_daily_demand * demand_volatility
        lead_time = 7
        current_inv = rng.uniform(0, avg_daily_demand * 30)
        days_of_supply = current_inv / avg_daily_demand if avg_daily_demand > 0 else 999
        festival_in_7d = rng.choice([0, 1], p=[0.85, 0.15])
        month = rng.integers(1, 13)
        region_enc = rng.integers(0, 6)
        category_enc = rng.integers(0, 10)
        days_since_reorder = rng.integers(0, 30)

        # Stockout in next 7 days? Probability-based labeling
        expected_demand_7d = avg_daily_demand * 7 * (1.3 if festival_in_7d else 1.0)
        noise = rng.normal(0, std_daily_demand * np.sqrt(7))
        actual_demand_7d = expected_demand_7d + noise
        stockout = 1 if current_inv < actual_demand_7d else 0

        records.append({
            "Current_Inventory": current_inv,
            "Avg_Daily_Demand": avg_daily_demand,
            "Demand_Volatility": demand_volatility,
            "Days_Of_Supply": days_of_supply,
            "Lead_Time": lead_time,
            "Days_Since_Reorder": days_since_reorder,
            "Festival_In_7d": festival_in_7d,
            "Month": month,
            "Region_enc": region_enc,
            "Category_enc": category_enc,
            "Stockout_7d": stockout,
        })

    return pd.DataFrame(records)


def train_stockout_model(force_retrain=False):
    """Train XGBoost binary classifier for 7-day stockout prediction."""
    model_path = os.path.join(MODEL_DIR, "stockout_xgb.pkl")

    if not force_retrain and os.path.exists(model_path):
        print("  Loading cached stockout model...")
        return joblib.load(model_path)

    print("  Generating stockout training data...")
    df = _build_stockout_training_data(n_samples=60000)

    features = [
        "Current_Inventory", "Avg_Daily_Demand", "Demand_Volatility",
        "Days_Of_Supply", "Lead_Time", "Days_Since_Reorder",
        "Festival_In_7d", "Month", "Region_enc", "Category_enc"
    ]

    X = df[features]
    y = df["Stockout_7d"]

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    print("  Training XGBoost stockout classifier...")
    model = XGBClassifier(
        n_estimators=250, max_depth=7, learning_rate=0.08,
        subsample=0.8, colsample_bytree=0.8, scale_pos_weight=1.5,
        random_state=42, n_jobs=-1, tree_method="hist",
        use_label_encoder=False, eval_metric="logloss"
    )
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

    pred = model.predict(X_val)
    prob = model.predict_proba(X_val)[:, 1]
    acc = accuracy_score(y_val, pred)
    print(f"    Stockout XGB — Accuracy: {acc:.4f}")
    print(f"    Positive rate (actual): {y_val.mean():.3f}")
    print(f"    Positive rate (pred):   {pred.mean():.3f}")

    joblib.dump(model, model_path)
    return model


# ============================================================================
# MASTER TRAINING FUNCTION
# ============================================================================

def train_all_models(force_retrain=False):
    """Train all 5 ML models."""
    print("=" * 70)
    print("TRAINING ALL ML MODELS")
    print("=" * 70)

    print("\n[1/5] Demand Forecasting (RF + XGBoost Ensemble)")
    rf_demand, xgb_demand = train_demand_models(force_retrain)

    print("\n[2/5] Festival Impact Prediction (XGBoost)")
    festival_model = train_festival_impact_model(force_retrain)

    print("\n[3/5] Discount Optimization (XGBoost Classifier)")
    discount_model, discount_le = train_discount_model(force_retrain)

    print("\n[4/5] Inventory Reorder Classification (RF + XGBoost)")
    inv_clf, inv_priority, inv_le = train_inventory_models(force_retrain)

    print("\n[5/5] Stockout Risk Prediction (XGBoost)")
    stockout_model = train_stockout_model(force_retrain)

    print("\n" + "=" * 70)
    print("ALL MODELS TRAINED SUCCESSFULLY")
    print("=" * 70)

    return {
        "demand_rf": rf_demand,
        "demand_xgb": xgb_demand,
        "festival_uplift": festival_model,
        "discount_clf": discount_model,
        "discount_le": discount_le,
        "inventory_clf": inv_clf,
        "inventory_priority": inv_priority,
        "inventory_le": inv_le,
        "stockout_clf": stockout_model,
    }


if __name__ == "__main__":
    train_all_models(force_retrain=True)
