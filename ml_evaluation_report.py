"""
ML Evaluation Report Generator
================================
Generates comprehensive evaluation metrics, plots, and a JSON report for all
5 ML models in the Seasonal Demand Forecaster project.

Run:
    python ml_evaluation_report.py

Outputs (saved to outputs/evaluation/):
    - metrics_report.json          — machine-readable metrics for all models
    - 01_demand_comparison.png     — RF vs XGBoost vs Ensemble bar chart
    - 02_demand_scatter.png        — Actual vs Predicted scatter
    - 03_demand_feature_importance.png
    - 04_festival_predictions.png  — Uplift: actual vs predicted
    - 05_discount_confusion.png    — Confusion matrix
    - 06_discount_feature_importance.png
    - 07_inventory_confusion.png   — Confusion matrix
    - 08_inventory_feature_importance.png
    - 09_stockout_confusion.png    — Confusion matrix
    - 10_stockout_roc.png          — ROC curve
    - 11_model_summary.png         — All-model metric comparison
"""

import os
import sys
import json
import warnings
warnings.filterwarnings("ignore")

# Ensure UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # headless — no display needed
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, f1_score, precision_score, recall_score,
    confusion_matrix, classification_report,
    roc_curve, auc
)
from sklearn.preprocessing import LabelEncoder

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, "Data")
MODEL_DIR = os.path.join(BASE_DIR, "models")
EVAL_DIR  = os.path.join(BASE_DIR, "outputs", "evaluation")
os.makedirs(EVAL_DIR, exist_ok=True)

# ── styling ───────────────────────────────────────────────────────────────────
PALETTE    = ["#2196F3", "#FF9800", "#4CAF50", "#E91E63", "#9C27B0"]
TITLE_FONT = {"fontsize": 14, "fontweight": "bold"}
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({"figure.dpi": 120, "axes.titlesize": 13})

# ── helpers ───────────────────────────────────────────────────────────────────
def rmse(y_true, y_pred):
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))

