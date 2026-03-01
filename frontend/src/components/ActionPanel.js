import React, { useMemo } from 'react';
import { Lightbulb } from 'lucide-react';

function ActionPanel({ decision, discounts }) {
  const actions = useMemo(() => {
    const items = [];
    
    if (decision.decision === 'REORDER NOW' || decision.decision === 'REORDER SOON') {
      const orderQty = Math.round(decision.recommended_order_qty || 0);
      const daysUntilStockout = Math.round(decision.days_until_stockout || decision.days_of_supply || 0);
      
      if (orderQty > 0) {
        items.push(`Order ${orderQty.toLocaleString()} units within ${daysUntilStockout} days to avoid stockout`);
      }
    }

    if (discounts?.series) {
      const now = new Date();
      const upcomingDiscounts = discounts.series.filter(d => {
        const weekDate = new Date(d.week);
        return weekDate >= now && d.discount > 0;
      }).slice(0, 3);

      upcomingDiscounts.forEach(d => {
        const date = new Date(d.week);
        const month = date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        if (d.discount >= 5) {
          items.push(`Apply ${d.discount.toFixed(0)}% discount during ${month} period`);
        }
      });
    }

    if (decision.decision === 'WATCHLIST') {
      items.push(`Monitor inventory closely - stockout risk at ${(decision.stockout_risk * 100).toFixed(1)}%`);
    }

    if (decision.decision === 'OK') {
      items.push('Inventory levels are healthy - continue normal operations');
    }

    return items;
  }, [decision, discounts]);

  if (actions.length === 0) return null;

  return (
    <div className="action-panel">
      <div className="action-header">
        <Lightbulb size={20} />
        <h3>Action Required:</h3>
      </div>
      <ul className="action-list">
        {actions.map((action, index) => (
          <li key={index}>{action}</li>
        ))}
      </ul>
    </div>
  );
}

export default ActionPanel;