from pydantic import BaseModel
from datetime import date
from typing import Optional, List, Dict, Any

# ---------- core ----------
class HealthResponse(BaseModel):
    status: str
    forecast_rows: int
    discount_rows: int

class MetaResponse(BaseModel):
    forecast_rows: int
    discount_rows: int
    min_date: Optional[date] = None
    max_date: Optional[date] = None
    regions: List[str]
    stores: List[int]
    categories: List[str]
    months: Optional[List[int]] = None
    years: Optional[List[int]] = None
    store_names: Optional[Dict[str, Any]] = None

class RegionsResponse(BaseModel):
    regions: List[str]

class StoresResponse(BaseModel):
    stores: List[int]

class CategoriesResponse(BaseModel):
    categories: List[str]

class ForecastPoint(BaseModel):
    date: date
    value: float
    festival: Optional[str] = None
    fsi: Optional[float] = None

class ForecastSeriesResponse(BaseModel):
    region: str
    store: Optional[int] = None
    category: Optional[str] = None
    series: List[ForecastPoint]

class DiscountPoint(BaseModel):
    week: date
    discount: float

class DiscountSeriesResponse(BaseModel):
    region: str
    series: List[DiscountPoint]

# ---------- inventory decisions ----------
class InventoryExecSummary(BaseModel):
    total: int
    reorder_now: int
    watchlist: int
    ok: int

class RegionActionRow(BaseModel):
    region: str
    reorder_now: int
    watchlist: int
    ok: int

class RegionActionsResponse(BaseModel):
    rows: List[RegionActionRow]

class StoreDecisionRow(BaseModel):
    store: int
    region: str
    category: str
    decision: str
    stockout_risk: float
    reorder_point: float
    safety_stock: float
    days_of_supply: float
    current_inventory: Optional[float] = None
    priority_score: Optional[float] = None
    recommended_order_qty: Optional[float] = None
    days_until_stockout: Optional[int] = None

class StoreDecisionsResponse(BaseModel):
    store: int
    total_rows: int
    offset: int
    limit: int
    rows: List[StoreDecisionRow]

# ---------- KPIs ----------
class KPIRegionRow(BaseModel):
    region: str
    stores: int
    avg_stockout_risk: float
    max_stockout_risk: float
    avg_reorder_point: float
    total_safety_stock: float

class KPIRegionResponse(BaseModel):
    rows: List[KPIRegionRow]


# ---------- Predictions Catalog ----------
class PredictionCreate(BaseModel):
    owner_name: str
    business_name: str
    category: str = ""
    region: str = ""
    state: str = ""
    month: int
    year: int
    predicted_sales: int = 0
    predicted_range_min: int = 0
    predicted_range_max: int = 0
    baseline_sales: int = 0
    growth_percent: float = 0.0
    discount_recommendation: str = ""
    stock_range_min: int = 0
    stock_range_max: int = 0
    demand_level: str = ""
    festival_name: Optional[str] = None
    status: str = "Draft"
    notes: str = ""
    prediction_name: str = ""

class PredictionUpdate(BaseModel):
    owner_name: Optional[str] = None
    business_name: Optional[str] = None
    category: Optional[str] = None
    region: Optional[str] = None
    state: Optional[str] = None
    month: Optional[int] = None
    year: Optional[int] = None
    predicted_sales: Optional[int] = None
    predicted_range_min: Optional[int] = None
    predicted_range_max: Optional[int] = None
    baseline_sales: Optional[int] = None
    growth_percent: Optional[float] = None
    discount_recommendation: Optional[str] = None
    stock_range_min: Optional[int] = None
    stock_range_max: Optional[int] = None
    demand_level: Optional[str] = None
    festival_name: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    prediction_name: Optional[str] = None

class PredictionResponse(BaseModel):
    id: int
    owner_name: str
    business_name: str
    category: str
    region: str
    state: str
    month: int
    year: int
    predicted_sales: int
    predicted_range_min: int
    predicted_range_max: int
    baseline_sales: int
    growth_percent: float
    discount_recommendation: str
    stock_range_min: int
    stock_range_max: int
    demand_level: str
    festival_name: Optional[str] = None
    status: str
    notes: str
    prediction_name: str
    created_at: str
    updated_at: str
    history: List[Dict[str, Any]] = []

class PredictionListResponse(BaseModel):
    predictions: List[PredictionResponse]
    total: int

class BulkDeleteRequest(BaseModel):
    ids: List[int]

class CatalogStatsResponse(BaseModel):
    total: int
    this_month: int
    status_breakdown: Dict[str, int]
    top_categories: List[Dict[str, Any]]
    region_breakdown: Dict[str, int]