def save(fig, name):
    path = os.path.join(EVAL_DIR, name)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"   Saved → {path}")

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ==============================================================================
# 1. DEMAND FORECASTING — RF vs XGBoost vs Ensemble
# ==============================================================================
def evaluate_demand():
    section("1 / 5  DEMAND FORECASTING")
    print("  Loading Rossmann dataset …")

    train = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
    store = pd.read_csv(os.path.join(DATA_DIR, "store.csv"))

    df = train.merge(store, on="Store", how="left")
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[(df["Open"] == 1) & (df["Sales"] > 0)].copy()
    df["Year"]      = df["Date"].dt.year
    df["Month"]     = df["Date"].dt.month
    df["WeekOfYear"]= df["Date"].dt.isocalendar()["week"].astype(int)

    le_st = joblib.load(os.path.join(MODEL_DIR, "le_store_type.pkl"))
    le_as = joblib.load(os.path.join(MODEL_DIR, "le_assortment.pkl"))
    df["StoreType_enc"]  = le_st.transform(df["StoreType"].fillna("unknown"))
    df["Assortment_enc"] = le_as.transform(df["Assortment"].fillna("unknown"))
    df = df.fillna(0)

    FEATURES = [
        "Store","DayOfWeek","Promo","SchoolHoliday","CompetitionDistance",
        "Promo2","Year","Month","WeekOfYear","StoreType_enc","Assortment_enc"
    ]
    X = df[FEATURES]
    y = df["Sales"]

    # Use same random_state as training → reproducible test split
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    print(f"  Test set: {len(X_test):,} rows")

    rf  = joblib.load(os.path.join(MODEL_DIR, "demand_rf.pkl"))
    xgb = joblib.load(os.path.join(MODEL_DIR, "demand_xgb.pkl"))

    rf_pred  = rf.predict(X_test)
    xgb_pred = xgb.predict(X_test)
    ens_pred = 0.4 * rf_pred + 0.6 * xgb_pred

    metrics = {
        "RandomForest": {
            "MAE":  float(mean_absolute_error(y_test, rf_pred)),
            "RMSE": rmse(y_test, rf_pred),
            "R2":   float(r2_score(y_test, rf_pred)),
        },
        "XGBoost": {
            "MAE":  float(mean_absolute_error(y_test, xgb_pred)),
            "RMSE": rmse(y_test, xgb_pred),
            "R2":   float(r2_score(y_test, xgb_pred)),
        },
        "Ensemble_RF40_XGB60": {
            "MAE":  float(mean_absolute_error(y_test, ens_pred)),
            "RMSE": rmse(y_test, ens_pred),
            "R2":   float(r2_score(y_test, ens_pred)),
        },
    }
    for m, v in metrics.items():
        print(f"  {m:30s}  MAE={v['MAE']:.0f}  RMSE={v['RMSE']:.0f}  R²={v['R2']:.4f}")

    # ── Plot 1: metric comparison bar chart ──────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    models  = list(metrics.keys())
    labels  = ["Random\nForest", "XGBoost", "Ensemble\n(40/60)"]
    colors  = [PALETTE[0], PALETTE[1], PALETTE[2]]

    for ax, metric in zip(axes, ["MAE", "RMSE", "R2"]):
        vals = [metrics[m][metric] for m in models]
        bars = ax.bar(labels, vals, color=colors, width=0.5, edgecolor="white", linewidth=1.2)
        ax.set_title(metric, **TITLE_FONT)
        ax.set_ylabel(metric)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(vals)*0.01,
                    f"{v:.3f}" if metric == "R2" else f"{v:,.0f}",
                    ha="center", va="bottom", fontsize=9, fontweight="bold")

    fig.suptitle("Demand Forecasting — Model Comparison (Test Set)", **TITLE_FONT, y=1.02)
    plt.tight_layout()
    save(fig, "01_demand_comparison.png")

    # ── Plot 2: Actual vs Predicted scatter (sample 3000 pts) ───────────────
    idx   = np.random.default_rng(0).choice(len(y_test), size=3000, replace=False)
    y_s   = np.array(y_test)[idx]
    xgb_s = xgb_pred[idx]
    ens_s = ens_pred[idx]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    for ax, pred, label, color in [
        (ax1, xgb_s, "XGBoost", PALETTE[1]),
        (ax2, ens_s, "Ensemble", PALETTE[2]),
    ]:
        ax.scatter(y_s, pred, alpha=0.3, s=8, color=color)
        lo, hi = min(y_s.min(), pred.min()), max(y_s.max(), pred.max())
        ax.plot([lo, hi], [lo, hi], "r--", lw=1.5, label="Perfect prediction")
        ax.set_xlabel("Actual Sales", fontsize=11)
        ax.set_ylabel("Predicted Sales", fontsize=11)
        ax.set_title(f"{label} — Actual vs Predicted", **TITLE_FONT)
        r2 = r2_score(y_s, pred)
        ax.text(0.05, 0.92, f"R² = {r2:.4f}", transform=ax.transAxes,
                fontsize=11, color="black",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow"))
        ax.legend(fontsize=9)

    plt.tight_layout()
    save(fig, "02_demand_scatter.png")

    # ── Plot 3: Feature Importance (XGBoost) ─────────────────────────────────
    importances = pd.Series(xgb.feature_importances_, index=FEATURES).sort_values()
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(importances.index, importances.values,
                   color=[PALETTE[1] if v > importances.median() else "#90CAF9"
                          for v in importances.values])
    ax.set_title("Demand Forecasting — XGBoost Feature Importance", **TITLE_FONT)
    ax.set_xlabel("Importance Score")
    for bar, v in zip(bars, importances.values):
        ax.text(v + 0.002, bar.get_y() + bar.get_height()/2,
                f"{v:.3f}", va="center", fontsize=8)
    plt.tight_layout()
    save(fig, "03_demand_feature_importance.png")

    return metrics


# ==============================================================================
# 2. FESTIVAL IMPACT — XGBoost Regressor
# ==============================================================================
def evaluate_festival():
    section("2 / 5  FESTIVAL IMPACT")

    train_df = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
    store_df = pd.read_csv(os.path.join(DATA_DIR, "store.csv"))
    df = train_df.merge(store_df, on="Store", how="left")
    df["Date"]      = pd.to_datetime(df["Date"])
    df = df[(df["Open"] == 1) & (df["Sales"] > 0)].copy()
    df["Month"]     = df["Date"].dt.month
    df["IsHoliday"] = df["StateHoliday"].astype(str).apply(lambda x: 0 if x == "0" else 1)

    le_st = LabelEncoder(); le_as = LabelEncoder()
    df["StoreType_enc"]  = le_st.fit_transform(df["StoreType"].fillna("unknown"))
    df["Assortment_enc"] = le_as.fit_transform(df["Assortment"].fillna("unknown"))

    normal  = df[df["IsHoliday"]==0].groupby(["Store","Month"])["Sales"].mean().rename("Normal_Avg")
    holiday = df[df["IsHoliday"]==1].groupby(["Store","Month"])["Sales"].mean().rename("Holiday_Avg")
    uplift  = pd.DataFrame({"Normal_Avg":normal,"Holiday_Avg":holiday}).dropna()
    uplift["Uplift"] = ((uplift["Holiday_Avg"] - uplift["Normal_Avg"]) / uplift["Normal_Avg"]).clip(-0.5,1.0)
    uplift  = uplift.reset_index()

    uplift = uplift.merge(
        store_df[["Store","StoreType","Assortment","CompetitionDistance","Promo2"]],
        on="Store", how="left"
    ).fillna(0)
    uplift["StoreType_enc"]  = le_st.fit_transform(uplift["StoreType"].fillna("unknown"))
    uplift["Assortment_enc"] = le_as.fit_transform(uplift["Assortment"].fillna("unknown"))

    FEATURES = ["Store","Month","StoreType_enc","Assortment_enc","CompetitionDistance","Promo2"]
    X = uplift[FEATURES]; y = uplift["Uplift"]
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = joblib.load(os.path.join(MODEL_DIR, "festival_uplift_xgb.pkl"))
    pred  = model.predict(X_test)

    metrics = {
        "Festival_XGBoost": {
            "MAE":  float(mean_absolute_error(y_test, pred)),
            "RMSE": rmse(y_test, pred),
            "R2":   float(r2_score(y_test, pred)),
        }
    }
    v = metrics["Festival_XGBoost"]
    print(f"  Festival XGBoost  MAE={v['MAE']:.4f}  RMSE={v['RMSE']:.4f}  R²={v['R2']:.4f}")

    # ── Plot 4: Predicted uplift vs actual ───────────────────────────────────
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    ax1.scatter(y_test, pred, alpha=0.4, s=12, color=PALETTE[3])
    lo, hi = -0.55, 1.05
    ax1.plot([lo,hi],[lo,hi],"r--",lw=1.5, label="Perfect prediction")
    ax1.set_xlabel("Actual Uplift", fontsize=11)
    ax1.set_ylabel("Predicted Uplift", fontsize=11)
    ax1.set_title("Festival Uplift — Actual vs Predicted", **TITLE_FONT)
    ax1.text(0.05, 0.92, f"R² = {v['R2']:.4f}", transform=ax1.transAxes,
             fontsize=11, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow"))
    ax1.legend(fontsize=9)

    # Monthly uplift pattern
    uplift["Predicted"] = model.predict(uplift[FEATURES])
    monthly = uplift.groupby("Month")[["Uplift","Predicted"]].mean()
    ax2.plot(monthly.index, monthly["Uplift"],    "o-", color=PALETTE[3], lw=2, label="Actual Uplift")
    ax2.plot(monthly.index, monthly["Predicted"], "s--",color=PALETTE[1], lw=2, label="Predicted Uplift")
    ax2.set_xlabel("Month"); ax2.set_ylabel("Festival Uplift (fraction)")
    ax2.set_title("Average Festival Uplift by Month", **TITLE_FONT)
    ax2.set_xticks(range(1,13))
    ax2.set_xticklabels(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])
    ax2.legend(); ax2.grid(True, alpha=0.4)
    plt.tight_layout()
    save(fig, "04_festival_predictions.png")

    return metrics


# ==============================================================================
# 3. DISCOUNT CLASSIFIER — XGBoost
# ==============================================================================
def evaluate_discount():
    section("3 / 5  DISCOUNT OPTIMIZATION")

    train_df = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
    store_df = pd.read_csv(os.path.join(DATA_DIR, "store.csv"))
    sr       = pd.read_csv(os.path.join(DATA_DIR, "store_region.csv"))

    df = train_df.merge(store_df, on="Store", how="left").merge(sr, on="Store", how="left")
    df["Date"]      = pd.to_datetime(df["Date"])
    df = df[(df["Open"]==1) & (df["Sales"]>0)].copy()
    df["Month"]     = df["Date"].dt.month
    df["IsHoliday"] = df["StateHoliday"].astype(str).apply(lambda x: 0 if x=="0" else 1)

    agg = df.groupby(["Store","Month","Region"]).agg(
        Avg_Sales=("Sales","mean"), Std_Sales=("Sales","std"),
        Avg_Customers=("Customers","mean"), Promo_Ratio=("Promo","mean"),
        Holiday_Ratio=("IsHoliday","mean"),
    ).reset_index().fillna(0)

    agg = agg.merge(
        store_df[["Store","StoreType","Assortment","CompetitionDistance","Promo2"]],
        on="Store", how="left"
    )
    le_st = LabelEncoder(); le_as = LabelEncoder(); le_rg = LabelEncoder()
    agg["StoreType_enc"]  = le_st.fit_transform(agg["StoreType"].fillna("unknown"))
    agg["Assortment_enc"] = le_as.fit_transform(agg["Assortment"].fillna("unknown"))
    agg["Region_enc"]     = le_rg.fit_transform(agg["Region"].fillna("Pan-India"))
    agg = agg.fillna(0)

    agg["Demand_Score"] = (
        agg["Avg_Sales"] / agg["Avg_Sales"].quantile(0.75) * 0.4 +
        agg["Holiday_Ratio"] * 0.3 +
        agg["Avg_Customers"] / agg["Avg_Customers"].quantile(0.75) * 0.3
    )
    conditions = [agg["Demand_Score"]>=0.80, agg["Demand_Score"]>=0.60,
                  agg["Demand_Score"]>=0.40, agg["Demand_Score"]>=0.20]
    choices    = ["NO_DISCOUNT","SMALL_5","MEDIUM_10","HIGH_15"]
    agg["Discount_Tier"] = np.select(conditions, choices, default="CLEARANCE_20")

    FEATURES = [
        "Store","Month","Avg_Sales","Std_Sales","Avg_Customers",
        "Promo_Ratio","Holiday_Ratio","StoreType_enc","Assortment_enc",
        "Region_enc","CompetitionDistance","Promo2"
    ]
    le_tier = joblib.load(os.path.join(MODEL_DIR, "le_discount_tier.pkl"))
    X = agg[FEATURES]; y = le_tier.transform(agg["Discount_Tier"])
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = joblib.load(os.path.join(MODEL_DIR, "discount_xgb.pkl"))
    pred  = model.predict(X_test)

    acc  = float(accuracy_score(y_test, pred))
    f1   = float(f1_score(y_test, pred, average="weighted"))
    prec = float(precision_score(y_test, pred, average="weighted", zero_division=0))
    rec  = float(recall_score(y_test, pred, average="weighted", zero_division=0))
    print(f"  Discount XGB  Acc={acc:.4f}  F1={f1:.4f}  Prec={prec:.4f}  Rec={rec:.4f}")
    print(classification_report(y_test, pred, target_names=le_tier.classes_, zero_division=0))

    metrics = {"Discount_XGBoost": {
        "Accuracy":  acc, "F1_weighted": f1,
        "Precision": prec, "Recall": rec
    }}

    # ── Plot 5: Confusion matrix ──────────────────────────────────────────────
    cm = confusion_matrix(y_test, pred)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=le_tier.classes_, yticklabels=le_tier.classes_,
                ax=ax1, linewidths=0.5)
    ax1.set_title("Discount Classifier — Confusion Matrix", **TITLE_FONT)
    ax1.set_xlabel("Predicted"); ax1.set_ylabel("Actual")

    # ── Plot 6: Feature importance ────────────────────────────────────────────
    fi = pd.Series(model.feature_importances_, index=FEATURES).sort_values()
    ax2.barh(fi.index, fi.values,
             color=[PALETTE[0] if v > fi.median() else "#BBDEFB" for v in fi.values])
    ax2.set_title("Discount Classifier — Feature Importance", **TITLE_FONT)
    ax2.set_xlabel("Importance")
    for bar, v in zip(ax2.patches, fi.values):
        ax2.text(v+0.001, bar.get_y()+bar.get_height()/2,
                 f"{v:.3f}", va="center", fontsize=8)
    plt.tight_layout()
    save(fig, "05_discount_confusion_and_importance.png")

    return metrics


