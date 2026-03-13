import React, { useMemo, useRef, useImperativeHandle } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { TrendingUp } from 'lucide-react';
import { buildFestivalMarkers, FestivalMarkersLegend } from './FestivalMarkers';

ChartJS.register(
  CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler
);

function getWeekStart(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  const day = d.getDay();
  d.setDate(d.getDate() + (day === 0 ? -6 : 1 - day));
  return d.toISOString().split('T')[0];
}

const ForecastChart = React.forwardRef(function ForecastChart({ data, category, festivals = [] }, forwardedRef) {
  const chartRef = useRef(null);

  // Expose chart instance to parent for PDF capture
  useImperativeHandle(forwardedRef, () => chartRef.current, []);

  // ── 1. Aggregate daily → weekly + rolling avg + festival markers ──────────
  const { weeklyLabels, weeklyValues, rollingAvg, festivalMarkers } = useMemo(() => {
    if (!data?.series?.length) {
      return { weeklyLabels: [], weeklyValues: [], rollingAvg: [], festivalMarkers: [] };
    }

    const weekMap = new Map();
    for (const point of data.series) {
      const ws = getWeekStart(point.date);
      if (!weekMap.has(ws)) weekMap.set(ws, { sum: 0, festival: null, fsi: 0 });
      const e = weekMap.get(ws);
      e.sum += point.value;
      const ptFsi = point.fsi || 0;
      if (ptFsi > e.fsi) { e.fsi = ptFsi; e.festival = point.festival || null; }
    }

    const sorted = [...weekMap.keys()].sort();
    const labels = sorted.map(ws => {
      const d = new Date(ws + 'T00:00:00');
      return d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
    });
    const values = sorted.map(ws => Math.round(weekMap.get(ws).sum));

    // 4-week rolling average
    const rolling = values.map((_, i) => {
      const win = values.slice(Math.max(0, i - 3), i + 1);
      return Math.round(win.reduce((a, b) => a + b, 0) / win.length);
    });

    // Match festival dates → nearest week index
    const markers = buildFestivalMarkers(sorted, festivals, new Map(sorted.map((ws) => [ws, weekMap.get(ws)?.fsi || 0])));

    return { weeklyLabels: labels, weeklyValues: values, rollingAvg: rolling, festivalMarkers: markers };
  }, [data, festivals]);

  // ── 2. Custom plugin: vertical festival lines + badge labels ──────────────
  const festivalLinesPlugin = useMemo(() => ({
    id: 'festivalLines',
    afterDraw(chart) {
      if (!festivalMarkers.length) return;
      const { ctx, chartArea, scales } = chart;
      ctx.save();
      festivalMarkers.forEach(({ index, color, short, fsi }) => {
        const x = scales.x.getPixelForValue(index);
        if (x < chartArea.left || x > chartArea.right) return;

        // Dashed vertical line
        ctx.strokeStyle = color;
        ctx.setLineDash([4, 3]);
        ctx.lineWidth = 1.5;
        ctx.globalAlpha = 0.6;
        ctx.beginPath();
        ctx.moveTo(x, chartArea.top + 20);
        ctx.lineTo(x, chartArea.bottom);
        ctx.stroke();

        // Floating badge
        ctx.globalAlpha = 1;
        ctx.setLineDash([]);
        const label = `${short}`;
        const pad = 5;
        ctx.font = 'bold 9px Inter, system-ui, sans-serif';
        const tw = ctx.measureText(label).width;
        const bw = tw + pad * 2, bh = 15;
        const bx = Math.min(Math.max(x - bw / 2, chartArea.left + 2), chartArea.right - bw - 2);
        const by = chartArea.top;
        ctx.fillStyle = color;
        if (ctx.roundRect) { ctx.beginPath(); ctx.roundRect(bx, by, bw, bh, 3); ctx.fill(); }
        else ctx.fillRect(bx, by, bw, bh);
        ctx.fillStyle = '#fff';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText(label, bx + pad, by + bh / 2);
      });
      ctx.restore();
    }
  }), [festivalMarkers]);

  // ── 3. Custom plugin: month separator gridlines ───────────────────────────
  const monthGridPlugin = useMemo(() => ({
    id: 'monthGrid',
    afterDraw(chart) {
      const { ctx, chartArea, scales } = chart;
      ctx.save();
      weeklyLabels.forEach((label, i) => {
        if (/\b1$/.test(label)) {
          const x = scales.x.getPixelForValue(i);
          ctx.strokeStyle = 'rgba(255,255,255,0.13)';
          ctx.setLineDash([]);
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(x, chartArea.top);
          ctx.lineTo(x, chartArea.bottom);
          ctx.stroke();
        }
      });
      ctx.restore();
    }
  }), [weeklyLabels]);

  // ── 4. chartData + options ────────────────────────────────────────────────
  const festByIndex = useMemo(() => {
    const m = {};
    festivalMarkers.forEach(f => { m[f.index] = f; });
    return m;
  }, [festivalMarkers]);

  const { chartData, options } = useMemo(() => {
    if (!weeklyValues.length) return { chartData: null, options: {} };

    const minVal = Math.min(...weeklyValues);
    const maxVal = Math.max(...weeklyValues);
    const yMin = Math.max(0, Math.floor(minVal * 0.82 / 50) * 50);
    const yMax = Math.ceil(maxVal * 1.10 / 50) * 50;

    const cData = {
      labels: weeklyLabels,
      datasets: [
        {
          label: 'Weekly Sales',
          data: weeklyValues,
          borderColor: '#06b6d4',
          backgroundColor: 'rgba(6, 182, 212, 0.10)',
          borderWidth: 2,
          tension: 0.35,
          fill: true,
          pointRadius: (ctx) => festByIndex[ctx.dataIndex] ? 5 : 2,
          pointBackgroundColor: (ctx) => {
            const f = festByIndex[ctx.dataIndex];
            return f ? f.color : '#06b6d4';
          },
          pointHoverRadius: 7,
          pointHoverBorderColor: '#fff',
          pointHoverBorderWidth: 2,
          order: 2,
        },
        {
          label: '4-Wk Trend',
          data: rollingAvg,
          borderColor: 'rgba(251, 191, 36, 0.85)',
          backgroundColor: 'transparent',
          borderWidth: 2,
          borderDash: [7, 4],
          tension: 0.5,
          fill: false,
          pointRadius: 0,
          pointHoverRadius: 4,
          order: 1,
        },
      ],
    };

    const opts = {
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { top: 24, right: 8 } },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          align: 'end',
          labels: { color: '#9ca3af', boxWidth: 14, padding: 16, font: { size: 11 }, usePointStyle: true },
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: 'rgba(10, 18, 35, 0.97)',
          padding: 14,
          titleColor: '#f1f5f9',
          bodyColor: '#cbd5e1',
          borderColor: '#06b6d4',
          borderWidth: 1,
          displayColors: true,
          callbacks: {
            title: (items) => {
              const idx = items[0]?.dataIndex;
              const fest = festByIndex[idx];
              return fest
                ? `📅 Week of ${weeklyLabels[idx]}   ${fest.markerEmoji || '🎉'} ${fest.name}`
                : `📅 Week of ${weeklyLabels[idx]}`;
            },
            label: (context) => {
              const val = context.parsed.y;
              if (context.datasetIndex === 0) {
                const fest = festByIndex[context.dataIndex];
                if (fest) {
                  return [
                    `  Weekly Sales: ${val.toLocaleString('en-IN')}`,
                    `  Festival: ${fest.name}`,
                    `  Date: ${fest.date}`,
                    `  Type: ${fest.type === 'pan-indian' ? 'Pan-Indian' : 'Local'}`,
                    `  Impact: ${fest.impactMultiplier.toFixed(1)}×`,
                  ];
                }
                return `  Weekly Sales: ${val.toLocaleString('en-IN')}`;
              }
              return `  4-Wk Trend: ${val.toLocaleString('en-IN')}`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false },
          ticks: { color: '#6b7280', maxRotation: 0, autoSkipPadding: 40, font: { size: 11 } },
        },
        y: {
          min: yMin,
          max: yMax,
          grid: { color: 'rgba(255,255,255,0.06)', drawBorder: false },
          ticks: { color: '#9ca3af', font: { size: 11 }, callback: (v) => v.toLocaleString('en-IN') },
        },
      },
      interaction: { mode: 'index', axis: 'x', intersect: false },
    };

    return { chartData: cData, options: opts };
  }, [weeklyLabels, weeklyValues, rollingAvg, festByIndex]);

  // ── 5. Render ─────────────────────────────────────────────────────────────
  if (!chartData) {
    return (
      <div className="forecast-chart">
        <div className="chart-header"><TrendingUp size={20} /><h3>Sales Forecast — {category} Category</h3></div>
        <div className="chart-empty">No forecast data available for this category.</div>
      </div>
    );
  }

  return (
    <div className="forecast-chart">
      <div className="chart-header">
        <TrendingUp size={20} />
        <h3>Sales Forecast — {category} Category</h3>
        <div className="festival-pills">
          {festivalMarkers.map(f => (
            <span key={`${f.short}-${f.date}`} className="festival-pill"
              style={{ borderColor: f.color, color: f.color }} title={f.name}>
              {f.short}
            </span>
          ))}
        </div>
      </div>
      <FestivalMarkersLegend festivals={festivalMarkers} />
      <div className="chart-container">
        <Line ref={chartRef} data={chartData} options={options} plugins={[festivalLinesPlugin, monthGridPlugin]} />
      </div>
    </div>
  );
});

export default ForecastChart;