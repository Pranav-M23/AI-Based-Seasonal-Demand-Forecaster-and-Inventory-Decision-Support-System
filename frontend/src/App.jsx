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
  
  // Dashboard data
  const [summary, setSummary] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [storeDecisions, setStoreDecisions] = useState(null);
  const [discounts, setDiscounts] = useState(null);

  // Load metadata on mount
  useEffect(() => {
    loadMetadata();
  }, []);

  const loadMetadata = async () => {
    try {
      const data = await dashboardAPI.getMeta();
      setMetadata(data);
      if (data.stores && data.stores.length > 0) {
        setSelectedStore(data.stores[0]);
      }
      if (data.regions && data.regions.length > 0) {
        setSelectedRegion(data.regions[0]);
      }
      if (data.categories && data.categories.length > 0) {
        setSelectedCategory(data.categories[0]);
      }
    } catch (error) {
      console.error('Error loading metadata:', error);
    }
  };

  const loadDashboard = async () => {
    if (!selectedStore || !selectedRegion) return;
    
    setLoading(true);
    try {
      // Load all dashboard data in parallel
      const [summaryData, forecastData, decisionsData, discountData] = await Promise.all([
        dashboardAPI.getInventorySummary(),
        dashboardAPI.getStoreCategoryForecast(selectedStore, selectedCategory),
        dashboardAPI.getStoreDecisions(selectedStore, null, selectedCategory),
        dashboardAPI.getDiscountByRegion(selectedRegion),
      ]);

      setSummary(summaryData);
      setForecastData(forecastData);
      setStoreDecisions(decisionsData);
      setDiscounts(discountData);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!metadata) {
    return (
      <div className="app-container loading">
        <div className="loading-spinner"></div>
        <p>Loading application...</p>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Header
        stores={metadata.stores}
        storeNames={metadata.store_names || {}}
        regions={metadata.regions}
        selectedStore={selectedStore}
        selectedRegion={selectedRegion}
        onStoreChange={setSelectedStore}
        onRegionChange={setSelectedRegion}
        onLoadDashboard={loadDashboard}
        loading={loading}
      />

      {!loading && summary && (
        <>
          <div className="store-header">
            <div className="store-icon">🏪</div>
            <h2>
              {(metadata.store_names && metadata.store_names[String(selectedStore)])
                ? metadata.store_names[String(selectedStore)]
                : `Store ${selectedStore}`}
              {' '}&mdash; {selectedRegion}
            </h2>
          </div>

          <SummaryCards summary={summary} />

          <div className="content-grid">
            <div className="category-section">
              <h3>Select Product Category:</h3>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="category-select"
              >
                {metadata.categories.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div className="chart-section">
              <ForecastChart
                data={forecastData}
                category={selectedCategory}
                discounts={discounts}
              />
            </div>
          </div>

          {storeDecisions && storeDecisions.rows && storeDecisions.rows.length > 0 && (
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
        </>
      )}

      {!summary && !loading && (
        <div className="empty-state">
          <p>👆 Select a store and region, then click <strong>[Load Dashboard]</strong> to view insights</p>
        </div>
      )}
    </div>
  );
}

export default App;