# ==============================================================================
# 4. INVENTORY REORDER — RF Classifier + XGBoost Priority
# ==============================================================================
def evaluate_inventory():
    section("4 / 5  INVENTORY REORDER CLASSIFICATION")

    rng = np.random.default_rng(42)
    n   = 60000
    avg_d = rng.uniform(50, 2000, n)
    std_d = avg_d * rng.uniform(0.1, 0.5, n)
    safety= 1.65 * std_d * np.sqrt(7)
    rop   = avg_d * 7 + safety

    inv_ratio = np.where(
        rng.random(n) < 0.15, rng.uniform(0.1, 0.5, n),
        np.where(rng.random(n) < 0.3, rng.uniform(0.5, 0.7, n),
        np.where(rng.random(n) < 0.5, rng.uniform(0.7, 0.85, n),
        np.where(rng.random(n) < 0.75, rng.uniform(0.85, 1.2, n),
        rng.uniform(1.2, 2.5, n)))))

    cur_inv  = rop * inv_ratio
    dos      = cur_inv / avg_d
    fest     = rng.choice([0,1], size=n, p=[0.8,0.2])
    month    = rng.integers(1,13, n)
    reg      = rng.integers(0,6, n)
    cat      = rng.integers(0,10, n)
    inv_pos  = cur_inv / rop

    action = np.where(
        fest==1,
        np.select([inv_pos>=1.5, inv_pos>=1.0, inv_pos>=0.8, inv_pos>=0.6],
                  ["OK","MONITOR","WATCHLIST","REORDER SOON"], "REORDER NOW"),
        np.select([inv_pos>=1.2, inv_pos>=0.85, inv_pos>=0.70, inv_pos>=0.50],
                  ["OK","MONITOR","WATCHLIST","REORDER SOON"], "REORDER NOW")
    )

    df = pd.DataFrame({
        "Avg_Daily_Demand":avg_d, "Std_Daily_Demand":std_d,
        "Current_Inventory":cur_inv, "Reorder_Point":rop,
        "Safety_Stock":safety, "Days_Of_Supply":dos,
        "Inventory_Position":inv_pos, "Festival_Upcoming":fest,
        "Month":month, "Region_enc":reg, "Category_enc":cat, "Action":action,
    })

    FEATURES = [
        "Avg_Daily_Demand","Std_Daily_Demand","Current_Inventory","Reorder_Point",
        "Safety_Stock","Days_Of_Supply","Inventory_Position","Festival_Upcoming",
        "Month","Region_enc","Category_enc"
    ]
    le_action = joblib.load(os.path.join(MODEL_DIR, "le_inventory_action.pkl"))
    X = df[FEATURES]; y = le_action.transform(df["Action"])
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    clf = joblib.load(os.path.join(MODEL_DIR, "inventory_rf.pkl"))
    pred = clf.predict(X_test)

    acc  = float(accuracy_score(y_test, pred))
    f1   = float(f1_score(y_test, pred, average="weighted"))
    prec = float(precision_score(y_test, pred, average="weighted", zero_division=0))
    rec  = float(recall_score(y_test, pred, average="weighted", zero_division=0))
    print(f"  Inventory RF  Acc={acc:.4f}  F1={f1:.4f}  Prec={prec:.4f}  Rec={rec:.4f}")
    print(classification_report(y_test, pred, target_names=le_action.classes_, zero_division=0))

    metrics = {"Inventory_RF": {
        "Accuracy":  acc, "F1_weighted": f1,
        "Precision": prec, "Recall": rec
    }}

    # ── Plot 7: Confusion matrix ──────────────────────────────────────────────
    cm = confusion_matrix(y_test, pred)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Greens",
                xticklabels=le_action.classes_, yticklabels=le_action.classes_,
                ax=ax1, linewidths=0.5)
    ax1.set_title("Inventory Classifier — Confusion Matrix", **TITLE_FONT)
    ax1.set_xlabel("Predicted"); ax1.set_ylabel("Actual")

    # Feature importance from RF
    fi = pd.Series(clf.feature_importances_, index=FEATURES).sort_values()
    ax2.barh(fi.index, fi.values,
             color=[PALETTE[2] if v > fi.median() else "#C8E6C9" for v in fi.values])
    ax2.set_title("Inventory RF — Feature Importance", **TITLE_FONT)
    ax2.set_xlabel("Importance")
    for bar, v in zip(ax2.patches, fi.values):
        ax2.text(v+0.001, bar.get_y()+bar.get_height()/2,
                 f"{v:.3f}", va="center", fontsize=8)
    plt.tight_layout()
    save(fig, "07_inventory_confusion_and_importance.png")

    return metrics


