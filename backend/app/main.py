from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from datetime import date

from .data_loader import store
from .schemas import (
    HealthResponse, MetaResponse,
    RegionsResponse, StoresResponse, CategoriesResponse,
    ForecastSeriesResponse, ForecastPoint,
    DiscountSeriesResponse, DiscountPoint,
    InventoryExecSummary, RegionActionsResponse,
    StoreDecisionsResponse, StoreDecisionRow,
    KPIRegionResponse, KPIRegionRow
)

app = FastAPI(title="Seasonal Demand Forecaster API", version="14.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup():
    try:
        store.load()
        print("✅ Data loaded successfully")
        print(f"   Forecast rows: {len(store.forecast)}")
        print(f"   Discount rows: {len(store.discount)}")
        print(f"   Decisions rows: {len(store.decisions_store_category)}")
        print(f"   Regions: {store.regions}")
        print(f"   Categories: {store.categories}")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        raise

@app.get("/")
def root():
    return {
        "name": "Seasonal Demand Forecaster API",
        "version": "14.3",
        "docs": "/docs",
        "health": "/health",
        "meta": "/meta"
    }

@app.get("/health", response_model=HealthResponse)
def health():
    fc_rows = 0 if store.forecast is None else len(store.forecast)
    dc_rows = 0 if store.discount is None else len(store.discount)
    return {"status": "ok", "forecast_rows": fc_rows, "discount_rows": dc_rows}

@app.get("/meta", response_model=MetaResponse)
def meta():
    fc = store.forecast
    min_date = None
    max_date = None
    
    if fc is not None and not fc.empty:
        min_date = pd.to_datetime(fc["Date"]).min().date()
        max_date = pd.to_datetime(fc["Date"]).max().date()

    return {
        "forecast_rows": 0 if fc is None else len(fc),
        "discount_rows": 0 if store.discount is None else len(store.discount),
        "min_date": min_date,
        "max_date": max_date,
        "regions": store.regions,
        "stores": store.stores,
        "categories": store.categories,
    }

@app.post("/refresh")
def refresh():
    try:
        store.refresh()
        return {
            "status": "reloaded",
            "forecast_rows": len(store.forecast),
            "discount_rows": len(store.discount)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/regions", response_model=RegionsResponse)
def regions():
    return {"regions": store.regions}

@app.get("/stores", response_model=StoresResponse)
def stores(region: str | None = None):
    df = store.forecast
    if df is None or df.empty:
        return {"stores": []}
    if region:
        df = df[df["Region"] == region]
    stores_list = sorted(df["Store"].dropna().astype(int).unique().tolist())
    return {"stores": stores_list}

@app.get("/categories", response_model=CategoriesResponse)
def categories():
    return {"categories": store.categories}

@app.get("/forecast/region", response_model=ForecastSeriesResponse)
def forecast_region(region: str = Query(...), start: date | None = None, end: date | None = None):
    df = store.forecast
    df = df[df["Region"] == region].copy()
    if start:
        df = df[df["Date"] >= pd.Timestamp(start)]
    if end:
        df = df[df["Date"] <= pd.Timestamp(end)]
    daily = df.groupby("Date")["ForecastValue"].sum().reset_index()
    series = [ForecastPoint(date=d.date(), value=float(v)) for d, v in zip(daily["Date"], daily["ForecastValue"])]
    return {"region": region, "store": None, "category": None, "series": series}

@app.get("/forecast/store", response_model=ForecastSeriesResponse)
def forecast_store(store_id: int = Query(..., alias="store"), start: date | None = None, end: date | None = None):
    df = store.forecast
    df = df[df["Store"].astype(int) == int(store_id)].copy()
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Store {store_id} not found")
    if start:
        df = df[df["Date"] >= pd.Timestamp(start)]
    if end:
        df = df[df["Date"] <= pd.Timestamp(end)]
    daily = df.groupby(["Date", "Region"])["ForecastValue"].sum().reset_index()
    region = str(daily["Region"].iloc[0])
    series = [ForecastPoint(date=d.date(), value=float(v)) for d, v in zip(daily["Date"], daily["ForecastValue"])]
    return {"region": region, "store": store_id, "category": None, "series": series}

@app.get("/forecast/store-category", response_model=ForecastSeriesResponse)
def forecast_store_category(
    store_id: int = Query(..., alias="store"),
    category: str = Query(...),
    start: date | None = None,
    end: date | None = None,
):
    df = store.forecast
    df = df[(df["Store"].astype(int) == int(store_id)) & (df["Product_Category"].astype(str) == str(category))].copy()
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data for store {store_id}, category {category}")
    if start:
        df = df[df["Date"] >= pd.Timestamp(start)]
    if end:
        df = df[df["Date"] <= pd.Timestamp(end)]
    daily = df.groupby(["Date", "Region"])["ForecastValue"].sum().reset_index()
    region = str(daily["Region"].iloc[0]) if not daily.empty else "Unknown"
    series = [ForecastPoint(date=d.date(), value=float(v)) for d, v in zip(daily["Date"], daily["ForecastValue"])]
    return {"region": region, "store": store_id, "category": category, "series": series}

@app.get("/discount/region", response_model=DiscountSeriesResponse)
def discount_region(region: str = Query(...)):
    dc = store.discount
    if dc is None or dc.empty:
        return {"region": region, "series": []}
    sub = dc[dc["Region"] == region].copy()
    if sub.empty:
        return {"region": region, "series": []}
    sub = sub.sort_values("Week")
    series = [DiscountPoint(week=w.date(), discount=float(d)) for w, d in zip(sub["Week"], sub["RecommendedDiscount"])]
    return {"region": region, "series": series}

@app.get("/inventory/exec-summary", response_model=InventoryExecSummary)
def inventory_exec_summary():
    df = store.decisions_store_category
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="Decision data not loaded")
    dec = df["Decision"].astype(str).str.upper()
    return {
        "total": int(len(df)),
        "reorder_now": int((dec == "REORDER NOW").sum()),
        "watchlist": int(dec.isin(["WATCHLIST", "MONITOR", "REORDER SOON"]).sum()),
        "ok": int((dec == "OK").sum()),
    }

@app.get("/inventory/region-actions", response_model=RegionActionsResponse)
def inventory_region_actions():
    df = store.decisions_store_category
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="Decision data not loaded")
    tmp = df.copy()
    tmp["Region"] = tmp["Region"].astype(str)
    tmp["Decision"] = tmp["Decision"].astype(str).str.upper()
    rows = []
    for reg, sub in tmp.groupby("Region"):
        rows.append({
            "region": reg,
            "reorder_now": int((sub["Decision"] == "REORDER NOW").sum()),
            "watchlist": int(sub["Decision"].isin(["WATCHLIST", "MONITOR", "REORDER SOON"]).sum()),
            "ok": int((sub["Decision"] == "OK").sum()),
        })
    return {"rows": rows}

