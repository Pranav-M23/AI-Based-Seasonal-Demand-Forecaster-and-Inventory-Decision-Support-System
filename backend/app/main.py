"""
Enhanced Seasonal Demand Forecaster API
Version 15.2 - With Indian stores, month filtering, and enhanced recommendations
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from datetime import date
from typing import Optional

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

app = FastAPI(
    title="Seasonal Demand Forecaster API - Enhanced",
    version="15.2",
    description="Enhanced API with Indian stores, month filtering, and comprehensive recommendations"
)

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
        
        # Load enhanced data if available
        try:
            store.actions = pd.read_csv('../../outputs/action_recommendations_enhanced.csv')
            print(f"   ✅ Actions rows: {len(store.actions)}")
        except:
            store.actions = None
            print(f"   ⚠️  Enhanced actions not loaded (optional)")
            
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        raise

@app.get("/")
def root():
    return {
        "name": "Seasonal Demand Forecaster API - Enhanced",
        "version": "15.2",
        "features": [
            "Indian stores with realistic names",
            "State-level regional data",
            "Month/Year filtering",
            "Enhanced action recommendations",
            "Festival Season Index (FSI)",
            "Category-specific insights"
        ],
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
    """Enhanced metadata with months and years"""
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
        "months": list(range(1, 13)),  # 1-12
        "years": [2026],  # Available years
        "store_names": {}  # Will be populated if Store_Name column exists
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
def stores(region: str | None = None, state: str | None = None):
    """Get stores with optional region/state filtering"""
    df = store.forecast
    if df is None or df.empty:
        return {"stores": []}
    
    if region:
        df = df[df["Region"] == region]
    
    # Support state filtering if State column exists
    if state and "State" in df.columns:
        df = df[df["State"] == state]
    
    stores_list = sorted(df["Store"].dropna().astype(int).unique().tolist())
    return {"stores": stores_list}

@app.get("/categories", response_model=CategoriesResponse)
def categories():
    return {"categories": store.categories}

# ============================================================================
# ENHANCED FORECAST ENDPOINTS WITH MONTH/YEAR FILTERING
# ============================================================================

@app.get("/forecast/region", response_model=ForecastSeriesResponse)
def forecast_region(
    region: str = Query(...),
    start: date | None = None,
    end: date | None = None,
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2025, le=2030)
):
    """Regional forecast with optional month/year filtering"""
    df = store.forecast
    df = df[df["Region"] == region].copy()
    
    if start:
        df = df[df["Date"] >= pd.Timestamp(start)]
    if end:
        df = df[df["Date"] <= pd.Timestamp(end)]
    
    # Month/Year filtering
    if month or year:
        df["_date"] = pd.to_datetime(df["Date"])
        if month:
            df = df[df["_date"].dt.month == month]
        if year:
            df = df[df["_date"].dt.year == year]
    
    daily = df.groupby("Date")["ForecastValue"].sum().reset_index()
    series = [ForecastPoint(date=d.date(), value=float(v)) for d, v in zip(daily["Date"], daily["ForecastValue"])]
    return {"region": region, "store": None, "category": None, "series": series}

@app.get("/forecast/store", response_model=ForecastSeriesResponse)
def forecast_store(
    store_id: int = Query(..., alias="store"),
    start: date | None = None,
    end: date | None = None,
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2025, le=2030)
):
    """Store forecast with optional month/year filtering"""
    df = store.forecast
    df = df[df["Store"].astype(int) == int(store_id)].copy()
    
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Store {store_id} not found")
    
    if start:
        df = df[df["Date"] >= pd.Timestamp(start)]
    if end:
        df = df[df["Date"] <= pd.Timestamp(end)]
    
    # Month/Year filtering
    if month or year:
        df["_date"] = pd.to_datetime(df["Date"])
        if month:
            df = df[df["_date"].dt.month == month]
        if year:
            df = df[df["_date"].dt.year == year]
    
    daily = df.groupby(["Date", "Region"])["ForecastValue"].sum().reset_index()
    region = str(daily["Region"].iloc[0]) if not daily.empty else "Unknown"
    series = [ForecastPoint(date=d.date(), value=float(v)) for d, v in zip(daily["Date"], daily["ForecastValue"])]
    return {"region": region, "store": store_id, "category": None, "series": series}

@app.get("/forecast/store-category", response_model=ForecastSeriesResponse)
def forecast_store_category(
    store_id: int = Query(..., alias="store"),
    category: str = Query(...),
    start: date | None = None,
    end: date | None = None,
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2025, le=2030)
):
    """
    Store-category forecast with month/year filtering
    Enhanced to support FSI and festival data if available
    """
    df = store.forecast
    
    # Handle "All" category - sum across all categories
    if category == "All":
        df = df[df["Store"].astype(int) == int(store_id)].copy()
    else:
        df = df[(df["Store"].astype(int) == int(store_id)) & (df["Product_Category"].astype(str) == str(category))].copy()
    
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data for store {store_id}, category {category}")
    
    if start:
        df = df[df["Date"] >= pd.Timestamp(start)]
    if end:
        df = df[df["Date"] <= pd.Timestamp(end)]
    
    # Month/Year filtering
    if month or year:
        df["_date"] = pd.to_datetime(df["Date"])
        if month:
            df = df[df["_date"].dt.month == month]
        if year:
            df = df[df["_date"].dt.year == year]
    
    # Group and include festival data if available
    if "Festival_Name" in df.columns and "FSI" in df.columns:
        daily = df.groupby(["Date", "Region"]).agg({
            "ForecastValue": "sum",
            "Festival_Name": "first",
            "FSI": "max"
        }).reset_index()
    else:
        daily = df.groupby(["Date", "Region"])["ForecastValue"].sum().reset_index()
    
    region = str(daily["Region"].iloc[0]) if not daily.empty else "Unknown"
    
    # Build series with enhanced data
    series = []
    for _, row in daily.iterrows():
        point = {
            "date": row["Date"].date() if hasattr(row["Date"], 'date') else row["Date"],
            "value": float(row["ForecastValue"])
        }
        
        # Add festival info if available
        if "Festival_Name" in row and pd.notna(row["Festival_Name"]):
            point["festival"] = str(row["Festival_Name"])
        if "FSI" in row:
            point["fsi"] = float(row["FSI"])
        
        series.append(ForecastPoint(**point))
    
    return {"region": region, "store": store_id, "category": category, "series": series}

# ============================================================================
# DISCOUNT ENDPOINTS
# ============================================================================

@app.get("/discount/region", response_model=DiscountSeriesResponse)
def discount_region(region: str = Query(...)):
    """Regional discount recommendations"""
    dc = store.discount
    if dc is None or dc.empty:
        return {"region": region, "series": []}
    
    sub = dc[dc["Region"] == region].copy()
    if sub.empty:
        return {"region": region, "series": []}
    
    sub = sub.sort_values("Week")
    series = [DiscountPoint(week=w.date(), discount=float(d)) for w, d in zip(sub["Week"], sub["RecommendedDiscount"])]
    return {"region": region, "series": series}

@app.get("/discount/store-month")
def discount_store_month(
    store_id: int = Query(..., alias="store"),
    month: int | None = Query(None, ge=1, le=12),
    category: str | None = None
):
    """
    Get discount recommendations for specific store/month/category
    NEW ENDPOINT for enhanced discount data
    """
    try:
        # Try to load enhanced discount file
        discount_enhanced = pd.read_csv('../../outputs/discount_recommendations_enhanced.csv')
        
        df = discount_enhanced[discount_enhanced['Store_ID'] == store_id].copy()
        
        if month:
            df = df[df['Month'] == month]
        
        if category and category != "All":
            df = df[df['Category'] == category]
        
        if df.empty:
            return {"store": store_id, "month": month, "recommendations": []}
        
        return {
            "store": store_id,
            "month": month,
            "category": category,
            "recommendations": df.to_dict('records')
        }
    except FileNotFoundError:
        # Fallback to region-based discount
        return {"store": store_id, "month": month, "recommendations": [], "note": "Enhanced discounts not available"}

# ============================================================================
# INVENTORY ENDPOINTS
# ============================================================================

@app.get("/inventory/exec-summary", response_model=InventoryExecSummary)
def inventory_exec_summary():
    """Executive summary of inventory across all stores"""
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
    """Inventory actions breakdown by region"""
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
    """
    Get inventory decisions for specific store
    Enhanced with current_inventory field
    """
    df = store.decisions_store_category
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="Decision data not loaded")
    
    sub = df[df["Store"].astype(int) == int(store_id)].copy()
    
    if sub.empty:
        raise HTTPException(status_code=404, detail=f"No data for store {store_id}")
    
    if decision:
        sub = sub[sub["Decision"].astype(str).str.upper() == decision.upper()]
    
    if category and category != "All":
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
            current_inventory=float(r.get("Current_Stock", r.get("Current_Inventory", 0.0))),  # Enhanced field
            priority_score=float(r.get("Priority_Score", 0.0)),
            recommended_order_qty=float(r.get("Recommended_Order_Qty", 0.0)),
            days_until_stockout=int(r.get("Days_Until_Stockout", 0)) if pd.notna(r.get("Days_Until_Stockout")) else None
        ))
    
    return {"store": store_id, "total_rows": total_rows, "offset": offset, "limit": limit, "rows": rows}

# ============================================================================
# NEW ENHANCED ENDPOINTS
# ============================================================================

@app.get("/actions/store")
def get_actions_for_store(
    store_id: int = Query(..., alias="store"),
    category: str | None = None,
    priority: str | None = Query(None, regex="^(CRITICAL|HIGH|MEDIUM|INFO)$")
):
    """
    Get enhanced action recommendations for store
    NEW ENDPOINT
    
    Returns: Comprehensive action recommendations including:
    - Stock reorder alerts
    - Overstock warnings
    - Category-specific tips
    - Discount recommendations
    - Seasonal insights
    """
    if store.actions is None:
        # Fallback to basic recommendations from inventory decisions
        df = store.decisions_store_category
        if df is None or df.empty:
            return {"store": store_id, "actions": []}
        
        sub = df[df["Store"].astype(int) == store_id].copy()
        
        if category and category != "All":
            sub = sub[sub["Category"] == category]
        
        # Generate basic actions
        actions = []
        for _, row in sub.iterrows():
            if row["Decision"] == "REORDER NOW":
                actions.append({
                    "priority": "CRITICAL",
                    "type": "Reorder",
                    "category": row["Category"],
                    "message": f"Order immediately - low stock in {row['Category']}"
                })
        
        return {"store": store_id, "total": len(actions), "actions": actions}
    
    # Use enhanced actions if available
    df = store.actions[store.actions['Store_ID'] == store_id].copy()
    
    if category and category != "All":
        df = df[df['Category'] == category]
    
    if priority:
        df = df[df['Priority'] == priority]
    
    # Sort by priority
    priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'INFO': 3}
    df['priority_rank'] = df['Priority'].map(priority_order)
    df = df.sort_values('priority_rank')
    
    actions = df[['Priority', 'Action_Type', 'Category', 'Recommendation']].to_dict('records')
    
    return {
        "store": store_id,
        "category": category,
        "total": len(actions),
        "actions": actions
    }

@app.get("/kpi/store")
def get_store_kpi(store_id: int = Query(..., alias="store")):
    """
    Get KPIs for specific store
    NEW ENDPOINT
    """
    df = store.decisions_store_category
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="Inventory data not loaded")
    
    inv = df[df["Store"].astype(int) == store_id]
    
    if inv.empty:
        raise HTTPException(status_code=404, detail=f"Store {store_id} not found")
    
    return {
        "store": store_id,
        "total_categories": int(len(inv)),
        "avg_days_supply": round(float(inv['Days_Of_Supply'].mean()), 1),
        "low_stock_items": int((inv['Decision'].isin(['REORDER NOW', 'REORDER SOON'])).sum()),
        "total_current_stock": round(float(inv.get('Current_Stock', inv.get('Current_Inventory', pd.Series([0]))).sum()), 0),
        "total_reorder_point": round(float(inv['Reorder_Point'].sum()), 0),
        "critical_items": int((inv['Decision'] == 'REORDER NOW').sum()),
        "healthy_items": int((inv['Decision'] == 'OK').sum())
    }

# ============================================================================
# KPI & DEBUG ENDPOINTS
# ============================================================================

@app.get("/kpi/region-summary", response_model=KPIRegionResponse)
def kpi_region_summary():
    """Regional KPI summary"""
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
    """Debug endpoint to check data loading status"""
    return {
        "forecast_loaded": store.forecast is not None,
        "forecast_rows": len(store.forecast) if store.forecast is not None else 0,
        "discount_loaded": store.discount is not None,
        "discount_rows": len(store.discount) if store.discount is not None else 0,
        "decisions_loaded": store.decisions_store_category is not None,
        "decisions_rows": len(store.decisions_store_category) if store.decisions_store_category is not None else 0,
        "kpi_loaded": store.kpi_region_summary is not None,
        "kpi_rows": len(store.kpi_region_summary) if store.kpi_region_summary is not None else 0,
        "actions_loaded": hasattr(store, 'actions') and store.actions is not None,
        "actions_rows": len(store.actions) if hasattr(store, 'actions') and store.actions is not None else 0,
        "regions": store.regions,
        "categories": store.categories,
        "stores_count": len(store.stores) if store.stores else 0
    }