# ==============================================================================
# 5. STOCKOUT RISK — XGBoost Binary Classifier
# ==============================================================================
def evaluate_stockout():
    section("5 / 5  STOCKOUT RISK PREDICTION")

    rng = np.random.default_rng(123)
    n   = 60000
    avg_d  = rng.uniform(50, 2000, n)
    vol    = rng.uniform(0.1, 0.6, n)
    std_d  = avg_d * vol
    cur_inv= rng.uniform(0, avg_d * 30)
    dos    = cur_inv / avg_d
    fest7  = rng.choice([0,1], size=n, p=[0.85,0.15])
    month  = rng.integers(1,13, n)
    reg    = rng.integers(0,6, n)
    cat    = rng.integers(0,10, n)
    days_sr= rng.integers(0,30, n)

    exp_d7 = avg_d * 7 * (1.3 * fest7 + 1.0 * (1 - fest7))
    noise  = rng.normal(0, std_d * np.sqrt(7), n)
    actual_d7 = exp_d7 + noise
    stockout  = (cur_inv < actual_d7).astype(int)

    df = pd.DataFrame({
        "Current_Inventory":cur_inv, "Avg_Daily_Demand":avg_d,
        "Demand_Volatility":vol, "Days_Of_Supply":dos,
        "Lead_Time":7, "Days_Since_Reorder":days_sr,
        "Festival_In_7d":fest7, "Month":month,
        "Region_enc":reg, "Category_enc":cat,
        "Stockout_7d":stockout,
    })

    FEATURES = [
        "Current_Inventory","Avg_Daily_Demand","Demand_Volatility",
        "Days_Of_Supply","Lead_Time","Days_Since_Reorder",
        "Festival_In_7d","Month","Region_enc","Category_enc"
    ]
    X = df[FEATURES]; y = df["Stockout_7d"]
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = joblib.load(os.path.join(MODEL_DIR, "stockout_xgb.pkl"))
    pred  = model.predict(X_test)
    prob  = model.predict_proba(X_test)[:, 1]

    acc  = float(accuracy_score(y_test, pred))
    f1   = float(f1_score(y_test, pred, average="binary"))
    prec = float(precision_score(y_test, pred, average="binary", zero_division=0))
    rec  = float(recall_score(y_test, pred, average="binary", zero_division=0))
    fpr, tpr, _ = roc_curve(y_test, prob)
    roc_auc = float(auc(fpr, tpr))

    print(f"  Stockout XGB  Acc={acc:.4f}  F1={f1:.4f}  AUC={roc_auc:.4f}  Prec={prec:.4f}  Rec={rec:.4f}")

    metrics = {"Stockout_XGBoost": {
        "Accuracy":  acc, "F1_binary": f1,
        "Precision": prec, "Recall": rec, "ROC_AUC": roc_auc,
    }}

    # ── Plot 9: Confusion matrix + ROC ────────────────────────────────────────
    cm = confusion_matrix(y_test, pred)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Oranges",
                xticklabels=["No Stockout","Stockout"],
                yticklabels=["No Stockout","Stockout"],
                ax=ax1, linewidths=0.5)
    ax1.set_title("Stockout Predictor — Confusion Matrix", **TITLE_FONT)
    ax1.set_xlabel("Predicted"); ax1.set_ylabel("Actual")

    ax2.plot(fpr, tpr, color=PALETTE[1], lw=2, label=f"ROC (AUC = {roc_auc:.4f})")
    ax2.plot([0,1],[0,1],"k--",lw=1,label="Random classifier")
    ax2.set_xlabel("False Positive Rate"); ax2.set_ylabel("True Positive Rate")
    ax2.set_title("Stockout Predictor — ROC Curve", **TITLE_FONT)
    ax2.legend(fontsize=10); ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    save(fig, "09_stockout_confusion_and_roc.png")

    return metrics