@app.get("/inventory/store-decisions", response_model=StoreDecisionsResponse)
def inventory_store_decisions(
    store_id: int = Query(..., alias="store"),
    decision: str | None = None,
    category: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    df = store.decisions_store_category
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="Decision data not loaded")
    sub = df[df["Store"].astype(int) == int(store_id)].copy()
    if sub.empty:
        raise HTTPException(status_code=404, detail=f"No data for store {store_id}")
    if decision:
        sub = sub[sub["Decision"].astype(str).str.upper() == decision.upper()]
    if category:
        sub = sub[sub["Category"].astype(str) == str(category)]
    total_rows = len(sub)
    sub = sub.sort_values(["Decision", "Stockout_Risk"], ascending=[True, False], na_position="last")
    page = sub.iloc[offset: offset + limit].copy()
    rows = []
    for _, r in page.iterrows():
        rows.append(StoreDecisionRow(
            store=int(r["Store"]),
            region=str(r["Region"]),
            category=str(r["Category"]),
            decision=str(r["Decision"]),
            stockout_risk=float(r.get("Stockout_Risk", 0.0)),
            reorder_point=float(r.get("Reorder_Point", 0.0)),
            safety_stock=float(r.get("Safety_Stock", 0.0)),
            days_of_supply=float(r.get("Days_Of_Supply", r.get("DaysOfSupply", 0.0))),
        ))
    return {"store": store_id, "total_rows": total_rows, "offset": offset, "limit": limit, "rows": rows}

@app.get("/kpi/region-summary", response_model=KPIRegionResponse)
def kpi_region_summary():
    df = store.kpi_region_summary
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="KPI data not loaded")
    rows = []
    for _, r in df.iterrows():
        rows.append(KPIRegionRow(
            region=str(r.get("Region", "")),
            stores=int(r.get("Stores", 0)),
            avg_stockout_risk=float(r.get("Avg_Stockout_Risk", 0.0)),
            max_stockout_risk=float(r.get("Max_Stockout_Risk", 0.0)),
            avg_reorder_point=float(r.get("Avg_Reorder_Point", 0.0)),
            total_safety_stock=float(r.get("Total_Safety_Stock", 0.0)),
        ))
    return {"rows": rows}

@app.get("/debug/data-status")
def debug_data_status():
    return {
        "forecast_loaded": store.forecast is not None,
        "forecast_rows": len(store.forecast) if store.forecast is not None else 0,
        "discount_loaded": store.discount is not None,
        "discount_rows": len(store.discount) if store.discount is not None else 0,
        "decisions_loaded": store.decisions_store_category is not None,
        "decisions_rows": len(store.decisions_store_category) if store.decisions_store_category is not None else 0,
        "kpi_loaded": store.kpi_region_summary is not None,
        "kpi_rows": len(store.kpi_region_summary) if store.kpi_region_summary is not None else 0,
        "regions": store.regions,
        "categories": store.categories,
    }