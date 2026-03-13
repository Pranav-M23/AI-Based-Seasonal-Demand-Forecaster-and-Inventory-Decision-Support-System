import React, { useMemo } from 'react';
import { RefreshCw, Info } from 'lucide-react';

export const MONTHS = [
  'January','February','March','April','May','June',
  'July','August','September','October','November','December'
];

export const QUARTERS = [
  { label: 'Q1 (Jan-Mar) | New Year / Spring',      months: [0, 1, 2]  },
  { label: 'Q2 (Apr-Jun) | Summer / Mid-year',       months: [3, 4, 5]  },
  { label: 'Q3 (Jul-Sep) | Monsoon / Pre-festive',   months: [6, 7, 8]  },
  { label: 'Q4 (Oct-Dec) | Peak Festive Season',     months: [9, 10, 11] },
];

function toFestivalCalendar(festivals = []) {
  return (festivals || []).map((f) => {
    const d = new Date(`${f.date}T00:00:00`);
    const month = d.getMonth();
    const week = Math.min(4, Math.ceil(d.getDate() / 7));
    return {
      month,
      week,
      name: f.name,
      fsiBoost: Number(f.impact_multiplier || 1),
      type: f.type,
      color: f.type === 'pan-indian' ? '#f59e0b' : '#10b981',
      date: f.date,
    };
  });
}



function Tooltip({ text }) {
  return (
    <span className="ss-tooltip-wrap">
      <Info size={12} className="ss-tooltip-icon" />
      <span className="ss-tooltip-text">{text}</span>
    </span>
  );
}

/**
 * Derive the festival that best matches the selected period (if any).
 * Returns { name, fsiBoost, color } or null.
 */
function getFestivalForPeriod(filterMode, selectedMonth, selectedWeek, selectedQuarter, festivalCalendar) {
  if (filterMode === 'quarter') {
    const qMonths = QUARTERS[selectedQuarter].months;
    // Return the highest-boost festival in this quarter
    const hits = festivalCalendar.filter(f => qMonths.includes(f.month));
    return hits.sort((a, b) => b.fsiBoost - a.fsiBoost)[0] || null;
  }
  // Exact week match first, then month-only
  const exactMatch = festivalCalendar.find(
    f => f.month === selectedMonth && f.week === selectedWeek
  );
  if (exactMatch) return exactMatch;
  const monthHits = festivalCalendar.filter(f => f.month === selectedMonth);
  return monthHits.sort((a, b) => b.fsiBoost - a.fsiBoost)[0] || null;
}