# ==============================================================================
# SUMMARY CHART — All models side by side
# ==============================================================================
def plot_summary(all_metrics):
    section("SUMMARY CHART")

    rows = []
    for model, mets in all_metrics.items():
        for metric, value in mets.items():
            rows.append({"Model": model, "Metric": metric, "Value": value})
    df = pd.DataFrame(rows)

    # Primary accuracy/R2 metrics only
    key_metrics = {
        "RandomForest":          ("R2",        "R² Score",   PALETTE[0]),
        "XGBoost":               ("R2",        "R² Score",   PALETTE[1]),
        "Ensemble_RF40_XGB60":   ("R2",        "R² Score",   PALETTE[2]),
        "Festival_XGBoost":      ("R2",        "R² Score",   PALETTE[3]),
        "Discount_XGBoost":      ("Accuracy",  "Accuracy",   PALETTE[4]),
        "Inventory_RF":          ("Accuracy",  "Accuracy",   "#009688"),
        "Stockout_XGBoost":      ("ROC_AUC",   "ROC AUC",    "#795548"),
    }

    labels, values, colors = [], [], []
    for model, (metric, _, color) in key_metrics.items():
        if model in all_metrics and metric in all_metrics[model]:
            labels.append(model.replace("_", "\n"))
            values.append(all_metrics[model][metric])
            colors.append(color)

    fig, ax = plt.subplots(figsize=(14, 6))
    bars = ax.bar(labels, values, color=colors, width=0.6, edgecolor="white", linewidth=1.2)
    ax.set_ylim(0, 1.15)
    ax.axhline(1.0, color="gray", linestyle="--", lw=1, alpha=0.6)
    ax.set_ylabel("Score (R² / Accuracy / AUC)", fontsize=12)
    ax.set_title("All Models — Primary Performance Metric (Test Set)", **TITLE_FONT)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.012,
                f"{v:.4f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
    plt.xticks(fontsize=9)
    plt.tight_layout()
    save(fig, "11_model_summary.png")


