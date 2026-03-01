import React, { useMemo } from 'react';
import { RefreshCw } from 'lucide-react';

function StockSection({ decision, category, discounts }) {
  const currentMonth = useMemo(() => {
    const now = new Date();
    return now.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  }, []);

  const discountForMonth = useMemo(() => {
    if (!discounts?.series) return 0;
    const now = new Date();
    const currentWeek = discounts.series.find(d => {
      const weekDate = new Date(d.week);
      return Math.abs(weekDate - now) < 7 * 24 * 60 * 60 * 1000;
    });
    return currentWeek?.discount || 5;
  }, [discounts]);

  const statusClass = decision.decision === 'REORDER NOW' ? 'status-reorder' : 
                      decision.decision === 'WATCHLIST' ? 'status-watchlist' : 'status-ok';

  return (
    <div className="stock-section">
      <div className="section-header">
        <RefreshCw size={20} />
        <h3>Stock Refilling Section - {category}</h3>
      </div>

      <div className="stock-grid">
        <div className="stock-info">
          <div className="info-group">
            <div className="info-label">Current Stock:</div>
            <div className="info-value">{Math.round(decision.current_inventory || 0).toLocaleString()} units</div>
          </div>
          <div className="info-group">
            <div className="info-label">Reorder Point:</div>
            <div className="info-value">{Math.round(decision.reorder_point || 0).toLocaleString()} units</div>
          </div>
        </div>

        <div className="stock-metrics">
          <div className="metric-item">
            <div className="metric-label">Days of Supply</div>
            <div className="metric-value">{(decision.days_of_supply || 0).toFixed(1)} days</div>
          </div>
          <div className="metric-item">
            <div className="metric-label">Priority Score</div>
            <div className="metric-value">{(decision.priority_score || 0).toFixed(1)}/100</div>
          </div>
          <div className="metric-item">
            <div className="metric-label">Status</div>
            <div className={`status-badge ${statusClass}`}>
              {decision.decision === 'REORDER NOW' && '🚨'} {decision.decision}
            </div>
          </div>
          <div className="metric-item">
            <div className="metric-label">Discount Recommendation</div>
            <div className="metric-value">{discountForMonth.toFixed(0)}% ({currentMonth})</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default StockSection;