import React from 'react';
import { Package } from 'lucide-react';

function Header({ stores, storeNames, regions, selectedStore, selectedRegion, onStoreChange, onRegionChange, onLoadDashboard, loading, onExportPDF, pdfReady, pdfBusy }) {
  return (
    <header className="header">
      <div className="header-title">
        <Package size={32} />
        <h1>Seasonal Demand Forecaster - Inventory Decision Support</h1>
      </div>
      
      <div className="header-controls">
        <div className="control-group">
          <label>Region:</label>
          <select
            value={selectedRegion || ''}
            onChange={(e) => onRegionChange(e.target.value)}
            className="dropdown"
          >
            <option value="" disabled>-- Select Region --</option>
            {regions.map(region => (
              <option key={region} value={region}>{region}</option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Select Store:</label>
          <select
            value={selectedStore || ''}
            onChange={(e) => onStoreChange(Number(e.target.value))}
            className="dropdown"
            disabled={!selectedRegion || stores.length === 0}
          >
            {!selectedRegion
              ? <option value="" disabled>-- Select Region First --</option>
              : stores.length === 0
                ? <option value="" disabled>No stores in region</option>
                : stores.map(storeId => (
                    <option key={storeId} value={storeId}>
                      {storeNames && storeNames[String(storeId)]
                        ? storeNames[String(storeId)]
                        : `Store ${storeId}`}
                    </option>
                  ))
            }
          </select>
        </div>

        <button
          onClick={onLoadDashboard}
          className="load-btn"
          disabled={loading || !selectedStore || !selectedRegion}
        >
          {loading ? 'Loading...' : '[Load Dashboard]'}
        </button>

        <button
          onClick={onExportPDF}
          className="export-pdf-btn"
          disabled={!pdfReady || pdfBusy || loading}
          title="Export current dashboard view as PDF report"
        >
          {pdfBusy ? '⏳ Generating…' : '📄 Export to PDF'}
        </button>
      </div>
    </header>
  );
}

export default Header;