# ==============================================================================
# MAIN
# ==============================================================================
def main():
    print("\n" + "="*60)
    print("  SEASONAL DEMAND FORECASTER — ML EVALUATION REPORT")
    print("  Date: March 2026  |  Output: outputs/evaluation/")
    print("="*60)

    all_metrics = {}

    m1 = evaluate_demand()
    all_metrics.update(m1)

    m2 = evaluate_festival()
    all_metrics.update(m2)

    m3 = evaluate_discount()
    all_metrics.update(m3)

    m4 = evaluate_inventory()
    all_metrics.update(m4)

    m5 = evaluate_stockout()
    all_metrics.update(m5)

    plot_summary(all_metrics)

    # ── Save JSON report ──────────────────────────────────────────────────────
    report = {
        "project":     "AI-Based Seasonal Demand Forecaster & Inventory Decision Support",
        "generated":   "2026-03-08",
        "framework":   "XGBoost 3.2.0 + scikit-learn 1.6.1",
        "dataset":     "Rossmann Store Sales (1,017,211 rows × 1,116 stores)",
        "models":      all_metrics,
        "eval_dir":    EVAL_DIR,
    }
    json_path = os.path.join(EVAL_DIR, "metrics_report.json")
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n✅  metrics_report.json → {json_path}")

    section("EVALUATION COMPLETE")
    print(f"  All artefacts saved to: {EVAL_DIR}")
    print(f"  Files generated:")
    for fname in sorted(os.listdir(EVAL_DIR)):
        size = os.path.getsize(os.path.join(EVAL_DIR, fname))
        print(f"    {fname:50s}  {size//1024:>6} KB")


if __name__ == "__main__":
    main()