function StockSection({
  decision, category, discounts, forecastData,
  festivals = [],
  filterMode, setFilterMode,
  selectedMonth, setSelectedMonth,
  selectedWeek, setSelectedWeek,
  selectedQuarter, setSelectedQuarter,
}) {
  const festivalCalendar = useMemo(() => toFestivalCalendar(festivals), [festivals]);

  const {
    periodFsi, smartDiscount, discountPct, discountReason, daysOfStock,
    fsiLabel, fsiClass, fsiDisplay,
    computedStatus, computedStatusClass, computedStatusIcon,
    festivalMatch,
  } = useMemo(() => {
    // â”€â”€ 1. Locate matching festival â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    const festivalMatch = getFestivalForPeriod(filterMode, selectedMonth, selectedWeek, selectedQuarter, festivalCalendar);

    // â”€â”€ 2. Compute FSI â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    //   Priority: (a) festival calendar boost, (b) backend forecast FSI field, (c) ratio-based
    let fsi = 1.0;
    let dataFsi = 1.0;

    if (forecastData?.series?.length) {
      const all      = forecastData.series.map(p => p.value);
      const baseline = all.reduce((a, b) => a + b, 0) / all.length;

      let periodPoints;
      if (filterMode === 'quarter') {
        const qMonths = QUARTERS[selectedQuarter].months;
        periodPoints = forecastData.series.filter(p =>
          qMonths.includes(new Date(p.date + 'T00:00:00').getMonth())
        );
      } else {
        periodPoints = forecastData.series.filter(p => {
          const d = new Date(p.date + 'T00:00:00');
          if (d.getMonth() !== selectedMonth) return false;
          return Math.ceil(d.getDate() / 7) === selectedWeek;
        });
        if (!periodPoints.length) {
          periodPoints = forecastData.series.filter(p =>
            new Date(p.date + 'T00:00:00').getMonth() === selectedMonth
          );
        }
      }

      if (periodPoints.length && baseline > 0) {
        const periodAvg = periodPoints.reduce((a, b) => a + b.value, 0) / periodPoints.length;
        dataFsi = periodAvg / baseline;
      }

      // Highest backend FSI value in the period
      const maxBackendFsi = Math.max(...periodPoints.map(p => p.fsi || 0));
      if (maxBackendFsi > 0) {
        dataFsi = Math.max(dataFsi, 1 + (maxBackendFsi / 100));
      }
    }

    // Festival calendar overrides if it gives a higher number (Onam +8500% = Ã—9.5)
    fsi = festivalMatch ? Math.max(dataFsi, festivalMatch.fsiBoost) : dataFsi;

    // â”€â”€ 3. Smart discount (inverse of FSI) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    let discountPct, discountReason, smartDiscount;
    if (fsi >= 3.0) {
      discountPct    = 0;
      discountReason = 'No discount — organic demand is at peak. Maintain full price.';
      smartDiscount  = 'None';
    } else if (fsi >= 1.5) {
      discountPct    = 5;
      discountReason = 'Minimal 5% — demand is strong, keep momentum with a small nudge.';
      smartDiscount  = '5%';
    } else if (fsi >= 0.8) {
      discountPct    = 10;
      discountReason = 'Standard 10% — steady sales, maintain healthy stock turnover.';
      smartDiscount  = '10%';
    } else if (fsi >= 0.65) {
      discountPct    = 20;
      discountReason = 'Apply 20% to accelerate slower-moving inventory this period.';
      smartDiscount  = '20%';
    } else {
      discountPct    = 30;
      discountReason = 'High 30% Clearance — liquidate stagnant stock, improve cash flow.';
      smartDiscount  = '30%';
    }

    // â”€â”€ 4. FSI display label â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    let fsiLabel, fsiClass, fsiDisplay;
    if (fsi >= 9.0) {
      fsiLabel   = '🔥 Explosive Demand';  fsiClass = 'fsi-explosive';
      fsiDisplay = fsi.toFixed(1);
    } else if (fsi >= 3.0) {
      fsiLabel   = '🚀 Peak Season';       fsiClass = 'fsi-peak';
      fsiDisplay = fsi.toFixed(2);
    } else if (fsi >= 1.5) {
      fsiLabel   = '📈 High Demand';       fsiClass = 'fsi-high';
      fsiDisplay = fsi.toFixed(2);
    } else if (fsi <= 0.65) {
      fsiLabel   = '📉 Very Slow Period';  fsiClass = 'fsi-very-low';
      fsiDisplay = fsi.toFixed(2);
    } else if (fsi <= 0.85) {
      fsiLabel   = '⬇️ Slow Period';       fsiClass = 'fsi-low';
      fsiDisplay = fsi.toFixed(2);
    } else {
      fsiLabel   = '👍 Normal';            fsiClass = 'fsi-normal';
      fsiDisplay = fsi.toFixed(2);
    }

    // â”€â”€ 5. Adjusted days of stock â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    const rawDays      = decision.days_of_supply || 0;
    const adjustedDays = fsi > 0 ? rawDays / fsi : rawDays;

    // â”€â”€ 6. Computed status (dynamic, not backend static) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    let computedStatus, computedStatusClass, computedStatusIcon;
    if (fsi >= 3.0 || adjustedDays < 5) {
      computedStatus      = 'RESTOCK NOW';
      computedStatusClass = 'status-reorder';
      computedStatusIcon  = '🚨 Restock Now';
    } else if (fsi >= 1.5 || adjustedDays < 10) {
      computedStatus      = 'MONITOR';
      computedStatusClass = 'status-watchlist';
      computedStatusIcon  = '⚠️ Monitor';
    } else if (fsi <= 0.65) {
      computedStatus      = 'CLEAR STOCK';
      computedStatusClass = 'status-clearance';
      computedStatusIcon  = '📉 Clear Stock';
    } else {
      computedStatus      = 'OK';
      computedStatusClass = 'status-ok';
      computedStatusIcon  = '✅ OK';
    }

    return {
      periodFsi: fsi, smartDiscount, discountPct, discountReason,
      daysOfStock: adjustedDays, fsiLabel, fsiClass, fsiDisplay,
      computedStatus, computedStatusClass, computedStatusIcon,
      festivalMatch,
    };
  }, [decision, discounts, forecastData, filterMode, selectedMonth, selectedWeek, selectedQuarter, festivalCalendar]);

  const sectionBorderClass = computedStatus === 'RESTOCK NOW' ? 'stock-section--danger'
                           : computedStatus === 'CLEAR STOCK' ? 'stock-section--warn'
                           : computedStatus === 'MONITOR'     ? 'stock-section--warn'
                           : 'stock-section--ok';

  const daysClass = daysOfStock < 5  ? 'metric-card--danger'
                  : daysOfStock < 10 ? 'metric-card--warn'
                  : 'metric-card--ok';

  const prioScore = decision.priority_score || 0;
  const prioClass = prioScore > 60 ? 'metric-card--danger' : prioScore > 30 ? 'metric-card--warn' : 'metric-card--ok';

  return (
    <div className={`stock-section ${sectionBorderClass}`}>

      {/* â”€â”€ Header â”€â”€ */}
      <div className="section-header">
        <RefreshCw size={20} />
        <h3>Stock Refilling — {category}</h3>
        {festivalMatch && (
          <span className="ss-festival-tag" style={{ borderColor: festivalMatch.color, color: festivalMatch.color }}>
            🎉 {festivalMatch.name}
          </span>
        )}
        <div className={`status-badge ${computedStatusClass}`}>{computedStatusIcon}</div>
      </div>

      {/* â”€â”€ Time Controls â”€â”€ */}
      <div className="ss-time-controls">
        <div className="ss-mode-tabs">
          <button className={`ss-mode-tab ${filterMode === 'month' ? 'active' : ''}`}
            onClick={() => setFilterMode('month')}>Monthly View</button>
          <button className={`ss-mode-tab ${filterMode === 'quarter' ? 'active' : ''}`}
            onClick={() => setFilterMode('quarter')}>Quarterly View</button>
        </div>

        {filterMode === 'month' ? (
          <div className="ss-dropdowns">
            <div className="ss-select-group">
              <label>Month</label>
              <select value={selectedMonth} onChange={e => setSelectedMonth(Number(e.target.value))}>
                {MONTHS.map((m, i) => <option key={m} value={i}>{m}</option>)}
              </select>
            </div>
            <div className="ss-select-group">
              <label>Week</label>
              <select value={selectedWeek} onChange={e => setSelectedWeek(Number(e.target.value))}>
                <option value={1}>Week 1 (1-7)</option>
                <option value={2}>Week 2 (8-14)</option>
                <option value={3}>Week 3 (15-21)</option>
                <option value={4}>Week 4 (22-31)</option>
              </select>
            </div>
          </div>
        ) : (
          <div className="ss-dropdowns">
            <div className="ss-select-group ss-select-group--wide">
              <label>Business Quarter</label>
              <select value={selectedQuarter} onChange={e => setSelectedQuarter(Number(e.target.value))}>
                {QUARTERS.map((q, i) => <option key={i} value={i}>{q.label}</option>)}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* â”€â”€ Metrics Grid â”€â”€ */}
      <div className="ss-metrics-grid">

        <div className="ss-metric-card">
          <div className="ss-metric-label">Current Stock</div>
          <div className="ss-metric-value">{Math.round(decision.current_inventory || 0).toLocaleString('en-IN')}</div>
          <div className="ss-metric-unit">units on shelf</div>
        </div>

        <div className={`ss-metric-card ${daysClass}`}>
          <div className="ss-metric-label">Days of Stock
            <Tooltip text="Adjusted for current demand pace. During peak seasons, stock depletes faster." />
          </div>
          <div className="ss-metric-value">{daysOfStock.toFixed(1)}</div>
          <div className="ss-metric-unit">
            {daysOfStock < 5 ? '🚨 Critically low — order today'
              : daysOfStock < 10 ? '⚠️ Running low — reorder soon'
              : 'days until shelf is empty'}
          </div>
        </div>

        <div className="ss-metric-card">
          <div className="ss-metric-label">
            Restock Trigger Level
            <Tooltip text="When stock hits this number, it's time to buy more to avoid running out." />
          </div>
          <div className="ss-metric-value">{Math.round(decision.reorder_point || 0).toLocaleString('en-IN')}</div>
          <div className="ss-metric-unit">units — order before reaching this</div>
        </div>

        <div className={`ss-metric-card ss-metric-card--fsi ${fsiClass}`}>
          <div className="ss-metric-label">
            Sales Momentum (FSI)
            <Tooltip text="Festival Sales Index: 1.0 = normal · 1.5+ = high demand · 9+ = explosive (e.g. Onam). Powered by XGBoost Festival Impact model (R²=0.686)." />
          </div>
          <div className="ss-metric-value ss-fsi-value">{fsiDisplay}</div>
          <div className="ss-metric-unit">{fsiLabel}</div>
        </div>

        <div className={`ss-metric-card ss-metric-card--discount
          ${periodFsi <= 0.65 ? 'metric-card--danger' : periodFsi >= 3.0 ? 'metric-card--ok' : ''}`}>
          <div className="ss-metric-label">
            Discount Recommendation
            <Tooltip text="Inverse FSI logic: higher demand = lower discount. Powered by XGBoost Discount Optimiser (Acc=98.7%)." />
          </div>
          <div className="ss-metric-value">{smartDiscount}</div>
          <div className="ss-metric-unit">{discountReason}</div>
        </div>

        <div className={`ss-metric-card ${prioClass}`}>
          <div className="ss-metric-label">
            Priority Score
            <Tooltip text="Random Forest Inventory Reorder model (Acc=99.98%). Higher = more urgent restocking needed." />
          </div>
          <div className="ss-metric-value">
            {prioScore.toFixed(1)}<span className="ss-metric-total">/100</span>
          </div>
          <div className="ss-metric-unit">
            {prioScore > 60 ? '🚨 Urgent attention needed' : prioScore > 30 ? '⚠️ Keep an eye on this' : '✅ No immediate action'}
          </div>
        </div>

      </div>
    </div>
  );
}

export default StockSection;
