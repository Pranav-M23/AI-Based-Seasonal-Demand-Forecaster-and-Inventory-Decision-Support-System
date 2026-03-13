import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Upload, ArrowLeft, TrendingUp, Save, FolderOpen } from 'lucide-react';
import { Line } from 'react-chartjs-2';
import ExportButton from './ExportButton';
import SavePredictionDialog from './SavePredictionDialog';
import PredictionsCatalog from './PredictionsCatalog';
import { dashboardAPI } from '../services/api';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

/* ── Region → State mapping ────────────────────── */
const REGION_STATES = {
  'North India':   ['Delhi', 'Haryana', 'Punjab', 'Uttar Pradesh', 'Uttarakhand', 'Himachal Pradesh', 'Jammu & Kashmir', 'Rajasthan'],
  'South India':   ['Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh', 'Telangana'],
  'East India':    ['West Bengal', 'Odisha', 'Bihar', 'Jharkhand', 'Tripura'],
  'West India':    ['Maharashtra', 'Gujarat', 'Goa', 'Rajasthan'],
  'Central India': ['Madhya Pradesh', 'Chhattisgarh'],
  'Northeast India': ['Assam', 'Manipur', 'Nagaland', 'Mizoram', 'Arunachal Pradesh', 'Meghalaya', 'Sikkim'],
};
const REGIONS = Object.keys(REGION_STATES);

const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const SHORT_MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

function normalizeFestivalsForChart(apiFestivals = []) {
  return (apiFestivals || []).map((f) => {
    const d = new Date(`${f.date}T00:00:00`);
    return {
      month: d.getMonth(),
      name: f.name,
      date: f.date,
      boost: Number(f.impact_multiplier || 1),
      type: f.type || 'local',
      color: f.type === 'pan-indian' ? '#f59e0b' : '#10b981',
    };
  });
}

/* ── CSV parsing helper ────────────────────────── */
function parseCSV(text) {
  const lines = text.trim().split('\n');
  if (lines.length < 2) return [];
  const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
  return lines.slice(1).map(line => {
    const vals = line.split(',').map(v => v.trim().replace(/^"|"$/g, ''));
    const row = {};
    headers.forEach((h, i) => { row[h] = vals[i]; });
    return row;
  });
}

/* ── Simulate a 12-month forecast from raw sales rows ──── */
function buildForecast(rows, region, selectedCats, salesYear, apiFestivals = []) {
  const nextYear = parseInt(salesYear, 10) + 1;
  const festivals = normalizeFestivalsForChart(apiFestivals);

  /* Try to detect column names flexibly */
  const dateCol  = Object.keys(rows[0] || {}).find(k => /date/i.test(k))   || 'Date';
  const salesCol = Object.keys(rows[0] || {}).find(k => /sales|units|value/i.test(k)) || 'Sales';
  const catCol   = Object.keys(rows[0] || {}).find(k => /category|cat/i.test(k)) || 'Category';
  const regCol   = Object.keys(rows[0] || {}).find(k => /region/i.test(k))  || 'Region';

  /* Filter rows by region + selected categories (if present in CSV) */
  let filtered = rows;
  if (rows[0] && rows[0][regCol]) {
    filtered = filtered.filter(r => r[regCol] === region);
  }
  if (selectedCats.length > 0 && rows[0] && rows[0][catCol]) {
    const catFiltered = filtered.filter(r => selectedCats.includes(r[catCol]));
    if (catFiltered.length > 0) filtered = catFiltered;
    // If no rows matched the category name, keep all rows (CSV uses different naming)
  }

  /* Aggregate baseline by month (0-11) from last year data */
  const monthlyBaseline = new Array(12).fill(0);
  const monthlyCount = new Array(12).fill(0);
  filtered.forEach(r => {
    const d = new Date(r[dateCol]);
    if (isNaN(d.getTime())) return;
    const m = d.getMonth();
    const val = parseFloat(r[salesCol]) || 0;
    monthlyBaseline[m] += val;
    monthlyCount[m] += 1;
  });

  /* If no data matched, generate reasonable demo data */
  const hasData = monthlyBaseline.some(v => v > 0);
  if (!hasData) {
    for (let m = 0; m < 12; m++) {
      monthlyBaseline[m] = Math.round(200 + Math.sin(m * 0.5) * 60 + Math.random() * 40);
    }
  }

  /* Build predictions: baseline = monthly total, predicted = total * growth * festival */
  const growthFactor = 1.08; // assume 8% YoY growth
  const monthly = [];
  for (let m = 0; m < 12; m++) {
    const base = monthlyBaseline[m];
    const fest = festivals.find(f => f.month === m);
    const boost = fest ? fest.boost : 1.0;
    const predicted = Math.round(base * growthFactor * boost);
    const baselineVal = Math.round(base);
    monthly.push({
      month: m,
      monthLabel: SHORT_MONTHS[m],
      predicted,
      baseline: baselineVal,
      festival: fest || null,
    });
  }

  /* Also build daily series for the line chart (one point per day) */
  const dailySeries = [];
  for (let m = 0; m < 12; m++) {
    const md = monthly[m];
    const daysInMonth = new Date(nextYear, m + 1, 0).getDate();
    const dailyBase = md.predicted / daysInMonth;
    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${nextYear}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      // Add slight variation
      const noise = 0.85 + Math.random() * 0.30;
      dailySeries.push({
        date: dateStr,
        value: Math.round(dailyBase * noise),
        month: m,
        festival: md.festival ? md.festival.name : null,
      });
    }
  }

  return { monthly, dailySeries, nextYear, festivals };
}


