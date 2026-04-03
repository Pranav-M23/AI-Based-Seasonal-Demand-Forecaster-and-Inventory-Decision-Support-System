# ML Documentation — AI-Based Seasonal Demand Forecaster & Inventory Decision Support System

**Project**: S6 MiniProject — College of Engineering  
**Date**: March 2026  
**Tech Stack**: Python 3.10 · XGBoost 3.2.0 · scikit-learn 1.6.1 · FastAPI · React  

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Why Machine Learning?](#2-why-machine-learning)
3. [Dataset](#3-dataset)
4. [Architecture Overview](#4-architecture-overview)
5. [Model 1 — Demand Forecasting](#5-model-1--demand-forecasting-rf--xgboost-ensemble)
6. [Model 2 — Festival Impact](#6-model-2--festival-impact-xgboost-regressor)
7. [Model 3 — Discount Optimization](#7-model-3--discount-optimization-xgboost-classifier)
8. [Model 4 — Inventory Reorder](#8-model-4--inventory-reorder-classification-rf-classifier)
9. [Model 5 — Stockout Risk](#9-model-5--stockout-risk-prediction-xgboost-binary-classifier)
10. [Feature Engineering](#10-feature-engineering)
11. [Training Process](#11-training-process)
12. [Evaluation Results](#12-evaluation-results)
13. [Deployment Strategy](#13-deployment-strategy)
14. [File Reference](#14-file-reference)

---

## 1. Problem Statement

Indian retail stores face two interrelated challenges:

| Challenge | Impact |
|-----------|--------|
| Demand spikes during festivals (Diwali +300%) | Stockouts → lost revenue |
| Slow seasons (July–August) | Overstock → wastage + holding costs |
| Manual reorder decisions | Errors, delays, inconsistency |
| Non-data-driven discounts | Margin loss or missed sales |

**Goal**: Replace all rule-based heuristics with trained ML models that:
- Forecast daily demand for 258 Indian stores × 10 product categories
- Detect festival uplift automatically from patterns
- Recommend optimal discount tiers
- Classify inventory urgency (OK → REORDER NOW)
- Predict 7-day stockout probability in real-time

---

## 2. Why Machine Learning?

### Rule-based approach (before):
```python
# Hard-coded festival calendar
if festival == "Diwali":
    uplift = 3.0    # always 3×, same for every store/category
discount = 10%      # same discount every month
reorder = current_stock < 500  # arbitrary threshold
```

**Problems**: No personalisation, no uncertainty, fails on new data, brittle.

### ML approach (after):

| Decision | ML Model | Why better |
|----------|----------|-----------|
| Daily demand | RF + XGBoost ensemble | Learns store–season–promo interactions |
| Festival uplift | XGBoost Regressor | Different uplift per store/month/category |
| Discount tier | XGBoost Classifier | Demand-based tier, not flat % |
| Reorder urgency | Random Forest | Continuously scaled urgency, not binary |
| Stockout risk | XGBoost Classifier | Probability with lead time & volatility |

---

## 3. Dataset

### Dataset Creation and Processing

The dataset is built in two layers: a robust training layer from the Rossmann Kaggle data and a localized Indian retail layer that drives the final forecasts and downstream decisions.

**1) Rossmann data preparation**
- Merge `train.csv` with `store.csv` so each transaction inherits store metadata.
- Keep only open days and positive sales to remove closed-store noise.
- Parse `Date` and derive `Year`, `Month`, and `WeekOfYear` while retaining `DayOfWeek`.
- Encode `StoreType` and `Assortment`, persisting encoders for consistent reuse.
- Fill missing numeric values (e.g., competition distance, promo flags) with safe defaults.

**2) Indian store and category synthesis**
- Generate 258 Indian stores across 6 regions and 16 chains, each with state, region, store type, area, and competition distance.
- Create 10 product categories with typical item counts per store.
- Map each Indian store to a Rossmann store ID (modulo mapping) to keep feature compatibility.

**3) Baseline forecast generation**
- Use the RF + XGBoost ensemble to predict daily demand for every store-category-date in 2026.
- Scale Rossmann revenue predictions to category-level item counts using each category's average items per store.
- Inject small stochastic noise (3%) and floor low values to avoid flat or zero sales.

**4) Festival enrichment and FSI**
- Load regional and state calendars from JSON and expand them into festival windows with pre, core, and post-festival weights.
- Apply region and state rules, with stronger core weights for Diwali and regional realism (e.g., Durga in West Bengal).
- Predict ML festival uplift and blend with calendar weights (60% ML, 40% calendar).
- Compute `FSI = Festival_Weight * 100` and adjust demand as `Adjusted = Baseline * (1 + Festival_Weight)`.

**5) Final outputs**
- Write the localized, festival-aware dataset to `outputs/yearly_forecast_indian.csv`.
- Aggregate store-category-month features to feed discount, inventory, and stockout models.

### Primary Training Dataset: Rossmann Store Sales
- **Source**: Real German retail chain (Kaggle competition)  
- **Size**: 1,017,211 transaction rows × 18 features  
- **Stores**: 1,116 stores across store types a/b/c/d  
- **Date range**: Jan 2013 – Jul 2015  
- **Target variable**: `Sales` (daily store revenue)

```
train.csv   — 1,017,211 rows (transactions)
store.csv   — 1,116 rows  (store metadata)
```

### Columns used:

| Column | Type | Role |
|--------|------|------|
| Store | int | Store ID (feature) |
| DayOfWeek | int 1–7 | Temporal feature |
| Date | date | Engineered → Year, Month, WeekOfYear |
| Sales | float | **Demand target** |
| Customers | int | Demand proxy |
| Open | bool | Filter (only open days) |
| Promo | bool | Promotion active |
| StateHoliday | str | Festival proxy |
| SchoolHoliday | bool | Seasonal feature |
| StoreType | str a/b/c/d | Encoded → `StoreType_enc` |
| Assortment | str a/b/c | Encoded → `Assortment_enc` |
| CompetitionDistance | float | Business context |
| Promo2 | bool | Extended promo |

### Indian Stores Mapping
- **258 stores** mapped across 6 regions (North, South, East, West, Central, Northeast)  
- **10 product categories**: Fresh Produce, Groceries, Electronics, Clothing, Dairy, Personal Care, Home Care, Health, Snacks, Kitchen  
- Rossmann-trained models run predictions scaled to Indian demand levels

---

## 4. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRAINING PHASE (offline)                      │
│                                                                  │
│  Data/train.csv  ──►  ml_models.py  ──►  models/*.pkl           │
│  Data/store.csv         │                                        │
│                    5 model trainers                              │
│                    (RF, XGBoost ×4)                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PIPELINE PHASE (ml_pipeline.py)               │
│                                                                  │
│  models/*.pkl  ──►  Predict for Indian stores  ──►  outputs/*.csv │
│                     (258 stores × 365 days × 10 categories)     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVING PHASE (FastAPI)                       │
│                                                                  │
│  outputs/*.csv  ──►  backend/app/  ──►  REST API (port 8000)    │
│                      data_loader.py                              │
│                      main.py (v15.2)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION (React)                          │
│                                                                  │
│  frontend/src/  ──►  Dashboard (port 3000)                      │
│  Chart.js + Tailwind CSS                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Model 1 — Demand Forecasting (RF + XGBoost Ensemble)

### Objective
Predict daily `Sales` for any store, given date + promo context.

### Features (11)
```python
DEMAND_FEATURES = [
    "Store",             # Store ID (1–1116)
    "DayOfWeek",         # 1=Mon … 7=Sun
    "Promo",             # 0/1 — promotion active today
    "SchoolHoliday",     # 0/1 — school holiday
    "CompetitionDistance", # metres to nearest competitor
    "Promo2",            # 0/1 — extended promotional period
    "Year",              # 2013–2015
    "Month",             # 1–12
    "WeekOfYear",        # 1–53
    "StoreType_enc",     # LabelEncoded: a→0, b→1, c→2, d→3
    "Assortment_enc",    # LabelEncoded: a→0, b→1, c→2
]
```

### Architecture: Stacked Ensemble

```
X ──► Random Forest (n=150, depth=18) ──► rf_pred
   │                                          │
   └──► XGBoost (n=300, lr=0.08, depth=8) ──► xgb_pred
                                               │
                     Ensemble = 0.4 × rf_pred + 0.6 × xgb_pred
```

**Why 40/60 blend?** XGBoost captures non-linear feature interactions better and has lower MAE on validation; RF provides regularisation against XGBoost overfitting on sparse dates.

### Hyperparameters

| Param | Random Forest | XGBoost |
|-------|--------------|---------|
| n_estimators | 150 | 300 |
| max_depth | 18 | 8 |
| learning_rate | — | 0.08 |
| subsample | — | 0.8 |
| colsample_bytree | — | 0.8 |
| reg_alpha | — | 0.1 |
| reg_lambda | — | 1.0 |
| tree_method | — | hist (GPU-like) |

### Data Split
- 85% training / 15% test (`train_test_split(random_state=42)`)
- ~864,000 training rows, ~153,000 test rows

### Performance

| Model | MAE | RMSE | R² |
|-------|-----|------|----|
| Random Forest | ~886 | ~1,381 | 0.83 |
| XGBoost | ~708 | ~1,098 | 0.89 |
| **Ensemble (final)** | **~728** | **~1,128** | **0.89** |

---

## 6. Model 2 — Festival Impact (XGBoost Regressor)

### Objective
Predict `festival uplift` = (holiday_sales − normal_sales) / normal_sales per store-month, expressed as a fraction (e.g. 0.30 = +30%).

### Features (6)
```python
["Store", "Month", "StoreType_enc", "Assortment_enc", "CompetitionDistance", "Promo2"]
```

### Label Construction
- `Normal_Avg` = mean Sales on non-holiday days, per (Store, Month)
- `Holiday_Avg` = mean Sales on StateHoliday days, per (Store, Month)
- `Uplift` = (Holiday_Avg − Normal_Avg) / Normal_Avg, clipped to [−0.5, 1.0]

### Training Data
- ~12,000 store-month combinations with matched holiday/normal data
- 80/20 train/test split

### Performance

| Metric | Value |
|--------|-------|
| MAE | ~0.04 (4 percentage points) |
| RMSE | ~0.06 |
| R² | 0.69 |

### How it's used in production
```python
# In ml_pipeline.py — blends ML uplift with festival calendar
ml_uplift = festival_model.predict(features)         # model output
cal_weight = festival_calendar_weight                # rule-based calendar
final_uplift = 0.6 * ml_uplift + 0.4 * cal_weight   # 60/40 blend
adjusted = baseline * (1 + final_uplift)
```

**Result**: 62,000 rows have festival-adjusted forecast. Diwali peaks reach FSI = 332%.

---

## 7. Model 3 — Discount Optimization (XGBoost Classifier)

### Objective
Classify each store-month into 1 of 4 discount tiers:

| Tier | Discount | When |
|------|----------|------|
| NO_DISCOUNT | 0% | High demand / festival period |
| SMALL_5 | 5% | Moderate demand |
| MEDIUM_10 | 10% | Low-moderate demand |
| HIGH_15 | 15% | Low demand / slow season |

### Features (12)
```python
["Store", "Month", "Avg_Sales", "Std_Sales", "Avg_Customers",
 "Promo_Ratio", "Holiday_Ratio", "StoreType_enc", "Assortment_enc",
 "Region_enc", "CompetitionDistance", "Promo2"]
```

### Label Construction
```python
Demand_Score = (Avg_Sales / P75_Sales × 0.4)
             + (Holiday_Ratio × 0.3)
             + (Avg_Customers / P75_Customers × 0.3)

if Demand_Score ≥ 0.80: "NO_DISCOUNT"
elif Demand_Score ≥ 0.60: "SMALL_5"
elif Demand_Score ≥ 0.40: "MEDIUM_10"
elif Demand_Score ≥ 0.20: "HIGH_15"
else:                      "CLEARANCE_20"
```

### Performance

| Metric | Value |
|--------|-------|
| Accuracy | 0.99 |
| F1 (weighted) | 0.99 |
| Precision | 0.99 |
| Recall | 0.99 |

### Production output distribution (30,960 store-month rows):
```
HIGH_15       → 18,305  (59%)   Slow-demand periods
MEDIUM_10     →  5,540  (18%)
NO_DISCOUNT   →  4,725  (15%)   Festival periods
SMALL_5       →  2,390  ( 8%)
```

---

## 8. Model 4 — Inventory Reorder Classification (RF Classifier)

### Objective
Classify inventory status into 5 urgency tiers and compute a priority score.

| Tier | Meaning | Action |
|------|---------|--------|
| OK | Well stocked | No action |
| MONITOR | Adequate | Watch closely |
| WATCHLIST | Getting low | Plan order |
| REORDER SOON | Below reorder point | Order within 3 days |
| REORDER NOW | Critical — stockout imminent | Order immediately |

### Two sub-models

**4a. Random Forest Classifier** → predicts urgency tier  
**4b. XGBoost Regressor** → assigns continuous `priority_score` (0–100)

### Features (11)
```python
["Avg_Daily_Demand", "Std_Daily_Demand", "Current_Inventory",
 "Reorder_Point", "Safety_Stock", "Days_Of_Supply",
 "Inventory_Position",   # Current_Inventory / Reorder_Point
 "Festival_Upcoming", "Month", "Region_enc", "Category_enc"]
```

### Label Generation (synthetic data — 60,000 samples)
```python
# Rule: inventory position + festival awareness
Inventory_Position = Current_Inventory / Reorder_Point

if festival_upcoming:
    # More aggressive thresholds during festivals
    OK if pos >= 1.5, MONITOR if >= 1.0, WATCHLIST if >= 0.8 ...
else:
    OK if pos >= 1.2, MONITOR if >= 0.85 ...
```

### Safety Stock Formula (Wilson model)
```
Safety_Stock = Z × σ_demand × √(Lead_Time)
             = 1.65 × Std_Daily_Demand × √7
```

### Performance

| Model | Accuracy | F1 (weighted) |
|-------|----------|--------------|
| Inventory RF | 0.9995 | 0.9995 |
| Priority XGB | R² = 0.998 | — |

### Production output (2,580 Indian store decisions):
```
MONITOR      → 795 (31%)
OK           → 540 (21%)
WATCHLIST    → 504 (20%)
REORDER SOON → 375 (15%)
REORDER NOW  → 366 (14%)
```

---

## 9. Model 5 — Stockout Risk Prediction (XGBoost Binary Classifier)

### Objective
Predict probability of stockout within the **next 7 days** (binary: 0 / 1).

### Features (10)
```python
["Current_Inventory", "Avg_Daily_Demand", "Demand_Volatility",
 "Days_Of_Supply", "Lead_Time", "Days_Since_Reorder",
 "Festival_In_7d",   # is there a festival in next 7 days?
 "Month", "Region_enc", "Category_enc"]
```

### Label Generation (synthetic, 60,000 samples)
```python
# Realistic simulation
Expected_Demand_7d = Avg_Daily_Demand × 7 × (1.3 if festival else 1.0)
Noise = Normal(0, Std_Daily_Demand × √7)
Actual_Demand_7d = Expected + Noise
Stockout = 1 if Current_Inventory < Actual_Demand_7d else 0
```

### Handling class imbalance
```python
XGBClassifier(scale_pos_weight=1.5)  # ~40% positive rate
```

### Performance

| Metric | Value |
|--------|-------|
| Accuracy | 0.97 |
| F1 (binary) | 0.96 |
| ROC AUC | 0.99 |
| Precision | 0.96 |
| Recall | 0.97 |

### How it drives the dashboard
```python
# inventory_decisions_indian.csv
Stockout_Risk = 0.977  # → "REORDER NOW" in ActionPanel
```

---

## 10. Feature Engineering

### Temporal features (from Date)
| Feature | Formula |
|---------|---------|
| Year | `date.year` |
| Month | `date.month` |
| WeekOfYear | `date.isocalendar().week` |
| DayOfWeek | Already in dataset (1–7) |

### Categorical encoding
```python
LabelEncoder().fit_transform(StoreType)   # a/b/c/d → 0/1/2/3
LabelEncoder().fit_transform(Assortment)  # a/b/c   → 0/1/2
LabelEncoder().fit_transform(Region)      # 6 Indian regions → 0-5
```

### Derived inventory features
```python
Inventory_Position = Current_Inventory / Reorder_Point    # key ratio
Days_Of_Supply     = Current_Inventory / Avg_Daily_Demand
Demand_Volatility  = Std_Daily_Demand / Avg_Daily_Demand  # CV
```

### Scale normalisation (Indian stores → Rossmann scale)
```python
# Rossmann stores average ~5,500 sales/day
# Indian category average ~300-500 units/month
scale = rossmann_mean / indian_mean
# Applied to Avg_Sales, Std_Sales, Avg_Customers before classification
```

---

## 11. Training Process

### How to retrain all models:
```bash
cd "S:\Pnav College\S6\MiniProject\Seasonal Demand Forecaster"
python ml_models.py         # trains and saves to models/
python ml_pipeline.py       # generates output CSVs for API
```

### Force retrain (ignore cached .pkl):
```python
# In ml_models.py
train_all_models(force_retrain=True)
```

### Training time (approximate):
| Step | Duration |
|------|----------|
| Data loading + merge | ~15 s |
| Random Forest demand | ~180 s |
| XGBoost demand | ~45 s |
| Festival XGBoost | ~10 s |
| Discount XGBoost | ~8 s |
| Inventory RF + XGB | ~35 s |
| Stockout XGBoost | ~15 s |
| **Total** | **~8 min** |

---

## 12. Evaluation Results

Full evaluation with charts: run `python ml_evaluation_report.py`  
Outputs saved to `outputs/evaluation/`

### Summary table:

| Model | Algorithm | Primary Metric | Value |
|-------|-----------|---------------|-------|
| Demand Forecasting | **RF + XGBoost Ensemble** | R² | **0.89** |
| &nbsp; | Random Forest only | R² | 0.83 |
| &nbsp; | XGBoost only | R² | 0.89 |
| Festival Impact | XGBoost Regressor | R² | 0.69 |
| Discount Optimization | XGBoost Classifier | Accuracy | **0.99** |
| Inventory Reorder | Random Forest Classifier | Accuracy | **0.9995** |
| Stockout Risk | XGBoost Classifier | ROC AUC | **0.99** |

### Charts generated:
1. `01_demand_comparison.png` — RF vs XGBoost vs Ensemble bar chart
2. `02_demand_scatter.png` — Actual vs Predicted scatter (3000 pts)
3. `03_demand_feature_importance.png` — Top features for demand
4. `04_festival_predictions.png` — Uplift actual vs predicted
5. `05_discount_confusion_and_importance.png` — Confusion matrix + features
6. `07_inventory_confusion_and_importance.png` — Confusion matrix + features
7. `09_stockout_confusion_and_roc.png` — Confusion matrix + ROC curve
8. `11_model_summary.png` — All-model summary bar chart

---

## 13. Deployment Strategy

### Current architecture (offline inference):

```
ml_pipeline.py runs ONCE → outputs/*.csv → FastAPI serves CSVs
```

**Why offline?** 941,700 forecast rows (258 stores × 10 categories × 365 days) — real-time inference would require ~10 minutes per request.

### API endpoints (FastAPI, port 8000):

| Endpoint | Data | ML source |
|----------|------|-----------|
| `GET /forecast/region` | Daily demand by region | Demand ensemble |
| `GET /forecast/store` | Daily demand by store | Demand ensemble |
| `GET /discount/region` | Weekly discount tiers | Discount classifier |
| `GET /inventory/store-decisions` | Reorder urgency + priority | Inventory RF + XGB |
| `GET /actions/store` | Prioritised action list | All models |

### Frontend (React, port 3000):
- Forecast chart with festival peaks visible
- Stock section with ML stockout risk score
- Discount recommendation panel
- Action panel with CRITICAL/HIGH/MEDIUM priorities

### To restart the system:
```bash
# Backend
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend
npm start
```

---

## 14. File Reference

```
Seasonal Demand Forecaster/
├── ml_models.py                 ← Model training code (5 models)
├── ml_pipeline.py               ← Run predictions, generate CSVs
├── ml_evaluation_report.py      ← Generate metrics + charts
├── ML_DOCUMENTATION.md          ← This file
├── model_comparison_notebook.ipynb ← Visual notebook
│
├── models/                      ← Saved model files
│   ├── demand_rf.pkl            (270 MB — Random Forest)
│   ├── demand_xgb.pkl           (4.7 MB — XGBoost)
│   ├── festival_uplift_xgb.pkl  (0.5 MB)
│   ├── discount_xgb.pkl         (1.7 MB)
│   ├── inventory_rf.pkl         (9.3 MB)
│   ├── inventory_priority_xgb.pkl (0.8 MB)
│   ├── stockout_xgb.pkl         (1.0 MB)
│   └── le_*.pkl                 (Label Encoders)
│
├── Data/
│   ├── train.csv                ← Rossmann 1M rows
│   ├── store.csv                ← 1116 stores
│   ├── store_region.csv         ← Indian store mapping
│   └── festival_calender.csv    ← Indian festival calendar
│
├── outputs/
│   ├── yearly_forecast_indian.csv    (941,700 rows — ML demand)
│   ├── discount_recommendations_enhanced.csv (30,960 rows — ML tiers)
│   ├── region_discount_recommendations.csv (288 rows — weekly)
│   ├── inventory_decisions_indian.csv (2,580 rows — ML decisions)
│   ├── action_recommendations_enhanced.csv (6,035 rows)
│   └── evaluation/              ← Generated by ml_evaluation_report.py
│       ├── metrics_report.json
│       └── *.png
│
└── backend/app/
    ├── main.py                  ← FastAPI v15.2
    ├── data_loader.py           ← CSV → in-memory store
    └── schemas.py               ← Pydantic models
```
