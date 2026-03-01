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
  const [selectedStore, setSelectedStore] = useState(1);
  const [selectedRegion, setSelectedRegion] = useState('Kerala');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [loading, setLoading] = useState(false);
  
  const [summary, setSummary] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [storeDecisions, setStoreDecisions] = useState(null);
  const [discounts, setDiscounts] = useState(null);

  useEffect(() => {
    loadMetadata();
  }, []);

  const loadMetadata = async () => {
    try {
      const data = await dashboardAPI.getMeta();
      setMetadata(data);
      if (data.stores?.[0]) setSelectedStore(data.stores[0]);
      if (data.regions?.[0]) setSelectedRegion(data.regions[0]);
      if (data.categories?.[0]) setSelectedCategory(data.categories[0]);
    } catch (error) {
      console.error('Error loading metadata:', error);
      alert('Cannot connect to backend. Make sure it is running on http://127.0.0.1:8000');
    }
  };

  const loadDashboard = async () => {
    if (!selectedStore || !selectedRegion) return;
    
    setLoading(true);
    try {
      const [summaryData, forecastData, decisionsData, discountData] = await Promise.all([
        dashboardAPI.getInventorySummary(),
        dashboardAPI.getStoreCategoryForecast(selectedStore, selectedCategory),
        dashboardAPI.getStoreDecisions(selectedStore, selectedCategory),
        dashboardAPI.getDiscountByRegion(selectedRegion),
      ]);

      setSummary(summaryData);
      setForecastData(forecastData);
      setStoreDecisions(decisionsData);
      setDiscounts(discountData);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      alert('Error loading dashboard. Make sure backend is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

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
        stores={metadata.stores}
        regions={metadata.regions}
        selectedStore={selectedStore}
        selectedRegion={selectedRegion}
        onStoreChange={setSelectedStore}
        onRegionChange={setSelectedRegion}
        onLoadDashboard={loadDashboard}
        loading={loading}
      />

      {summary && (
        <div className="dashboard-content">
          <div className="store-title">
            <span className="store-icon">🏪</span>
            <h2>Store {selectedStore} - {selectedRegion}</h2>
          </div>

          <SummaryCards summary={summary} />

          <div className="main-grid">
            <div className="category-selector">
              <h3>Select Product Category:</h3>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="category-dropdown"
              >
                {metadata.categories.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              <button onClick={loadDashboard} className="refresh-btn">
                Refresh Data
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
              />

              <ActionPanel
                decision={storeDecisions.rows[0]}
                discounts={discounts}
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