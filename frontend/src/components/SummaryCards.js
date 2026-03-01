import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle, Package } from 'lucide-react';

function SummaryCards({ summary }) {
  const cards = [
    {
      title: 'Total Items',
      value: summary.total,
      icon: <Package size={24} />,
      className: 'card-total'
    },
    {
      title: 'REORDER NOW',
      value: summary.reorder_now,
      icon: <AlertCircle size={24} />,
      className: 'card-reorder'
    },
    {
      title: 'WATCHLIST',
      value: summary.watchlist,
      icon: <AlertTriangle size={24} />,
      className: 'card-watchlist'
    },
    {
      title: 'OK',
      value: summary.ok,
      icon: <CheckCircle size={24} />,
      className: 'card-ok'
    }
  ];

  return (
    <div className="summary-cards">
      {cards.map((card, index) => (
        <div key={index} className={`summary-card ${card.className}`}>
          <div className="card-icon">{card.icon}</div>
          <div className="card-content">
            <div className="card-title">{card.title}</div>
            <div className="card-value">{card.value}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default SummaryCards;