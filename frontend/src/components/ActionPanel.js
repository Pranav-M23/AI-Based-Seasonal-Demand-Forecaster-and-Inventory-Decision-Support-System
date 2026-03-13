import React, { useMemo } from 'react';
import { Lightbulb } from 'lucide-react';
import { QUARTERS, MONTHS } from './StockSection';

function toFestivalCalendar(festivals = []) {
  return (festivals || []).map((f) => {
    const d = new Date(`${f.date}T00:00:00`);
    return {
      month: d.getMonth(),
      week: Math.min(4, Math.ceil(d.getDate() / 7)),
      name: f.name,
      date: f.date,
      fsiBoost: Number(f.impact_multiplier || 1),
      type: f.type,
      color: f.type === 'pan-indian' ? '#f59e0b' : '#10b981',
    };
  });
}

function ActionPanel({ decision, discounts, forecastData, festivals = [], filterMode, selectedMonth, selectedWeek, selectedQuarter }) {
  const { scenario, actions, scenarioClass, festivalAlert, fsi, periodLabel } = useMemo(() => {
    const festivalCalendar = toFestivalCalendar(festivals);
    // â”€â”€ Derive FSI for the selected period (mirrors StockSection logic) â”€â”€â”€
    let fsi = 1.0;
    let dataFsi = 1.0;

    // Locate matching festival for the selected period
    let festivalMatch = null;
    if (filterMode === 'quarter') {
      const qMonths = QUARTERS[selectedQuarter].months;
      const hits = festivalCalendar.filter(f => qMonths.includes(f.month));
      festivalMatch = hits.sort((a, b) => b.fsiBoost - a.fsiBoost)[0] || null;
    } else {
      festivalMatch = festivalCalendar.find(
        f => f.month === selectedMonth && f.week === selectedWeek
      ) || festivalCalendar.filter(f => f.month === selectedMonth)
         .sort((a, b) => b.fsiBoost - a.fsiBoost)[0] || null;
    }

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
        const avg = periodPoints.reduce((a, b) => a + b.value, 0) / periodPoints.length;
        dataFsi = avg / baseline;
      }
      const maxBackendFsi = Math.max(...periodPoints.map(p => p.fsi || 0));
      if (maxBackendFsi > 0) dataFsi = Math.max(dataFsi, 1 + (maxBackendFsi / 100));
    }
    fsi = festivalMatch ? Math.max(dataFsi, festivalMatch.fsiBoost) : dataFsi;

    // â”€â”€ Period label for message text â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    const periodLabel = filterMode === 'quarter'
      ? QUARTERS[selectedQuarter].label.split(' | ')[0].trim()
      : `${MONTHS[selectedMonth]} Week ${selectedWeek}`;

    // â”€â”€ ML-sourced metrics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    const status         = decision.decision;
    const daysSupply     = decision.days_of_supply || 0;
    const rawDays        = fsi > 0 ? daysSupply / fsi : daysSupply;
    const orderQty       = Math.round(decision.recommended_order_qty || 0);
    const daysToStockout = decision.days_until_stockout;
    const stockoutRisk   = (decision.stockout_risk || 0) * 100;

    // Compute days until the festival begins from today
    let daysToFestival = null;
    if (festivalMatch && filterMode === 'month') {
      const now = new Date();
      const festDate = new Date(now.getFullYear(), festivalMatch.month,
        festivalMatch.week === 1 ? 1 : festivalMatch.week === 2 ? 8 :
        festivalMatch.week === 3 ? 15 : 22);
      daysToFestival = Math.round((festDate - now) / 86400000);
    }

    // Smart discount (same inverse logic)
    let smartDiscount;
    if (fsi >= 3.0)      smartDiscount = 0;
    else if (fsi >= 1.5) smartDiscount = 5;
    else if (fsi >= 0.8) smartDiscount = 10;
    else if (fsi >= 0.65) smartDiscount = 20;
    else                  smartDiscount = 30;

    // â”€â”€ Choose scenario â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    let scenario, actions, scenarioClass;

    const isFestivalPrep     = daysToFestival !== null && daysToFestival > 0 && daysToFestival <= 21;
    const isFestivalLive     = festivalMatch && fsi >= 3.0;
    const isHighDemand       = fsi >= 1.5;
    const isLowDemand        = fsi <= 0.79;

    if (isFestivalLive) {
      // â”€â”€ ðŸš€ During Peak â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
      scenario      = `🚀 Peak Live: ${festivalMatch.name}`;
      scenarioClass = 'scenario--peak';
      const pctAbove = Math.round((fsi - 1) * 100);
      actions = [
        `Sales are +${pctAbove}% above baseline — driven by ${festivalMatch.name} (FSI: ${fsi.toFixed(1)}).`,
        `Monitor stock levels hourly. At this pace, ${rawDays.toFixed(0)} days of stock remain.`,
        `⚡ Do NOT apply additional discounts during peak — organic demand is at maximum.`,
        status === 'REORDER NOW' || rawDays < 5
          ? `🚨 Emergency restock: order ${orderQty > 0 ? orderQty.toLocaleString('en-IN') : 'additional'} units immediately.`
          : `Place pre-emptive top-up orders to maintain shelf availability through the peak.`,
        `Stockout Risk (ML model): ${stockoutRisk.toFixed(1)}%${stockoutRisk > 30 ? ' — HIGH, act now' : ' — manageable'}.`,
      ].filter(Boolean);

    } else if (isFestivalPrep) {
      // â”€â”€ âš ï¸ Festival Prep Window â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
      scenario      = `⚠️ Stockpiling Phase: ${festivalMatch.name} in ${daysToFestival} days`;
      scenarioClass = 'scenario--prep';
      actions = [
        `${festivalMatch.name} peak starts in ${daysToFestival} days. Sales momentum will surge to FSI ${festivalMatch.fsiBoost.toFixed(1)}.`,
        `Double your reorder quantities now to prevent stockouts during peak.`,
        `Current stock covers only ${rawDays.toFixed(0)} days at peak-season pace — reorder before day ${Math.max(1, daysToFestival - 7)}.`,
        orderQty > 0 ? `Suggested order: ${orderQty.toLocaleString('en-IN')} units (inventory model recommendation).` : null,
        `Keep a 5% introductory discount to boost pre-festival basket sizes.`,
      ].filter(Boolean);

    } else if (isHighDemand) {
      // â”€â”€ ðŸ“ˆ High Demand (no festival) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
      scenario      = '📈 Sales Heavy Period Detected';
      scenarioClass = 'scenario--high';
      actions = [
        `FSI is ${fsi.toFixed(2)} — demand is ${Math.round((fsi - 1) * 100)}% above average for ${periodLabel}.`,
        `Keep discount to ${smartDiscount}% only — no need to slash prices when organic demand is strong.`,
        status === 'REORDER NOW' && orderQty > 0
          ? `⚡ Urgent restock: order ${orderQty.toLocaleString('en-IN')} units${daysToStockout ? ` within ${daysToStockout} days` : ''}.`
          : `Increase restock frequency — consider ordering every 5-7 days instead of bi-weekly.`,
        `Stockout Risk: ${stockoutRisk.toFixed(1)}%.`,
      ].filter(Boolean);

    } else if (isLowDemand) {
      // â”€â”€ ðŸ“‰ Slow Period â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
      scenario      = `📉 Demand Slump: Sales are ${Math.round((1 - fsi) * 100)}% below average.`;
      scenarioClass = 'scenario--low';
      actions = [
        `Sales are currently ${Math.round((1 - fsi) * 100)}% below the annual baseline during ${periodLabel}.`,
        `🏷️ Launch a ${smartDiscount}% flash sale to liquidate slow-moving inventory and improve cash flow.`,
        `Pause or reduce incoming shipments — current stock covers ${(daysSupply).toFixed(0)} days at normal pace.`,
        status === 'WATCHLIST'
          ? `⚠️ Watchlist alert: stockout risk is ${stockoutRisk.toFixed(1)}% — monitor daily.`
          : null,
        `Consider bundling slow-moving items with popular ones to increase average basket value.`,
      ].filter(Boolean);

    } else {
      // â”€â”€ âœ… Balanced â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
      scenario      = '✅ Healthy Movement. Inventory levels are stable.';
      scenarioClass = 'scenario--ok';
      const nextFest = festivalCalendar
        .filter(f => {
          const now = new Date();
          const d   = new Date(now.getFullYear(), f.month, f.week * 7 - 3);
          return d > now;
        })
        .sort((a, b) => {
          const now = new Date();
          return new Date(now.getFullYear(), a.month, a.week * 7)
               - new Date(now.getFullYear(), b.month, b.week * 7);
        })[0];
      actions = [
        `Current stock covers ${rawDays.toFixed(0)} days at the ${periodLabel} demand rate.`,
        nextFest
          ? `📅 Upcoming peak: ${nextFest.name} (FSI ${nextFest.fsiBoost.toFixed(1)}×) — plan stock 2 weeks ahead.`
          : null,
        `No extra discounts needed — standard ${smartDiscount}% is optimal for this period.`,
        status === 'REORDER NOW' && orderQty > 0
          ? `Place a routine restock order of ${orderQty.toLocaleString('en-IN')} units near the Restock Trigger Level.`
          : null,
      ].filter(Boolean);
    }

    return { scenario, actions, scenarioClass, festivalAlert: festivalMatch, fsi, periodLabel };
  }, [decision, discounts, forecastData, festivals, filterMode, selectedMonth, selectedWeek, selectedQuarter]);

  return (
    <div className={`action-panel ${scenarioClass}`}>
      <div className="action-header">
        <Lightbulb size={20} />
        <h3>Action Required — {periodLabel}</h3>
        {festivalAlert && (
          <span className="ap-festival-badge" style={{ borderColor: festivalAlert.color, color: festivalAlert.color }}>
            🎉 {festivalAlert.name} · FSI {fsi.toFixed(1)}×
          </span>
        )}
      </div>
      <div className="ap-scenario-title">{scenario}</div>
      <ul className="action-list">
        {actions.map((action, i) => (
          <li key={i} className={action.startsWith('⚡') || action.startsWith('🚨') ? 'action-urgent' : ''}>
            {action}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default ActionPanel;
