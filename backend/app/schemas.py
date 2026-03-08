from pydantic import BaseModel
from datetime import date
from typing import Optional, List

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

class RegionsResponse(BaseModel):
    regions: List[str]

class StoresResponse(BaseModel):
    stores: List[int]

class CategoriesResponse(BaseModel):
    categories: List[str]

class ForecastPoint(BaseModel):
    date: date
    value: float

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