/* ══════════════════════════════════════════════════════════════════════
   MAIN COMPONENT
   ══════════════════════════════════════════════════════════════════════ */
function ShopOwnerAnalytics({ categories = [] }) {
  /* ── Form state ──────────────────────────── */
  const [ownerName, setOwnerName]       = useState('');
  const [businessName, setBusinessName] = useState('');
  const [region, setRegion]             = useState('');
  const [state, setState]               = useState('');
  const [selectedCats, setSelectedCats] = useState([]);
  const [salesYear, setSalesYear]       = useState('2025');
  const [csvFile, setCsvFile]           = useState(null);

  /* ── Results state ───────────────────────── */
  const [forecastMap, setForecastMap]    = useState(null);  // { [category]: { monthly, dailySeries, nextYear, festivals } }
  const [viewCategory, setViewCategory] = useState('');
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth());
  const [selectedQuarter, setSelectedQuarter] = useState('none');

  const chartRef = useRef(null);
  const categoryList = categories.filter(c => c !== 'All');
  const forecast = forecastMap && viewCategory ? forecastMap[viewCategory] : null;
  const forecastCategories = forecastMap ? Object.keys(forecastMap) : [];
  const statesForRegion = REGION_STATES[region] || [];
  const [contextFestivals, setContextFestivals] = useState([]);

  /* ── Save/Catalog dialog state ──────── */
  const [showSaveDialog, setShowSaveDialog]     = useState(false);
  const [showCatalog, setShowCatalog]           = useState(false);
  const [savedToast, setSavedToast]             = useState(false);

  /* ── Form handlers ──────────────────────── */
  const handleRegionChange = (e) => { setRegion(e.target.value); setState(''); };
  const toggleCategory = (cat) => {
    setSelectedCats(prev => prev.includes(cat) ? prev.filter(c => c !== cat) : [...prev, cat]);
  };
  const handleFileChange = (e) => {
    const file = e.target.files && e.target.files[0];
    if (file && file.name.endsWith('.csv')) setCsvFile(file);
  };

  useEffect(() => {
    const loadFestivals = async () => {
      if (!region) {
        setContextFestivals([]);
        return;
      }
      try {
        const response = await dashboardAPI.getFestivalsByRegion(region, state || null);
        setContextFestivals(response?.festivals || []);
      } catch {
        setContextFestivals([]);
      }
    };
    loadFestivals();
  }, [region, state]);

  const handleLoadAnalytics = () => {
    if (!csvFile) { alert('Please upload a CSV file first.'); return; }
    if (!region)  { alert('Please select a region.'); return; }

    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target.result;
      const rows = parseCSV(text);
      if (rows.length === 0) { alert('CSV appears empty or invalid.'); return; }
      let catsToForecast;
      if (selectedCats.length > 0) {
        catsToForecast = selectedCats;
      } else {
        // Auto-detect categories from CSV
        const catCol = Object.keys(rows[0] || {}).find(k => /category|cat/i.test(k));
        if (catCol) {
          const unique = [...new Set(rows.map(r => r[catCol]).filter(Boolean))];
          catsToForecast = unique.length > 0 ? unique : categoryList;
        } else {
          catsToForecast = ['All Products'];
        }
      }
      const map = {};
      catsToForecast.forEach(cat => {
        map[cat] = buildForecast(rows, region, [cat], salesYear, contextFestivals);
      });
      setForecastMap(map);
      setViewCategory(catsToForecast[0]);
      setSelectedMonth(new Date().getMonth());
      setSelectedQuarter('none');
    };
    reader.readAsText(csvFile);
  };

  const handleBackToConfig = () => { setForecastMap(null); setViewCategory(''); };

  /* ── Derived data for selected month/quarter ── */
  const periodData = useMemo(() => {
    if (!forecast) return null;
    const { monthly, festivals } = forecast;

    let months;
    if (selectedQuarter !== 'none') {
      const q = parseInt(selectedQuarter, 10);
      months = [q * 3, q * 3 + 1, q * 3 + 2];
    } else {
      months = [selectedMonth];
    }

    const items = monthly.filter(m => months.includes(m.month));
    const predicted = items.reduce((s, i) => s + i.predicted, 0);
    const baseline  = items.reduce((s, i) => s + i.baseline, 0);
    const change    = predicted - baseline;
    const changePct = baseline > 0 ? Math.round((change / baseline) * 100) : 0;

    // Festival in this period
    const periodFestivals = festivals.filter(f => months.includes(f.month));
    const topFestival = periodFestivals.sort((a, b) => b.boost - a.boost)[0] || null;

    // Determine demand level
    let demandLevel, badgeColor, badgeText;
    if (changePct >= 40) {
      demandLevel = 'peak'; badgeColor = '#10b981'; badgeText = '\uD83D\uDD25 PEAK SEASON / HIGH GROWTH POTENTIAL';
    } else if (changePct >= 15) {
      demandLevel = 'high'; badgeColor = '#22d3ee'; badgeText = '\uD83D\uDCC8 HIGH DEMAND EXPECTED';
    } else if (changePct >= -10) {
      demandLevel = 'normal'; badgeColor = '#06b6d4'; badgeText = '\u2705 HEALTHY MOVEMENT / BALANCED';
    } else {
      demandLevel = 'low'; badgeColor = '#f59e0b'; badgeText = '\u26A0\uFE0F LOW DEMAND PERIOD';
    }

    const periodLabel = selectedQuarter !== 'none'
      ? `Q${parseInt(selectedQuarter, 10) + 1}`
      : MONTHS[selectedMonth];

    // Stock range recommendation
    const stockMin = Math.round(predicted * 0.75);
    const stockMax = Math.round(predicted * 1.10);

    // Discount recommendation
    let discountPct, discountReason;
    if (demandLevel === 'peak') {
      discountPct = '5%'; discountReason = 'Very high demand — minimal discount needed to maximize revenue';
    } else if (demandLevel === 'high') {
      discountPct = '8%'; discountReason = 'Strong demand driven by festivals — low discount to capitalize on sales';
    } else if (demandLevel === 'normal') {
      discountPct = '10%'; discountReason = 'Balanced demand — standard discount to maintain steady sales flow';
    } else {
      discountPct = '15-20%'; discountReason = 'Low demand period — higher discount to reduce holding costs and clear inventory';
    }

    return { predicted, baseline, change, changePct, topFestival, periodFestivals, demandLevel, badgeColor, badgeText, periodLabel, stockMin, stockMax, discountPct, discountReason };
  }, [forecast, selectedMonth, selectedQuarter]);

  /* ── Generate action advice ────────────── */
  const actions = useMemo(() => {
    if (!periodData) return [];
    const { changePct, topFestival, demandLevel, periodLabel } = periodData;
    const list = [];

    if (demandLevel === 'peak' || demandLevel === 'high') {
      const stockQty = changePct >= 40 ? '300+' : '200-250';
      list.push({
        icon: '\uD83D\uDCE6',
        title: 'Bulk Stocking Priority',
        text: `Model predicts +${changePct}% growth vs. last ${periodLabel}. Prepare fulfillment now. Action: Pre-order and Stock up ${stockQty} products for this month to prevent stockouts.`,
      });
      if (topFestival) {
        list.push({
          icon: '\uD83C\uDF89',
          title: 'Seasonal Boost',
          text: `Demand is driven by the festival of ${topFestival.name}. Ensure maximum fulfillment capability.`,
        });
      }
      const discountPct = changePct >= 40 ? 5 : 8;
      list.push({
        icon: '\uD83D\uDCB8',
        title: 'Pricing Strategy',
        text: `Discount: Keep ${discountPct}% Discount maximum. Maintain a low discount due to the very high demand for this product.`,
      });
    } else if (demandLevel === 'normal') {
      list.push({
        icon: '\uD83D\uDCE6',
        title: 'Balanced Stocking',
        text: 'Inventory levels are stable. Maintain standard reorder points.',
      });
      list.push({
        icon: '\uD83D\uDCB8',
        title: 'Strategy',
        text: '10% Standard Discount is optimal for maintaining consistent sales.',
      });
    } else {
      list.push({
        icon: '\uD83D\uDCE6',
        title: 'Conservative Stocking',
        text: `Sales are expected to dip ${Math.abs(changePct)}% vs. last year. Reduce order quantity to avoid excess inventory.`,
      });
      list.push({
        icon: '\uD83D\uDCB8',
        title: 'Clearance Strategy',
        text: '15-20% Discount recommended to keep inventory moving and reduce holding costs.',
      });
    }
    return list;
  }, [periodData]);


  /* ══════════════════════════════════════════
     CHART DATA (monthly line chart)
     ══════════════════════════════════════════ */
  const { chartData, chartOptions, festivalAnnotations } = useMemo(() => {
    if (!forecast) return { chartData: null, chartOptions: {}, festivalAnnotations: [] };
    const { monthly, festivals } = forecast;

    const labels = monthly.map(m => m.monthLabel);
    const predicted = monthly.map(m => m.predicted);
    const baselineVals = monthly.map(m => m.baseline);

    const annotations = festivals.map(f => ({
      month: f.month,
      name: f.name,
      color: f.color,
      type: f.type,
    }));

    const maxVal = Math.max(...predicted, ...baselineVals);
    const yMax = Math.ceil(maxVal * 1.15 / 50) * 50;

    const cData = {
      labels,
      datasets: [
        {
          label: `Predicted ${forecast.nextYear}`,
          data: predicted,
          borderColor: '#06b6d4',
          backgroundColor: 'rgba(6, 182, 212, 0.12)',
          borderWidth: 2.5,
          tension: 0.35,
          fill: true,
          pointRadius: (ctx) => annotations.find(a => a.month === ctx.dataIndex) ? 6 : 3,
          pointBackgroundColor: (ctx) => {
            const a = annotations.find(a2 => a2.month === ctx.dataIndex);
            return a ? a.color : '#06b6d4';
          },
          pointHoverRadius: 8,
          pointHoverBorderColor: '#fff',
          pointHoverBorderWidth: 2,
        },
        {
          label: `Baseline ${forecast.nextYear - 1}`,
          data: baselineVals,
          borderColor: 'rgba(148, 163, 184, 0.6)',
          backgroundColor: 'transparent',
          borderWidth: 1.5,
          borderDash: [6, 4],
          tension: 0.35,
          fill: false,
          pointRadius: 0,
        },
      ],
    };

    const opts = {
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { top: 24, right: 8 } },
      plugins: {
        legend: {
          display: true, position: 'top', align: 'end',
          labels: { color: '#9ca3af', boxWidth: 14, padding: 16, font: { size: 11 }, usePointStyle: true },
        },
        tooltip: {
          mode: 'index', intersect: false,
          backgroundColor: 'rgba(10, 18, 35, 0.97)',
          padding: 14, titleColor: '#f1f5f9', bodyColor: '#cbd5e1',
          borderColor: '#06b6d4', borderWidth: 1, displayColors: true,
          callbacks: {
            title: (items) => {
              const idx = items[0] && items[0].dataIndex;
              const fest = annotations.find(a => a.month === idx);
              return fest ? `${MONTHS[idx]}  \uD83C\uDF89 ${fest.name}` : MONTHS[idx];
            },
          },
        },
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false },
          ticks: { color: '#6b7280', font: { size: 11 } },
        },
        y: {
          min: 0, max: yMax,
          grid: { color: 'rgba(255,255,255,0.06)', drawBorder: false },
          ticks: { color: '#9ca3af', font: { size: 11 }, callback: (v) => v.toLocaleString('en-IN') },
        },
      },
      interaction: { mode: 'index', axis: 'x', intersect: false },
    };

    return { chartData: cData, chartOptions: opts, festivalAnnotations: annotations };
  }, [forecast]);

  /* Festival lines plugin */
  const festivalLinesPlugin = useMemo(() => ({
    id: 'soFestivalLines',
    afterDraw(chart) {
      if (!festivalAnnotations || !festivalAnnotations.length) return;
      const { ctx, chartArea, scales } = chart;
      ctx.save();
      festivalAnnotations.forEach(({ month, color, name }) => {
        const x = scales.x.getPixelForValue(month);
        if (x < chartArea.left || x > chartArea.right) return;
        ctx.strokeStyle = color;
        ctx.setLineDash([4, 3]);
        ctx.lineWidth = 1.5;
        ctx.globalAlpha = 0.6;
        ctx.beginPath();
        ctx.moveTo(x, chartArea.top + 18);
        ctx.lineTo(x, chartArea.bottom);
        ctx.stroke();
        // Badge
        ctx.globalAlpha = 1;
        ctx.setLineDash([]);
        const label = name.length > 12 ? name.substring(0, 11) + '…' : name;
        const pad = 5;
        ctx.font = 'bold 9px Inter, system-ui, sans-serif';
        const tw = ctx.measureText(label).width;
        const bw = tw + pad * 2, bh = 15;
        const bx = Math.min(Math.max(x - bw / 2, chartArea.left + 2), chartArea.right - bw - 2);
        const by = chartArea.top;
        ctx.fillStyle = color;
        ctx.beginPath();
        if (ctx.roundRect) { ctx.roundRect(bx, by, bw, bh, 3); ctx.fill(); }
        else ctx.fillRect(bx, by, bw, bh);
        ctx.fillStyle = '#fff';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText(label, bx + pad, by + bh / 2);
      });
      ctx.restore();
    }
  }), [festivalAnnotations]);

  /* ════════════════════════════════════════════
     RENDER — CONFIG FORM
     ════════════════════════════════════════════ */
  if (!forecastMap) {
    return (
      <div className="so-page">
        <div className="so-page-header">
          <h1>Shop Owner Advanced Analytics</h1>
          <p>Configure your business profile and forecast your future sales.</p>
        </div>

        {/* Section 1: Business Profile */}
        <section className="so-section">
          <div className="so-row">
            <div className="so-field">
              <label className="so-label">Shop Owner Name</label>
              <input type="text" className="so-input" value={ownerName} onChange={(e) => setOwnerName(e.target.value)} />
            </div>
            <div className="so-field">
              <label className="so-label">Business Name</label>
              <input type="text" className="so-input" value={businessName} onChange={(e) => setBusinessName(e.target.value)} />
            </div>
          </div>
        </section>

        {/* Section 2: Geographic & Category */}
        <section className="so-section">
          <h2 className="so-section-title">Geographic &amp; Category Focus</h2>
          <div className="so-row">
            <div className="so-field">
              <label className="so-label">Region <span className="so-hint">(North, South, Central, East, West India)</span></label>
              <select className="so-select" value={region} onChange={handleRegionChange}>
                <option value="">-- Select Region --</option>
                {REGIONS.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div className="so-field">
              <label className="so-label">State <span className="so-hint">(dynamically updates)</span></label>
              <select className="so-select" value={state} onChange={(e) => setState(e.target.value)} disabled={!region}>
                <option value="">{region ? '-- Select State --' : '-- Select Region First --'}</option>
                {statesForRegion.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>
          <div className="so-categories">
            <label className="so-label">Product Categories</label>
            <div className="so-cat-grid">
              {categoryList.map(cat => (
                <label key={cat} className="so-cat-item">
                  <input type="checkbox" checked={selectedCats.includes(cat)} onChange={() => toggleCategory(cat)} />
                  <span>{cat}</span>
                </label>
              ))}
            </div>
          </div>
        </section>

        {/* Section 3: Data Acquisition */}
        <section className="so-section">
          <p className="so-tagline">Upload Your Sales Data — We Predict Your Next Year Sales</p>
          <div className="so-row so-row--upload">
            <div className="so-field so-field--narrow">
              <label className="so-label">Sales Year: {salesYear}</label>
              <select className="so-select" value={salesYear} onChange={(e) => setSalesYear(e.target.value)}>
                <option value="2025">2025</option>
                <option value="2024">2024</option>
              </select>
            </div>
          </div>
          <label className="so-upload-btn">
            <Upload size={18} />
            <span>{csvFile ? csvFile.name : 'Upload CSV Sales Data'}</span>
            <input type="file" accept=".csv" hidden onChange={handleFileChange} />
          </label>
          <button className="so-load-btn" onClick={handleLoadAnalytics}>Load Analytics</button>
        </section>
      </div>
    );
  }


  /* ════════════════════════════════════════════
     RENDER — RESULTS VIEW
     ════════════════════════════════════════════ */
  return (
    <div className="so-page so-page--wide">
      {/* ── Personalized greeting ────────────── */}
      <div className="so-greeting-header">
        <h1>Hi {ownerName || 'there'}, {forecast ? forecast.nextYear : ''} Sales Demand Forecasting for {businessName || 'Your Business'}</h1>
      </div>

      {/* ── Export + Save + Catalog Buttons ───── */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginBottom: 12, flexWrap: 'wrap' }}>
        <button className="pc-open-btn" onClick={() => setShowCatalog(true)}>
          <FolderOpen size={16} /> Predictions Catalog
        </button>
        <button className="spd-save-btn" onClick={() => setShowSaveDialog(true)}>
          <Save size={16} /> Save Prediction
        </button>
        <ExportButton
          dataType="forecast"
          forecastMap={forecastMap}
          activeCategory={viewCategory}
          chartRef={chartRef}
          shopOwnerInfo={{
            name: ownerName,
            business: businessName,
            region: region,
            state: state,
            category: viewCategory,
          }}
        />
      </div>

      {/* ── Top bar ────────────────────── */}
      <div className="so-results-header">
        <div className="so-results-header-left">
          <h2>Month: {periodData ? periodData.periodLabel : ''}</h2>
          <span className="so-results-meta">
            Category <span className="so-hint">({viewCategory || 'All'})</span>
            {' · '} Region <span className="so-hint">({region})</span>
            {state ? <>{' · '} State <span className="so-hint">({state})</span></> : null}
          </span>
        </div>
        <button className="so-modify-btn" onClick={handleBackToConfig}>
          <ArrowLeft size={16} /> Modify Configuration
        </button>
      </div>

      {/* ── 3.1 Yearly Demand Chart ──────────── */}
      <section className="so-section so-chart-section">
        <div className="chart-header">
          <TrendingUp size={20} />
          <h3>12-Month Demand Forecast — {forecast.nextYear}</h3>
          <div className="festival-pills">
            {festivalAnnotations.map(f => (
              <span key={f.name} className="festival-pill" style={{ borderColor: f.color, color: f.color }} title={f.name}>
                {f.name.length > 14 ? f.name.substring(0, 13) + '…' : f.name}
              </span>
            ))}
          </div>
        </div>
        <div className="festival-legend" style={{ marginTop: '-0.25rem' }}>
          <span className="festival-legend-item">
            <span className="festival-legend-dot" style={{ backgroundColor: '#10b981' }} />
            Local Festival
          </span>
          <span className="festival-legend-item">
            <span className="festival-legend-dot" style={{ backgroundColor: '#f59e0b' }} />
            Pan-Indian Festival
          </span>
        </div>
        <div className="so-chart-container">
          {chartData && <Line ref={chartRef} data={chartData} options={chartOptions} plugins={[festivalLinesPlugin]} />}
        </div>
      </section>

      {/* ── 3.2 Time Controls + Category Selector ── */}
      <div className="so-time-controls">
        {forecastCategories.length > 1 && (
          <div className="so-tc-group">
            <label className="so-label">Product Category</label>
            <select className="so-select so-select--category" value={viewCategory} onChange={(e) => setViewCategory(e.target.value)}>
              {forecastCategories.map(cat => <option key={cat} value={cat}>{cat}</option>)}
            </select>
          </div>
        )}
        <div className="so-tc-group">
          <label className="so-label">Select Month</label>
          <select className="so-select" value={selectedMonth} onChange={(e) => { setSelectedMonth(parseInt(e.target.value, 10)); setSelectedQuarter('none'); }}>
            {MONTHS.map((m, i) => <option key={i} value={i}>{m}</option>)}
          </select>
        </div>
        <div className="so-tc-group">
          <label className="so-label">Select Quarter</label>
          <select className="so-select" value={selectedQuarter} onChange={(e) => { setSelectedQuarter(e.target.value); }}>
            <option value="none">-- Month View --</option>
            <option value="0">Q1 (Jan - Mar)</option>
            <option value="1">Q2 (Apr - Jun)</option>
            <option value="2">Q3 (Jul - Sep)</option>
            <option value="3">Q4 (Oct - Dec)</option>
          </select>
        </div>
      </div>

      {/* ── 3.3 Metric Cards ─────────────────── */}
      {periodData && (
        <div className="so-metrics-row">
          <div className="so-metric-card">
            <span className="so-metric-label">Predicted {periodData.periodLabel} Sales</span>
            <span className="so-metric-value so-metric-value--teal">{periodData.predicted.toLocaleString('en-IN')}</span>
          </div>
          <div className="so-metric-card">
            <span className="so-metric-label">Baseline (Last Year)</span>
            <span className="so-metric-value">{periodData.baseline.toLocaleString('en-IN')}</span>
          </div>
          <div className="so-metric-card">
            <span className="so-metric-label">Stock Status</span>
            <span className="so-metric-value" style={{ color: periodData.change > 0 ? '#10b981' : periodData.change < 0 ? '#ef4444' : '#9ca3af' }}>
              {periodData.change >= 0 ? '+' : ''}{periodData.change.toLocaleString('en-IN')} units
            </span>
            <span className={`so-stock-indicator ${periodData.change > 0 ? 'so-stock-up' : periodData.change < 0 ? 'so-stock-down' : 'so-stock-same'}`}>
              {periodData.change > 0 ? '▲ Increase' : periodData.change < 0 ? '▼ Decrease' : '— Same'}
            </span>
          </div>
        </div>
      )}

      {/* ── 3.4 Action Required Engine ───────── */}
      {periodData && (
        <section className="so-section so-action-section">
          <div className="so-action-header">
            <h3>Action Required</h3>
            <span className="so-action-badge" style={{ background: periodData.badgeColor }}>
              {periodData.badgeText}
            </span>
          </div>

          {/* ── Highlighted Stock Range ────────── */}
          <div className="so-highlight-box so-highlight-stock">
            <span className="so-highlight-icon">📦</span>
            <div>
              <strong>Recommended Stock Range</strong>
              <p>Keep <span className="so-highlight-value">{periodData.stockMin.toLocaleString('en-IN')} – {periodData.stockMax.toLocaleString('en-IN')} products</span> for {periodData.periodLabel}</p>
            </div>
          </div>

          {/* ── Highlighted Discount Recommendation ── */}
          <div className="so-highlight-box so-highlight-discount">
            <span className="so-highlight-icon">💰</span>
            <div>
              <strong>Discount Recommendation: <span className="so-highlight-value">{periodData.discountPct}</span></strong>
              <p className="so-highlight-reason">{periodData.discountReason}</p>
            </div>
          </div>

          <ul className="so-action-list">
            {actions.map((a, i) => (
              <li key={i} className="so-action-item">
                <span className="so-action-icon">{a.icon}</span>
                <div>
                  <strong>{a.title}.</strong> {a.text}
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* ── Save Prediction Dialog ────────── */}
      <SavePredictionDialog
        isOpen={showSaveDialog}
        onClose={() => setShowSaveDialog(false)}
        onSaved={() => {
          setSavedToast(true);
          setTimeout(() => setSavedToast(false), 3000);
        }}
        predictionData={periodData ? {
          ownerName,
          businessName,
          category: viewCategory,
          region,
          state,
          month: selectedMonth,
          year: forecast?.nextYear || 2026,
          predicted: periodData.predicted,
          baseline: periodData.baseline,
          changePct: periodData.changePct,
          discountPct: periodData.discountPct,
          stockMin: periodData.stockMin,
          stockMax: periodData.stockMax,
          demandLevel: periodData.demandLevel,
          festivalName: periodData.topFestival?.name || null,
          periodLabel: periodData.periodLabel,
        } : null}
      />

      {/* ── Predictions Catalog Sidebar ──── */}
      <PredictionsCatalog
        isOpen={showCatalog}
        onClose={() => setShowCatalog(false)}
      />

      {/* ── Saved Toast ────────────────── */}
      {savedToast && (
        <div className="spd-toast">
          ✅ Prediction saved to Catalog!
        </div>
      )}
    </div>
  );
}

export default ShopOwnerAnalytics;
