import React, { useState, useEffect } from 'react';
import { dashboardAPI } from './services/api';
import Header from './components/Header';
import SummaryCards from './components/SummaryCards';
import ForecastChart from './components/ForecastChart';
import StockSection from './components/StockSection';
import ActionPanel from './components/ActionPanel';
import './App.css';

function App() {
  const [metadata, setMetadata] = useState(null);
  const [selectedStore, setSelectedStore] = useState(null);
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [regionStores, setRegionStores] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [loading, setLoading] = useState(false);
  
  const [summary, setSummary] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [storeDecisions, setStoreDecisions] = useState(null);
  const [discounts, setDiscounts] = useState(null);
  const [chartLoading, setChartLoading] = useState(false);

  // Shared period filter — owned here so StockSection + ActionPanel stay in sync
  const now = new Date();
  const [filterMode, setFilterMode]         = useState('month');
  const [selectedMonth, setSelectedMonth]   = useState(now.getMonth());
  const [selectedWeek, setSelectedWeek]     = useState(Math.ceil(now.getDate() / 7) || 1);
  const [selectedQuarter, setSelectedQuarter] = useState(Math.floor(now.getMonth() / 3));

  useEffect(() => {
    loadMetadata();
  }, []);

  const loadMetadata = async () => {
    try {
      const data = await dashboardAPI.getMeta();
      setMetadata(data);
      if (data.categories?.[0]) setSelectedCategory(data.categories[0]);
      // Don't pre-select region/store — wait for user to choose
    } catch (error) {
      console.error('Error loading metadata:', error);
      alert('Cannot connect to backend. Make sure it is running on http://127.0.0.1:8000');
    }
  };

  // When region changes: fetch stores for that region, reset store + dashboard
  const handleRegionChange = async (region) => {
    setSelectedRegion(region);
    setSelectedStore(null);
    setSummary(null);
    setForecastData(null);
    setStoreDecisions(null);
    setDiscounts(null);
    try {
      const data = await dashboardAPI.getStoresByRegion(region);
      setRegionStores(data.stores || []);
      if (data.stores?.length > 0) setSelectedStore(data.stores[0]);
    } catch (error) {
      console.error('Error loading stores for region:', error);
    }
  };

  const loadDashboard = async () => {
    if (!selectedStore || !selectedRegion) return;
    
    setLoading(true);
    try {
      const [summaryData, forecastResult, decisionsData, discountData] = await Promise.all([
        dashboardAPI.getInventorySummary(),
        dashboardAPI.getStoreCategoryForecast(selectedStore, selectedCategory),
        dashboardAPI.getStoreDecisions(selectedStore, selectedCategory),
        dashboardAPI.getDiscountByRegion(selectedRegion),
      ]);

      setSummary(summaryData);
      setForecastData(forecastResult);
      setStoreDecisions(decisionsData);
      setDiscounts(discountData);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh only the forecast chart when category changes (after dashboard loaded)
  useEffect(() => {
    if (!summary || !selectedStore || !selectedRegion) return;
    const fetchForecast = async () => {
      setChartLoading(true);
      try {
        const [forecastResult, decisionsData] = await Promise.all([
          dashboardAPI.getStoreCategoryForecast(selectedStore, selectedCategory),
          dashboardAPI.getStoreDecisions(selectedStore, selectedCategory),
        ]);
        setForecastData(forecastResult);
        setStoreDecisions(decisionsData);
      } catch (error) {
        console.error('Error refreshing forecast:', error);
      } finally {
        setChartLoading(false);
      }
    };
    fetchForecast();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCategory]);

  if (!metadata) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading application...</p>
      </div>
    );
  }

  return (
    <div className="app">
      <Header
        stores={regionStores}
        allStores={metadata.stores}
        storeNames={metadata.store_names || {}}
        regions={metadata.regions}
        selectedStore={selectedStore}
        selectedRegion={selectedRegion}
        onStoreChange={setSelectedStore}
        onRegionChange={handleRegionChange}
        onLoadDashboard={loadDashboard}
        loading={loading}
      />

      {summary && (
        <div className="dashboard-content">
          <div className="store-title">
            <span className="store-icon">🏪</span>
            <h2>
              {(metadata.store_names && metadata.store_names[String(selectedStore)])
                ? metadata.store_names[String(selectedStore)]
                : `Store ${selectedStore}`}
              {' — '}{selectedRegion}
            </h2>
          </div>

          <SummaryCards summary={summary} />

          <div className="main-grid">
            <div className="category-selector">
              <h3>Select Product Category:</h3>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="category-dropdown"
                disabled={chartLoading}
              >
                {metadata.categories.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              <button onClick={loadDashboard} className="refresh-btn" disabled={chartLoading}>
                {chartLoading ? 'Loading...' : 'Refresh Data'}
              </button>
            </div>

            <div className="forecast-container">
              <ForecastChart
                data={forecastData}
                category={selectedCategory}
              />
            </div>
          </div>

          {storeDecisions?.rows?.[0] && (
            <>
              <StockSection
                decision={storeDecisions.rows[0]}
                category={selectedCategory}
                discounts={discounts}
                forecastData={forecastData}
                filterMode={filterMode}       setFilterMode={setFilterMode}
                selectedMonth={selectedMonth} setSelectedMonth={setSelectedMonth}
                selectedWeek={selectedWeek}   setSelectedWeek={setSelectedWeek}
                selectedQuarter={selectedQuarter} setSelectedQuarter={setSelectedQuarter}
              />

              <ActionPanel
                decision={storeDecisions.rows[0]}
                discounts={discounts}
                forecastData={forecastData}
                filterMode={filterMode}
                selectedMonth={selectedMonth}
                selectedWeek={selectedWeek}
                selectedQuarter={selectedQuarter}
              />
            </>
          )}
        </div>
      )}

      {!summary && !loading && (
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <h3>Welcome to Seasonal Demand Forecaster</h3>
          <p>Select a store and region above, then click <strong>[Load Dashboard]</strong> to view insights</p>
        </div>
      )}
    </div>
  );
}

export default App;