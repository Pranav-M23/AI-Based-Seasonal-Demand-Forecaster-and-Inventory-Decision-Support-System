import os
import pandas as pd
import numpy as np

from .settings import settings
from .utils import to_dt, norm_region, pick_col, week_start_monday, safe_float

class DataStore:
    def __init__(self):
        self.forecast = None
        self.discount = None
        self.loaded = False
        self.categories = []

        # Inventory decision outputs
        self.decisions_store_category = None
        self.exec_summary = None
        
        # KPI Data
        self.kpi_region_summary = None

    def load(self):
        # ---------- Forecast ----------
        if not os.path.exists(settings.FORECAST_FILE):
            raise FileNotFoundError(f"Missing forecast file: {settings.FORECAST_FILE}")

        fc = pd.read_csv(settings.FORECAST_FILE)

        date_col = pick_col(fc, ["Date"])
        if not date_col:
            raise KeyError("Forecast CSV must have a Date column.")

        if "Store" not in fc.columns:
            raise KeyError("Forecast CSV must have Store column.")

        fc[date_col] = to_dt(fc[date_col])
        fc = fc.dropna(subset=[date_col]).copy()
        fc = fc.rename(columns={date_col: "Date"})

        # normalize region
        if "Region" in fc.columns:
            fc["Region"] = fc["Region"].apply(norm_region)
        else:
            fc["Region"] = "Pan-India"

        # choose forecast value column
        value_col = pick_col(fc, ["ForecastValue", "Adjusted_Forecast", "Baseline_Forecast", "Predicted_Sales", "Demand"])
        if not value_col:
            raise KeyError("No usable forecast column found.")

        if value_col != "ForecastValue":
            fc = fc.rename(columns={value_col: "ForecastValue"})

        # category (optional) - handle missing Product_Category
        if "Product_Category" not in fc.columns:
            fc["Product_Category"] = "All"

        # keep essentials
        keep = ["Date", "Store", "Region", "Product_Category", "ForecastValue"]
        for extra in ["Festival_Weight", "Festival_List", "Adjusted_Forecast", "Baseline_Forecast"]:
            if extra in fc.columns and extra not in keep:
                keep.append(extra)

        fc = fc[keep].copy()

        # cache categories
        self.categories = sorted(fc["Product_Category"].dropna().astype(str).unique().tolist())

        self.forecast = fc

        # ---------- Discount ----------
        if os.path.exists(settings.DISCOUNT_FILE):
            dc = pd.read_csv(settings.DISCOUNT_FILE)

            if "Region" not in dc.columns:
                rc = pick_col(dc, ["Region"])
                if rc:
                    dc = dc.rename(columns={rc: "Region"})
                else:
                    dc["Region"] = "Pan-India"

            dc["Region"] = dc["Region"].apply(norm_region)

            # Find discount column
            disc_col = None
            for c in dc.columns:
                if "discount" in str(c).lower():
                    disc_col = c
                    break

            # Find week column
            week_col = pick_col(dc, ["Week", "WeekStart", "week_start", "Date"])
            if not week_col:
                for c in dc.columns:
                    if "week" in str(c).lower() or "date" in str(c).lower():
                        week_col = c
                        break

            if disc_col and week_col:
                dc[week_col] = to_dt(dc[week_col])
                dc = dc.dropna(subset=[week_col]).copy()

                dc["Week"] = week_start_monday(dc[week_col])
                dc["RecommendedDiscount"] = dc[disc_col].apply(lambda x: safe_float(x, 0.0))

                # CRITICAL: Deduplicate to one row per (Region, Week)
                dc = dc.groupby(["Region", "Week"], as_index=False)["RecommendedDiscount"].mean()
                dc = dc[["Region", "Week", "RecommendedDiscount"]].copy()
            else:
                dc = pd.DataFrame(columns=["Region", "Week", "RecommendedDiscount"])
        else:
            dc = pd.DataFrame(columns=["Region", "Week", "RecommendedDiscount"])

        self.discount = dc

        # ---------- Inventory decision outputs ----------
        inv_sc_path = settings.DECISIONS_STORE_CATEGORY
        inv_exec_path = settings.DECISION_EXEC_SUMMARY

        if os.path.exists(inv_sc_path):
            dsc = pd.read_csv(inv_sc_path)
            
            print(f"📋 Loaded decisions file with columns: {list(dsc.columns)}")
            
            # CRITICAL FIX: Normalize column names
            # Step 1: Rename Product_Category -> Category
            if "Product_Category" in dsc.columns:
                dsc = dsc.rename(columns={"Product_Category": "Category"})
                print(f"   ✅ Renamed 'Product_Category' → 'Category'")
            elif "Category" not in dsc.columns:
                dsc["Category"] = "All"
                print(f"   ⚠️  No category column found, created 'Category' = 'All'")
            
            # Step 2: Rename Action -> Decision
            if "Action" in dsc.columns:
                dsc = dsc.rename(columns={"Action": "Decision"})
                print(f"   ✅ Renamed 'Action' → 'Decision'")
            elif "Decision" not in dsc.columns:
                dsc["Decision"] = "UNKNOWN"
                print(f"   ⚠️  No action/decision column found, created 'Decision' = 'UNKNOWN'")
            
            # Verify required columns exist
            required = ["Store", "Region", "Category", "Decision"]
            missing = [col for col in required if col not in dsc.columns]
            if missing:
                print(f"   ⚠️  WARNING: Missing columns after renaming: {missing}")
            else:
                print(f"   ✅ All required columns present: {required}")
            
            # Normalize Region column
            if "Region" in dsc.columns:
                dsc["Region"] = dsc["Region"].apply(norm_region)
            
            self.decisions_store_category = dsc
            print(f"   ✅ Decisions loaded: {len(dsc)} rows")
        else:
            print(f"   ❌ Decisions file not found: {inv_sc_path}")
            self.decisions_store_category = pd.DataFrame()

        if os.path.exists(inv_exec_path):
            self.exec_summary = pd.read_csv(inv_exec_path)
        else:
            self.exec_summary = pd.DataFrame()

        # ---------- KPI Load ----------
        kpi_path = settings.KPI_REGION_SUMMARY
        if os.path.exists(kpi_path):
            self.kpi_region_summary = pd.read_csv(kpi_path)
            print(f"📊 Loaded KPI data: {len(self.kpi_region_summary)} regions")
        else:
            self.kpi_region_summary = pd.DataFrame()

        self.loaded = True
        print(f"✅ Data loading complete!")

    def refresh(self):
        self.load()

    # --- Properties for /meta endpoint ---
    @property
    def regions(self):
        if self.forecast is None or self.forecast.empty:
            return []
        return sorted(self.forecast["Region"].dropna().unique().tolist())

    @property
    def stores(self):
        if self.forecast is None or self.forecast.empty:
            return []
        s_list = self.forecast["Store"].astype(str).str.strip()
        s_list = s_list[s_list != ""].unique().tolist()
        try:
            return sorted([int(float(s)) for s in s_list])
        except ValueError:
            return sorted(s_list)

store = DataStore()