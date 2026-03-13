# Seasonal Demand Forecaster — Feature & Change Summary

> **For AI Continuity** — This document summarises every feature, architectural decision, and non-trivial change made to this project. A new Claude (or any AI assistant) should read this before suggesting any modifications.

---

## Project Identity

| Field | Value |
|---|---|
| **Name** | Seasonal Demand Forecaster |
| **Type** | AI-powered retail analytics platform |
| **Backend version** | v15.2 (FastAPI, Python 3.10) |
| **Frontend** | React 18 + Chart.js + Tailwind CSS |
| **ML stack** | XGBoost 3.2 + scikit-learn 1.6.1 + joblib |
| **Port config** | Backend → 8000, Frontend → 3000 |
| **Current date context** | March 2026 |

---

## 1. Scale & Scope

The platform covers **258 Indian retail stores** across **6 geographic regions**, **10 product categories**, and **16 retail chains** (DMart, Reliance Smart, Big Bazaar, More Megastore, Spencer's, Star Bazaar, HyperCity, Metro Cash & Carry, Vishal Mega Mart, V-Mart, Ratnadeep, Heritage Fresh, Nilgiris, Foodworld, Aadhaar, Kirana King).

The forecast dataset contains approximately **942,700 rows** (258 stores × 10 categories × 365 days).

---

## 2. Three-Phase Architecture

```
Phase 1 — TRAINING (offline, one-time)
  ml_models.py → trains 5 ML models on Rossmann Kaggle data → saves .pkl to models/

Phase 2 — PIPELINE (offline, regenerable)
  ml_pipeline.py → loads models → applies to 258 Indian stores → writes CSVs to outputs/

Phase 3 — SERVING (runtime)
  backend/app/main.py (FastAPI) → serves CSVs as REST API → React frontend visualises
```

The backend **never runs inference at request time** — it serves pre-generated CSV outputs. This makes the API extremely fast (simple DataFrame filters, no model loading on request).

---

## 3. Data Sources

### Training Data (Rossmann Kaggle Dataset — German stores)
| File | Rows | Description |
|---|---|---|
| `Data/train.csv` | 1,017,211 | Daily sales 2013–2015, 1,116 German stores |
| `Data/store.csv` | 1,116 | Store metadata: type, assortment, competition distance, Promo2 |
| `Data/store_region.csv` | 1,116 | Store→Region mapping |
| `Data/test.csv` | — | Held-out test set |

### Indian Market Data (Generated/Supplementary)
| File | Description |
|---|---|
| `outputs/indian_stores.csv` | 258 synthetic Indian stores with names, chains, regions |
| `outputs/product_categories.csv` | 10 product categories with avg items per store |
| `Data/festival_calender.csv` | Indian festival calendar with dates, weights, regional applicability |
| `Data/qrs_technologies_sales_2025.csv` | Supplementary real-world sales data |
| `Data/sample_shop_owner_sales.csv` | Used by Shop Owner Analytics feature |

### Output CSVs (Pipeline → API Bridge)
| File | Consumed by |
|---|---|
| `outputs/yearly_forecast_indian.csv` | All `/forecast/*` endpoints |
| `outputs/region_discount_recommendations.csv` | `/discount/region` |
| `outputs/discount_recommendations_enhanced.csv` | `/discount/store-month` |
| `outputs/inventory_decisions_indian.csv` | `/inventory/store-decisions` |
| `outputs/inventory_kpi_region_summary.csv` | `/kpi/region-summary` |
| `outputs/action_recommendations_enhanced.csv` | `/actions/store` |
| `outputs/top_priority_reorders.csv` | Top 50 critical items (informational) |

---

## 4. Five ML Models

### Model 1 — Demand Forecasting (RF + XGBoost Ensemble)
- **Task**: Predict daily sales for store + date + promo context
- **Algorithm**: RF(n=150, depth=18) blended 40% + XGBoost(n=300, depth=8, lr=0.08) blended 60%
- **Features (11)**: Store, DayOfWeek, Promo, SchoolHoliday, CompetitionDistance, Promo2, Year, Month, WeekOfYear, StoreType_enc, Assortment_enc
- **Performance**: R²=0.89, MAE≈728
- **Indian store adaptation**: Rossmann IDs mapped via `Store_ID % 1116 + 1`; output scaled by `category_avg / rossmann_avg`
- **Saved as**: `models/demand_rf.pkl`, `models/demand_xgb.pkl`

### Model 2 — Festival Uplift (XGBoost Regressor)
- **Task**: Predict store-month festival uplift fraction (e.g. 0.30 = +30%)
- **Label construction**: `(holiday_avg − normal_avg) / normal_avg`, clipped to [-0.5, 1.0]
- **Features (6)**: Store, Month, StoreType_enc, Assortment_enc, CompetitionDistance, Promo2
- **Performance**: R²=0.69, MAE≈0.04
- **Production blend**: `final_uplift = 0.6 × ML_uplift + 0.4 × calendar_weight`
- **Result**: Diwali FSI peaks at 332%; 62,000 rows festival-adjusted
- **Saved as**: `models/festival_uplift_xgb.pkl`

### Model 3 — Discount Tier Optimization (XGBoost Classifier)
- **Task**: Classify store-month into 5 tiers: NO_DISCOUNT / SMALL_5 / MEDIUM_10 / HIGH_15 / CLEARANCE_20
- **Features (12)**: Store, Month, Avg_Sales, Std_Sales, Avg_Customers, Promo_Ratio, Holiday_Ratio, StoreType_enc, Assortment_enc, Region_enc, CompetitionDistance, Promo2
- **Label**: Demand Score = 0.4×(Sales/P75) + 0.3×Holiday_Ratio + 0.3×(Customers/P75)
- **Performance**: Accuracy 0.99, F1 0.99
- **Output distribution**: HIGH_15→59%, MEDIUM_10→18%, NO_DISCOUNT→15%, SMALL_5→8%
- **Saved as**: `models/discount_xgb.pkl`

### Model 4 — Inventory Urgency (RF Classifier + XGBoost Priority Scorer)
- **4a RF Classifier**: 5-tier urgency — OK / MONITOR / WATCHLIST / REORDER SOON / REORDER NOW
- **4b XGBoost Regressor**: Continuous priority score 0–100
- **Features (11)**: Avg_Daily_Demand, Std_Daily_Demand, Current_Inventory, Reorder_Point, Safety_Stock, Days_Of_Supply, Inventory_Position, Festival_Upcoming, Month, Region_enc, Category_enc
- **Training**: 60,000 synthetic samples with festival-aware thresholds
- **Safety stock**: Wilson model — `Safety_Stock = 1.65 × σ_demand × √7`
- **Performance**: RF Accuracy 0.9995, Priority R²=0.998
- **Production output distribution**: MONITOR 31%, OK 21%, WATCHLIST 20%, REORDER SOON 15%, REORDER NOW 14%
- **Saved as**: `models/inventory_rf.pkl`, `models/inventory_priority_xgb.pkl`

### Model 5 — 7-Day Stockout Risk (XGBoost Binary Classifier)
- **Task**: Binary prediction — will this item stock out within the next 7 days?
- **Features (10)**: Current_Inventory, Avg_Daily_Demand, Demand_Volatility, Days_Of_Supply, Lead_Time, Days_Since_Reorder, Festival_In_7d, Month, Region_enc, Category_enc
- **Training**: 60,000 synthetic samples; `scale_pos_weight=1.5` for class imbalance
- **Performance**: Accuracy 0.97, F1=0.96, ROC AUC=**0.99**
- **Saved as**: `models/stockout_xgb.pkl`

---

## 5. Backend API — All Endpoints

**File**: `backend/app/main.py` | FastAPI | CORS open for localhost:3000 and localhost:5173

### Meta / Health
| Endpoint | Description |
|---|---|
| `GET /` | Root — returns version string and feature list |
| `GET /health` | Service health with row counts |
| `GET /meta` | Regions, store IDs, category list, years, `store_names` dict |
| `POST /refresh` | Hot-reload all CSV data from disk |
| `GET /regions` | All available region strings |
| `GET /stores?region=&state=` | Store IDs filtered by region/state |
| `GET /categories` | All categories including "All" |
| `GET /debug/data-status` | Debug: shows loading status for all data sources |

### Forecast
| Endpoint | Key Params | Notes |
|---|---|---|
| `GET /forecast/region` | `region`, `start?`, `end?`, `month?`, `year?` | Daily demand aggregated across all stores in region |
| `GET /forecast/store` | `store`, filters | Daily demand for a single store |
| `GET /forecast/store-category` | `store`, `category`, filters | Per-store per-category. **Enriched**: each point includes `festival` name + `fsi` value for frontend overlays |

### Discount
| Endpoint | Params | Source CSV |
|---|---|---|
| `GET /discount/region` | `region` | `region_discount_recommendations.csv` — weekly discount % |
| `GET /discount/store-month` | `store`, `month?`, `category?` | `discount_recommendations_enhanced.csv` with graceful fallback |

### Inventory
| Endpoint | Params | Returns |
|---|---|---|
| `GET /inventory/exec-summary` | — | Fleet-wide: total, reorder_now, watchlist, ok counts |
| `GET /inventory/region-actions` | — | REORDER NOW / WATCHLIST / OK counts per region |
| `GET /inventory/store-decisions` | `store`, `decision?`, `category?`, `limit`, `offset` | Paginated `StoreDecisionRow` records (see schema below) |

**`StoreDecisionRow` schema** (complete):
```
store, region, category, decision, stockout_risk,
reorder_point, safety_stock, days_of_supply,
current_inventory, priority_score,
recommended_order_qty, days_until_stockout
```

### Actions & KPI
| Endpoint | Params | Notes |
|---|---|---|
| `GET /actions/store` | `store`, `category?`, `priority?` | CRITICAL/HIGH/MEDIUM/INFO actions. Uses enhanced CSV, falls back to reorder alerts |
| `GET /kpi/store` | `store` | avg_days_supply, low_stock_items, critical_items, total_current_stock |
| `GET /kpi/region-summary` | — | Per-region: stores, avg/max stockout risk, avg reorder point, total safety stock |

### Data Loading (`backend/app/data_loader.py`)
- **Singleton `DataStore`** loads all CSVs on startup
- **Priority fallback chain**: New Indian-store files tried first; legacy files used as fallback
- **Column aliasing**: Automatically resolves differences e.g. `Store_ID`→`Store`, `Action`→`Decision`, `Product_Category`→`Category`
- **Hot reload** via `POST /refresh` without server restart

---

## 6. Frontend — All Pages & Components

**Root**: `frontend/src/App.js` (main, full-featured) + `App.jsx` (simplified variant)

### Page 1 — Inventory Dashboard Analytics

**`Sidebar.js`** — Icon sidebar (Warehouse icon) for page navigation

**`Header.js`** — Controls:
- Region dropdown (populated from `/meta`)
- Store dropdown (populated from `/stores?region=...`, shows human-readable names from `store_names` map)
- `[Load Dashboard]` button

**`SummaryCards.js`** — 4 KPI cards from `/inventory/exec-summary`:
- Total Items (blue, Package icon)
- REORDER NOW (red, AlertCircle icon)
- WATCHLIST (yellow, AlertTriangle icon)
- OK (green, CheckCircle icon)

**`ForecastChart.js`** — The most complex component:
- Fetches `/forecast/store-category` data
- Aggregates daily → weekly buckets
- Computes 4-week rolling average (dashed amber line)
- Two Chart.js datasets: "Weekly Sales" (cyan area fill) + "4-Wk Trend" (dashed)
- **Custom festival overlay plugin** (`festivalLines`): dashed vertical lines with floating coloured badges (e.g. "Diwali +332%")
- **Month grid plugin** (`monthGrid`): subtle vertical separators at month boundaries
- Festival points highlighted with colored dots; tooltip shows festival name + FSI

**Hardcoded 2026 Indian Festival Calendar** (in `ForecastChart.js`):
```
Pongal = Jan 14 | Holi = Mar 25 | Vishu = Apr 14
Independence Day = Aug 15 | Onam = Aug 22
Navaratri/Dussehra = Oct 2 | Diwali = Oct 20 | Christmas = Dec 25
```

**`StockSection.js`** — FSI & Discount Intelligence Panel:
- Period filter: Month view (Month + Week selectors) OR Quarter view (Q1–Q4)
- **FSI computation** (3-source blend):
  1. Static calendar boosts: Onam=×9.5, Diwali=×3.5, etc.
  2. Backend `fsi` field from forecast endpoint
  3. Ratio of period-avg to annual-avg baseline
- **FSI display bands**: 🔥 Explosive (≥9×), 🚀 Peak (≥3×), 📈 High (≥1.5×), 👍 Normal (≥0.85×), ⬇️ Slow (≥0.65×), 📉 Very Slow (<0.65×)
- **Smart discount logic (inverse-FSI)**: FSI≥3→0% discount, FSI≥1.5→5%, FSI≥0.8→10%, FSI≥0.65→20%, else→30%
- **Stock status**: RESTOCK NOW / MONITOR / CLEAR STOCK / OK — colour-coded card border
- Displays: days-of-stock (FSI-adjusted), festival name badge, reorder point, safety stock, stockout risk %

**`ActionPanel.js`** — ML-Sourced Scenario Recommendations:
- Uses same period/FSI detection logic as `StockSection.js`
- Generates one of 5 contextual **scenarios** based on live ML data:
  1. **🚀 Peak Live**: Festival active (FSI≥3) → monitor hourly, no discounts, emergency restock if critical
  2. **⚠️ Stockpiling Phase**: Festival in ≤21 days → double reorder qty, order before day N
  3. **📈 Sales Heavy**: High demand non-festival (FSI≥1.5) → minimal discounts, increase restock frequency
  4. **📉 Demand Slump**: FSI≤0.79 → flash sale at computed discount %, pause shipments, bundle slow-movers
  5. **✅ Healthy Movement**: Normal FSI → routine restock note, upcoming festival preview
- All numbers (order quantities, days-to-stockout, stockout risk %) sourced from ML fields in `/inventory/store-decisions`

### Page 2 — Shop Owner Analytics

**`ShopOwnerAnalytics.js`** — Independent personal forecaster page:
- **CSV Upload**: User uploads their own sales CSV
- **Form**: Owner name, business name, region, state, product categories (multi-select), sales year
- **Forecast generation** (100% client-side, no backend call):
  - Parses CSV; auto-detects date/sales/category column names
  - Aggregates monthly baseline from historical data
  - Applies 8% YoY growth factor
  - Applies region-aware festival boosts with individual calendars:
    - South (Kerala/TN/AP) → Onam ×2.8, Pongal ×2.0
    - North (Delhi/UP) → Holi ×1.7, Diwali ×3.0
    - East (WB) → Durga Puja ×2.5
    - West (Maha/Guj) → Ganesh Chaturthi ×2.2
  - Generates monthly summary table + daily line-chart series with festival annotations
- **Output**: Chart.js line chart + monthly bar comparison (predicted vs baseline)

### State Management (`App.js`)
- Period filter state (`filterMode`, `selectedMonth`, `selectedWeek`, `selectedQuarter`) owned at App level, passed down to `StockSection` + `ActionPanel` to keep them **synchronized**
- Category change auto-refreshes chart + decisions without full reload
- Region change cascades: reset store → fetch filtered store list → reset dashboard

### API Service Layer (`frontend/src/services/api.js`)
- Axios client → `http://127.0.0.1:8000`
- Exposed functions: `getMeta()`, `getStoreCategoryForecast(storeId, category)`, `getDiscountByRegion(region)`, `getInventorySummary()`, `getStoreDecisions(storeId, category)`, `getStoresByRegion(region)`

---

## 7. Business Logic Details

### Forecast Generation (`generate_forecast.py`)
- Base demand: `categoryAverage × random(0.88, 1.12)` per store-category
- Festival boost applied per date + region:

| Festival | Boost | Regions |
|---|---|---|
| Diwali | ×2.8 | All |
| Onam | ×2.5 | South |
| Durga Puja | ×2.3 | East |
| Eid-ul-Fitr | ×1.9 | All |
| Holi | ×1.8 | North, West |
| + 10 more festivals | ×1.2–×1.6 | Varies |

- Output columns aliased for backend compatibility: `Store_ID`, `Category`, `ForecastValue`, `Festival_Name`

### Festival Season Index (FSI)
FSI encodes a demand multiplier. A raw ML uplift of 0.30 means +30%; the FSI displayed in frontend can reach ×9.5 for Onam in Kerala stores (strong localized retail effect). FSI is computed as `(boost − 1) × 100` in percentage terms for storage, then converted to a multiplier in the frontend.

### Inventory Decision Tiers (`inventory_decision_engine.py`)
Using `Inventory_Position = Current_Inventory / Reorder_Point`:

| Position | Decision |
|---|---|
| ≥1.2 | OK |
| ≥0.85 | MONITOR |
| ≥0.70 | WATCHLIST |
| ≥0.50 | REORDER SOON |
| <0.50 | REORDER NOW |

Priority Score: `CLIP(100 × (1 − Inventory_Position) + 20 / (Days_Of_Supply + 0.1), 0, 100)`

Recommended Order Qty targets 21 days of supply + safety stock above current inventory.

### Inventory KPI (`inventory_kpi.py`)
- Per-store-category: Avg_Daily_Demand, Safety_Stock (Wilson model, 95% service level), Reorder_Point, Days_Of_Supply, Stockout_Risk
- **Category risk profiles for simulation**: Electronics/Clothing → 60% well-stocked; medium → 40%; Furniture/Pet Care → 30%

### Discount Engine Evolution
| Version | Logic |
|---|---|
| Old (`discount_engine.py`) | Rule-based: FSI≥5% → NO_DISCOUNT; FSI≤0% → APPLY; else OPTIONAL |
| Current ML (`ml_pipeline.py`) | XGBoost classifier → 5-tier output → pre-aggregated weekly CSV |
| Frontend override (`StockSection.js`) | Inverse-FSI formula applied at render time to supplement API data |

---

## 8. Known Configurations & Quirks

1. **Backend never runs ML inference at request time** — it only serves pre-generated CSVs. If you regenerate output CSVs, call `POST /refresh` or restart the backend.

2. **Two App files exist**: `frontend/src/App.js` (full production version with all features) and `frontend/src/App.jsx` (simplified variant). The build uses `App.js`.

3. **Column aliasing in data_loader.py** — Multiple column name variants are silently normalised on load. If you add new CSV files, ensure at minimum `Store`, `Category`, `Date` columns exist, or update the alias map in `data_loader.py`.

4. **Festival calendar is duplicated** — It exists in `Data/festival_calender.csv`, in `generate_forecast.py` (boost dict), and hardcoded in `frontend/src/components/ForecastChart.js` (2026 dates). Changing one does not change the others.

5. **Indian store mapping** — 258 Indian stores map to Rossmann store IDs via `Store_ID % 1116 + 1`. This is intentional and means multiple Indian stores share the same Rossmann base statistics.

6. **StockSection and ActionPanel must stay in sync** — Both components independently re-derive the FSI from the same period filter state passed from `App.js`. If you change the FSI logic in one, change it in the other.

7. **Shop Owner Analytics is fully client-side** — It does not call the backend at all. Forecast generation happens in the browser via `ShopOwnerAnalytics.js`.

8. **CORS**: Backend allows `http://localhost:3000` and `http://localhost:5173`. If running frontend on a different port, update `backend/app/main.py`.

9. **`backend/app/_init_.py`** — Note the filename uses a single underscore on each side (`_init_.py`), not the standard Python double-underscore `__init__.py`. This may cause import issues if the package structure is changed.

---

## 9. File Map (Key Files Only)

```
Root
├── ml_models.py              — Trains all 5 ML models, saves to models/
├── ml_pipeline.py            — Applies models to 258 Indian stores, writes outputs/
├── generate_forecast.py      — Generates yearly_forecast_indian.csv
├── generate_indian_stores.py — Generates 258 store records
├── inventory_decision_engine.py — Rule + ML hybrid inventory decisions
├── inventory_kpi.py          — KPI computation (safety stock, reorder, stockout)
├── discount_engine.py        — Legacy rule-based discount logic
├── discount_recommendation.py— Enhanced ML-based discount output
├── discount_table.py         — Discount summary table generation
├── region_discount.py        — Per-region discount aggregation
├── generate_qrs_dataset.py   — QRS Technologies dataset generator
├── ML_DOCUMENTATION.md       — Technical ML documentation
│
backend/app/
├── main.py      — FastAPI app, all 20+ endpoints, v15.2
├── data_loader.py — DataStore singleton, CSV loading, column aliasing
├── schemas.py   — Pydantic response models
├── settings.py  — Centralised file path configuration
├── utils.py     — Shared utility functions
│
frontend/src/
├── App.js       — Main app, shared state, page router
├── App.jsx      — Simplified variant
├── services/api.js            — Axios API client
├── components/
│   ├── Sidebar.js             — Page navigation
│   ├── Header.js              — Region/store selectors
│   ├── SummaryCards.js        — 4 KPI cards
│   ├── ForecastChart.js       — Chart.js + festival overlay plugins
│   ├── StockSection.js        — FSI panel + discount intelligence
│   ├── ActionPanel.js         — Scenario-based action recommendations
│   └── ShopOwnerAnalytics.js  — Personal CSV-based forecaster (Page 2)
```

---

## 10. How to Run

```bash
# Backend
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm start
```

To regenerate all ML outputs from scratch:
```bash
# 1. Train models
python ml_models.py

# 2. Run full pipeline (Indian stores + forecasts + discounts + inventory)
python ml_pipeline.py

# 3. OR re-run individual generators
python generate_forecast.py
python inventory_kpi.py
python inventory_decision_engine.py
```

---

*Last updated: March 2026 | Backend API v15.2*
