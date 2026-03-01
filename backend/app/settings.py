import os
from dataclasses import dataclass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
ROOT_DIR = os.path.dirname(BASE_DIR)  # project root

@dataclass(frozen=True)
class Settings:
    FORECAST_FILE: str = os.path.join(ROOT_DIR, "outputs", "yearly_festival_adjusted_region.csv")
    DISCOUNT_FILE: str = os.path.join(ROOT_DIR, "outputs", "region_discount_recommendations.csv")

    KPI_REGION_SUMMARY: str = os.path.join(ROOT_DIR, "outputs", "inventory_kpi_region_summary.csv")
    KPI_REGION_CATEGORY: str = os.path.join(ROOT_DIR, "outputs", "inventory_kpi_region_category_summary.csv")
    KPI_STORE_LEVEL: str = os.path.join(ROOT_DIR, "outputs", "inventory_kpi_store_level.csv")
    KPI_STORE_CATEGORY: str = os.path.join(ROOT_DIR, "outputs", "inventory_kpi_store_category.csv")

    DECISIONS_STORE_CATEGORY: str = os.path.join(ROOT_DIR, "outputs", "inventory_decisions_store_category.csv")
    DECISION_EXEC_SUMMARY: str = os.path.join(ROOT_DIR, "outputs", "inventory_decision_executive_summary.csv")

settings = Settings()

