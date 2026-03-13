"""
Enhanced Data Loader for Seasonal Demand Forecaster
Supports both old and new (Indian stores) data formats
"""

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
        
        # Enhanced data (optional)
        self.actions = None  # Enhanced action recommendations
        self.store_names = {}  # Store ID -> Name mapping

    def load(self):
        """Load all data with support for enhanced Indian stores format"""
        
        print("\n" + "="*70)
        print("LOADING DATA - ENHANCED MODE")
        print("="*70)
        
        # ---------- Forecast ----------
        print("\n📊 Loading Forecast Data...")
        
        # Try new format first
        new_forecast_file = os.path.join(os.path.dirname(settings.FORECAST_FILE), "yearly_forecast_indian.csv")
        
        if os.path.exists(new_forecast_file):
            print(f"   ✅ Found NEW Indian stores forecast: {new_forecast_file}")
            fc = pd.read_csv(new_forecast_file, low_memory=False)
            
            # Map new columns to expected format
            column_mapping = {
                'Store_ID': 'Store',
                'Store_Name': 'StoreName',
                'Category': 'Product_Category',
                'Adjusted': 'ForecastValue',
                'Adjusted_Forecast': 'ForecastValue',
                'Baseline': 'Baseline_Forecast'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in fc.columns and new_col not in fc.columns:
                    fc = fc.rename(columns={old_col: new_col})
                    print(f"      Mapped: {old_col} → {new_col}")
            
            # If both Store_ID and Store columns exist, fill NaN Store values with Store_ID
            if 'Store_ID' in fc.columns and 'Store' in fc.columns:
                fc['Store'] = fc['Store'].fillna(fc['Store_ID'])
            
            # Ensure Store column is integer
            if 'Store' in fc.columns:
                fc['Store'] = fc['Store'].astype(float).astype('Int64')

            # If StoreName has NaN rows but Store_Name exists, fill from Store_Name
            if 'StoreName' in fc.columns and 'Store_Name' in fc.columns:
                fc['StoreName'] = fc['StoreName'].fillna(fc['Store_Name'])

            # Ensure ForecastValue exists
            if 'ForecastValue' not in fc.columns:
                if 'Adjusted_Forecast' in fc.columns:
                    fc['ForecastValue'] = fc['Adjusted_Forecast']
                elif 'Adjusted' in fc.columns:
                    fc['ForecastValue'] = fc['Adjusted']
                elif 'Baseline_Forecast' in fc.columns:
                    fc['ForecastValue'] = fc['Baseline_Forecast']
            
            # Store name mapping - merge Store_Name and StoreName sources
            name_col = 'StoreName' if 'StoreName' in fc.columns else ('Store_Name' if 'Store_Name' in fc.columns else None)
            if name_col:
                valid_names = fc[['Store', name_col]].dropna(subset=[name_col])
                if not valid_names.empty:
                    self.store_names = {
                        int(k): v
                        for k, v in valid_names.drop_duplicates('Store').set_index('Store')[name_col].to_dict().items()
                    }
                print(f"      ✅ Loaded {len(self.store_names)} store names")
            
        else:
            # Fallback to old format
            print(f"   ⚠️  New format not found, loading old format: {settings.FORECAST_FILE}")
            
            if not os.path.exists(settings.FORECAST_FILE):
                raise FileNotFoundError(f"Missing forecast file: {settings.FORECAST_FILE}")
            
            fc = pd.read_csv(settings.FORECAST_FILE)

        # Common processing for both formats
        date_col = pick_col(fc, ["Date"])
        if not date_col:
            raise KeyError("Forecast CSV must have a Date column.")

        if "Store" not in fc.columns:
            raise KeyError("Forecast CSV must have Store column.")

        fc[date_col] = to_dt(fc[date_col])
        fc = fc.dropna(subset=[date_col]).copy()
        fc = fc.rename(columns={date_col: "Date"})

        # Normalize region
        if "Region" in fc.columns:
            fc["Region"] = fc["Region"].apply(norm_region)
        else:
            fc["Region"] = "Pan-India"

        # Choose forecast value column
        if "ForecastValue" not in fc.columns:
            value_col = pick_col(fc, ["Adjusted_Forecast", "Baseline_Forecast", "Predicted_Sales", "Demand"])
            if not value_col:
                raise KeyError("No usable forecast column found.")
            fc = fc.rename(columns={value_col: "ForecastValue"})

        # Category (optional)
        if "Product_Category" not in fc.columns:
            fc["Product_Category"] = "All"

        # Keep essentials + optional enhanced fields
        keep = ["Date", "Store", "Region", "Product_Category", "ForecastValue"]
        
        # Keep optional enhanced fields if present
        optional_fields = [
            "Festival_Weight", "Festival_List", "Festival_Name", "FSI",
            "Adjusted_Forecast", "Baseline_Forecast", "State", "StoreName",
            "Month", "Year", "Week"
        ]
        for field in optional_fields:
            if field in fc.columns and field not in keep:
                keep.append(field)

        fc = fc[keep].copy()

        # Cache categories (including "All" if not present)
        cats = sorted(fc["Product_Category"].dropna().astype(str).unique().tolist())
        if "All" not in cats:
            cats = ["All"] + cats
        self.categories = cats

        self.forecast = fc
        print(f"   ✅ Forecast loaded: {len(fc):,} rows")
        print(f"      Regions: {len(fc['Region'].unique())}")
        print(f"      Stores: {len(fc['Store'].unique())}")
        print(f"      Categories: {len(self.categories)}")
        
        # Show sample of enhanced fields if present
        if "Festival_Name" in fc.columns:
            festival_count = fc['Festival_Name'].notna().sum()
            print(f"      ✨ Festival data: {festival_count:,} records with festivals")
        if "FSI" in fc.columns:
            max_fsi = fc['FSI'].max()
            print(f"      ✨ FSI (Festival Season Index): Max {max_fsi}%")

        # ---------- Discount ----------
        print("\n💰 Loading Discount Data...")
        
        discount_loaded = False
        
        # Try the pre-computed weekly region discount file first (fastest path)
        weekly_discount_file = os.path.join(os.path.dirname(settings.DISCOUNT_FILE), "region_discount_recommendations.csv")
        
        if os.path.exists(weekly_discount_file):
            print(f"   ✅ Found weekly region discounts: {weekly_discount_file}")
            dc = pd.read_csv(weekly_discount_file)
            
            if "Region" in dc.columns and "Week" in dc.columns and "Recommended_Discount" in dc.columns:
                dc["Region"] = dc["Region"].apply(norm_region)
                dc["Week"] = pd.to_datetime(dc["Week"], errors="coerce")
                dc = dc.dropna(subset=["Week"])
                dc["RecommendedDiscount"] = dc["Recommended_Discount"].apply(lambda x: safe_float(x, 0.0))
                dc = dc[["Region", "Week", "RecommendedDiscount"]].copy()
                discount_loaded = True
                print(f"      Loaded {len(dc):,} weekly discount records")
        
        if not discount_loaded and os.path.exists(settings.DISCOUNT_FILE):
            print(f"   ✅ Loading standard discounts: {settings.DISCOUNT_FILE}")
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

                # Deduplicate to one row per (Region, Week)
                dc = dc.groupby(["Region", "Week"], as_index=False)["RecommendedDiscount"].mean()
                dc = dc[["Region", "Week", "RecommendedDiscount"]].copy()
                discount_loaded = True
            else:
                dc = pd.DataFrame(columns=["Region", "Week", "RecommendedDiscount"])
        
        if not discount_loaded:
            dc = pd.DataFrame(columns=["Region", "Week", "RecommendedDiscount"])

        self.discount = dc
        
        if discount_loaded and len(dc) > 0:
            non_zero = (dc['RecommendedDiscount'] > 0).sum()
            avg_discount = dc[dc['RecommendedDiscount'] > 0]['RecommendedDiscount'].mean()
            print(f"   ✅ Discounts loaded: {len(dc):,} records")
            print(f"      Non-zero discounts: {non_zero} ({non_zero/len(dc)*100:.1f}%)")
            print(f"      Average discount: {avg_discount:.1f}%")
        else:
            print(f"   ⚠️  No discount data loaded")

        # ---------- Inventory Decisions ----------
        print("\n📦 Loading Inventory Decisions...")
        
        # Try new format first
        new_inventory_file = os.path.join(os.path.dirname(settings.DECISIONS_STORE_CATEGORY), "inventory_decisions_indian.csv")
        
        if os.path.exists(new_inventory_file):
            print(f"   ✅ Found NEW inventory: {new_inventory_file}")
            dsc = pd.read_csv(new_inventory_file)
        elif os.path.exists(settings.DECISIONS_STORE_CATEGORY):
            print(f"   ✅ Loading standard inventory: {settings.DECISIONS_STORE_CATEGORY}")
            dsc = pd.read_csv(settings.DECISIONS_STORE_CATEGORY)
        else:
            print(f"   ❌ No inventory file found")
            dsc = pd.DataFrame()

        if not dsc.empty:
            print(f"      Columns before mapping: {list(dsc.columns)}")
            
            # CRITICAL: Column mapping for compatibility
            column_mapping = {
                'Store_ID': 'Store',
                'Product_Category': 'Category',
                'Action': 'Decision',
                'Current_Stock': 'Current_Inventory',
                'Days_Of_Supply': 'DaysOfSupply'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in dsc.columns and new_col not in dsc.columns:
                    dsc = dsc.rename(columns={old_col: new_col})
                    print(f"      ✅ Mapped: {old_col} → {new_col}")
            
            # Ensure critical columns exist
            if "Category" not in dsc.columns:
                dsc["Category"] = "All"
                print(f"      ⚠️  Created 'Category' = 'All'")
            
            if "Decision" not in dsc.columns and "Action" in dsc.columns:
                dsc["Decision"] = dsc["Action"]
                print(f"      ✅ Used 'Action' as 'Decision'")
            
            # Normalize Region
            if "Region" in dsc.columns:
                dsc["Region"] = dsc["Region"].apply(norm_region)
            
            # Verify required columns
            required = ["Store", "Region", "Category", "Decision"]
            missing = [col for col in required if col not in dsc.columns]
            
            if missing:
                print(f"      ❌ ERROR: Missing columns: {missing}")
            else:
                print(f"      ✅ All required columns present")
            
            self.decisions_store_category = dsc
            
            # Summary stats
            decision_counts = dsc['Decision'].value_counts().to_dict()
            print(f"   ✅ Inventory loaded: {len(dsc):,} records")
            print(f"      Decision breakdown:")
            for decision, count in sorted(decision_counts.items(), key=lambda x: -x[1])[:5]:
                print(f"         {decision}: {count}")
            
            # Check for current stock
            stock_col = 'Current_Inventory' if 'Current_Inventory' in dsc.columns else 'Current_Stock'
            if stock_col in dsc.columns:
                non_zero_stock = (dsc[stock_col] > 0).sum()
                avg_stock = dsc[dsc[stock_col] > 0][stock_col].mean()
                print(f"      📊 Stock levels:")
                print(f"         Non-zero stock: {non_zero_stock} ({non_zero_stock/len(dsc)*100:.1f}%)")
                print(f"         Average stock: {avg_stock:.0f} units")
        else:
            self.decisions_store_category = pd.DataFrame()

        # Executive summary (optional)
        if os.path.exists(settings.DECISION_EXEC_SUMMARY):
            self.exec_summary = pd.read_csv(settings.DECISION_EXEC_SUMMARY)
        else:
            self.exec_summary = pd.DataFrame()

        # ---------- KPI Data ----------
        print("\n📈 Loading KPI Data...")
        if os.path.exists(settings.KPI_REGION_SUMMARY):
            self.kpi_region_summary = pd.read_csv(settings.KPI_REGION_SUMMARY)
            print(f"   ✅ KPI loaded: {len(self.kpi_region_summary)} regions")
        else:
            print(f"   ⚠️  KPI file not found")
            self.kpi_region_summary = pd.DataFrame()

        # ---------- Enhanced Actions (Optional) ----------
        print("\n💡 Loading Enhanced Actions...")
        actions_file = os.path.join(os.path.dirname(settings.FORECAST_FILE), "action_recommendations_enhanced.csv")
        
        if os.path.exists(actions_file):
            self.actions = pd.read_csv(actions_file)
            
            # Map Store_ID to Store if needed
            if 'Store_ID' in self.actions.columns and 'Store' not in self.actions.columns:
                self.actions['Store'] = self.actions['Store_ID']
            
            print(f"   ✅ Actions loaded: {len(self.actions):,} recommendations")
            
            # Show breakdown by priority
            if 'Priority' in self.actions.columns:
                priority_counts = self.actions['Priority'].value_counts().to_dict()
                print(f"      Priority breakdown:")
                for priority, count in sorted(priority_counts.items(), key=lambda x: ['CRITICAL', 'HIGH', 'MEDIUM', 'INFO'].index(x[0]) if x[0] in ['CRITICAL', 'HIGH', 'MEDIUM', 'INFO'] else 999):
                    print(f"         {priority}: {count}")
        else:
            print(f"   ⚠️  Enhanced actions not found (will use fallback mode)")
            self.actions = None

        self.loaded = True
        
        print("\n" + "="*70)
        print("✅ DATA LOADING COMPLETE!")
        print("="*70)
        print(f"Forecast: {len(self.forecast):,} rows")
        print(f"Discounts: {len(self.discount):,} rows")
        print(f"Inventory: {len(self.decisions_store_category):,} rows")
        print(f"Actions: {len(self.actions):,} rows" if self.actions is not None else "Actions: Not loaded")
        print(f"Regions: {len(self.regions)}")
        print(f"Stores: {len(self.stores)}")
        print(f"Categories: {len(self.categories)}")
        print("="*70 + "\n")

    def refresh(self):
        """Reload all data"""
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
        return sorted(self.forecast["Store"].dropna().astype(int).unique().tolist())

store = DataStore()