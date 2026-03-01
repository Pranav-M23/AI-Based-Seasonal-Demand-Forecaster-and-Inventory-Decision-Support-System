import React from 'react';
import { Package } from 'lucide-react';

function Header({ stores, regions, selectedStore, selectedRegion, onStoreChange, onRegionChange, onLoadDashboard, loading }) {
  return (
    <header className="header">
      <div className="header-title">
        <Package size={32} />
        <h1>Seasonal Demand Forecaster - Inventory Decision Support</h1>
      </div>
      
      <div className="header-controls">
        <div className="control-group">
          <label>Select Store:</label>
          <select 
            value={selectedStore} 
            onChange={(e) => onStoreChange(Number(e.target.value))}
            className="dropdown"
          >
            {stores.map(store => (
              <option key={store} value={store}>Store {store}</option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Region:</label>
          <select 
            value={selectedRegion} 
            onChange={(e) => onRegionChange(e.target.value)}
            className="dropdown"
          >
            {regions.map(region => (
              <option key={region} value={region}>{region}</option>
            ))}
          </select>
        </div>

        <button 
          onClick={onLoadDashboard} 
          className="load-btn"
          disabled={loading}
        >
          {loading ? 'Loading...' : '[Load Dashboard]'}
        </button>
      </div>
    </header>
  );
}

export default Header;