import { jsPDF } from 'jspdf';
import 'jspdf-autotable';
import html2canvas from 'html2canvas';

/* ── Constants ──────────────────────────────────────── */
const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];

const FESTIVAL_CALENDAR = [
  { date: '2026-01-14', name: 'Pongal / Makar Sankranti', color: '#f59e0b' },
  { date: '2026-03-25', name: 'Holi / Spring Season',     color: '#ec4899' },
  { date: '2026-04-14', name: 'Vishu / Tamil New Year',   color: '#10b981' },
  { date: '2026-08-15', name: 'Independence Day',          color: '#f97316' },
  { date: '2026-08-22', name: 'Onam (Peak)',               color: '#84cc16' },
  { date: '2026-10-02', name: 'Navaratri / Dussehra',     color: '#a855f7' },
  { date: '2026-10-20', name: 'Diwali Shopping Peak',     color: '#eab308' },
  { date: '2026-12-25', name: 'Christmas / Year-End',     color: '#06b6d4' },
];

/* ── Helpers ────────────────────────────────────────── */
function reportId(prefix = 'INV') {
  const now = new Date();
  const yy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const seq = String(Math.floor(Math.random() * 900) + 100);
  return `${prefix}-${yy}-${mm}-${seq}`;
}

function timestamp() {
  return new Date().toLocaleString('en-IN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hour12: true,
  });
}

/* ── Aggregate daily series → monthly data ──────────── */
function aggregateMonthly(series) {
  const buckets = {};
  for (const point of series) {
    const d = new Date(point.date + 'T00:00:00');
    const month = d.getMonth();
    if (!buckets[month]) {
      buckets[month] = { predicted: 0, baseline: 0, festival: null, maxFsi: 0 };
    }
    const fsi = point.fsi || 0;
    buckets[month].predicted += point.value;
    // Baseline = value without FSI boost
    const baseVal = fsi > 0 ? point.value / (1 + fsi / 100) : point.value;
    buckets[month].baseline += baseVal;
    if (point.festival && fsi > buckets[month].maxFsi) {
      buckets[month].maxFsi = fsi;
      buckets[month].festival = {
        name: point.festival,
        boost: 1 + fsi / 100,
      };
    }
  }

  // Also match FESTIVAL_CALENDAR for months that didn't get tagged via series
  FESTIVAL_CALENDAR.forEach(fest => {
    const m = new Date(fest.date + 'T00:00:00').getMonth();
    if (buckets[m] && !buckets[m].festival) {
      buckets[m].festival = { name: fest.name, boost: 1, color: fest.color };
    }
  });

  return Object.keys(buckets)
    .map(Number)
    .sort((a, b) => a - b)
    .map(month => ({
      month,
      monthLabel: MONTHS[month],
      predicted: Math.round(buckets[month].predicted),
      baseline: Math.round(buckets[month].baseline),
      festival: buckets[month].festival,
    }));
}

/* ══════════════════════════════════════════════════════════
   generateInventoryPDF
   ══════════════════════════════════════════════════════════ */
export async function generateInventoryPDF({
  forecastData,
  summary,
  storeDecisions,
  selectedCategory,
  storeName,
  region,
  chartRef,
}) {
  if (!forecastData?.series?.length) {
    alert('No forecast data loaded. Please load the dashboard first.');
    return;
  }

  const doc = new jsPDF('p', 'mm', 'a4');
  const pageW = doc.internal.pageSize.getWidth();
  const pageH = doc.internal.pageSize.getHeight();
  const rid = reportId('INV');
  const year = new Date().getFullYear();
  const footerH = 14;

  const monthly = aggregateMonthly(forecastData.series);
  const totalPredicted = monthly.reduce((s, m) => s + m.predicted, 0);
  const totalBaseline  = monthly.reduce((s, m) => s + m.baseline, 0);
  const overallGrowth  = totalBaseline > 0 ? ((totalPredicted - totalBaseline) / totalBaseline * 100).toFixed(1) : '0.0';
  const peakMonth      = [...monthly].sort((a, b) => b.predicted - a.predicted)[0];
  const festivalMonths = monthly.filter(m => m.festival);
  const topFestival    = [...festivalMonths].sort((a, b) => (b.festival?.boost || 0) - (a.festival?.boost || 0))[0];

  let y;

  function addFooter() {
    const pages = doc.internal.getNumberOfPages();
    for (let p = 1; p <= pages; p++) {
      doc.setPage(p);
      doc.setFillColor(26, 29, 46);
      doc.rect(0, pageH - footerH, pageW, footerH, 'F');
      doc.setTextColor(150, 150, 150);
      doc.setFontSize(8);
      doc.setFont('helvetica', 'normal');
      doc.text(`Powered by Seasonal Demand Forecaster  |  ${rid}  |  ${timestamp()}`, pageW / 2, pageH - 5, { align: 'center' });
      doc.text(`Page ${p} of ${pages}`, pageW - 14, pageH - 5, { align: 'right' });
    }
  }

  function ensureSpace(needed) {
    const available = pageH - footerH - 10;
    if (y + needed > available) {
      doc.addPage();
      y = 20;
    }
  }

  /* ═══════════════════════════════════════════
     PAGE 1: Strategic Executive Summary
     ═══════════════════════════════════════════ */
  // Dark header band
  doc.setFillColor(26, 29, 46);
  doc.rect(0, 0, pageW, 42, 'F');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(18);
  doc.setTextColor(16, 185, 129);
  doc.text('INVENTORY DEMAND FORECAST REPORT', 14, 16);
  doc.setFontSize(11);
  doc.setTextColor(200, 200, 220);
  doc.text(`${storeName || 'Store'}  |  ${region || '—'}  |  ${year}`, 14, 26);
  doc.setFontSize(9);
  doc.setTextColor(160, 165, 180);
  doc.text(`Report: ${rid}  |  Generated: ${timestamp()}`, 14, 34);
  doc.text(`Category: ${selectedCategory}`, pageW - 14, 34, { align: 'right' });

  y = 52;

  // Section title: Executive Highlights
  doc.setTextColor(26, 29, 46);
  doc.setFontSize(15);
  doc.setFont('helvetica', 'bold');
  doc.text('Executive Highlights', 14, y);
  y += 3;
  doc.setDrawColor(16, 185, 129);
  doc.setLineWidth(0.8);
  doc.line(14, y, pageW - 14, y);
  y += 9;

  // Bullet points
  const bullets = [
    `Total Annual Predicted Sales: ${totalPredicted.toLocaleString('en-IN')} units (${overallGrowth >= 0 ? '+' : ''}${overallGrowth}% growth vs baseline)`,
    `Peak Demand Month: ${peakMonth ? MONTHS[peakMonth.month] : '—'} (${peakMonth ? peakMonth.predicted.toLocaleString('en-IN') : 0} units)${topFestival ? ` driven by ${topFestival.festival.name}` : ''}`,
    `Inventory Overview: ${summary?.total || '—'} total SKUs  |  ${summary?.reorder_now || 0} Reorder Now  |  ${summary?.watchlist || 0} Watchlist  |  ${summary?.ok || 0} OK`,
    `Recommended Stock Range: ${Math.round(totalPredicted * 0.75).toLocaleString('en-IN')} – ${Math.round(totalPredicted * 1.10).toLocaleString('en-IN')} units to avoid stockouts`,
    `Store: ${storeName || '—'}  |  Region: ${region || '—'}  |  Category: ${selectedCategory}`,
  ];

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(10);
  doc.setTextColor(40, 40, 50);
  bullets.forEach(line => {
    const lines = doc.splitTextToSize(`•  ${line}`, pageW - 32);
    lines.forEach(l => { doc.text(l, 18, y); y += 6; });
    y += 1;
  });
  y += 4;

  // Embed chart image if available
  if (chartRef?.current) {
    try {
      const chartEl = chartRef.current.canvas || chartRef.current;
      const canvas = await html2canvas(chartEl, {
        backgroundColor: '#0f1225',
        scale: 2,
        useCORS: true,
        logging: false,
      });
      const imgData = canvas.toDataURL('image/png');
      const imgW = pageW - 28;
      const imgH = (canvas.height / canvas.width) * imgW;
      const maxH = Math.min(imgH, 75);
      ensureSpace(maxH + 10);

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(11);
      doc.setTextColor(26, 29, 46);
      doc.text('Annual Visual Trend', 14, y);
      y += 5;
      doc.addImage(imgData, 'PNG', 14, y, imgW, maxH);
      y += maxH + 8;
    } catch (err) {
      console.warn('Chart capture skipped:', err.message);
    }
  }

  /* ═══════════════════════════════════════════
     PAGES 2–N: Monthly Execution Playbook
     ═══════════════════════════════════════════ */
  doc.addPage();
  y = 20;

  doc.setFillColor(26, 29, 46);
  doc.rect(0, 0, pageW, 22, 'F');
  doc.setTextColor(16, 185, 129);
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text('Monthly Execution Playbook', 14, 15);
  doc.setTextColor(200, 200, 220);
  doc.setFontSize(9);
  doc.text(`${selectedCategory}  |  ${year}`, pageW - 14, 15, { align: 'right' });
  y = 30;

  monthly.forEach((m) => {
    const growth = m.baseline > 0 ? ((m.predicted - m.baseline) / m.baseline * 100) : 0;
    const growthStr = growth.toFixed(0);
    const stockMin = Math.round(m.predicted * 0.75).toLocaleString('en-IN');
    const stockMax = Math.round(m.predicted * 1.10).toLocaleString('en-IN');
    const hasFestival = !!m.festival;

    ensureSpace(52);

    // Month title bar
    doc.setFillColor(26, 29, 46);
    doc.roundedRect(14, y, pageW - 28, 8, 2, 2, 'F');
    doc.setTextColor(16, 185, 129);
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.text(`${MONTHS[m.month]} Strategy`, 18, y + 5.5);
    if (hasFestival) {
      doc.setTextColor(245, 158, 11);
      doc.setFontSize(9);
      doc.text(`Festival: ${m.festival.name}`, pageW - 18, y + 5.5, { align: 'right' });
    }
    y += 12;

    doc.setFontSize(9.5);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(40, 40, 50);

    // Forecast line
    doc.setFont('helvetica', 'bold');
    doc.text('Forecast:', 18, y);
    doc.setFont('helvetica', 'normal');
    const forecastLine = `Predicted sales of ${m.predicted.toLocaleString('en-IN')} units against a baseline of ${m.baseline.toLocaleString('en-IN')} (${growth >= 0 ? '+' : ''}${growthStr}% change).`;
    const fLines = doc.splitTextToSize(forecastLine, pageW - 52);
    doc.text(fLines, 40, y);
    y += fLines.length * 5 + 2;

    // Inventory Target line
    doc.setFont('helvetica', 'bold');
    doc.text('Inventory Target:', 18, y);
    doc.setFont('helvetica', 'normal');
    doc.text(`Maintain stock levels within ${stockMin} – ${stockMax} units.`, 52, y);
    y += 7;

    // Action Required
    doc.setFont('helvetica', 'bold');
    doc.text('Action Required:', 18, y);
    doc.setFont('helvetica', 'normal');

    let actionText, actionColor;
    if (hasFestival && growth >= 30) {
      actionColor = [245, 158, 11];
      actionText = `High Demand (Festival: ${m.festival.name}): Increase stock levels 2 weeks prior. Limit discount to 5% to protect margins.`;
    } else if (growth >= 40) {
      actionColor = [239, 68, 68];
      actionText = `REORDER NOW: Extreme demand surge (+${growthStr}%). Pre-order immediately. Keep discount at 5% maximum.`;
    } else if (hasFestival) {
      actionColor = [245, 158, 11];
      actionText = `Festival Prep (${m.festival.name}): Stock up in advance. Apply 8% discount to drive early sales.`;
    } else if (growth >= 15) {
      actionColor = [16, 185, 129];
      actionText = `Growing Demand: Sales trending up ${growthStr}%. Maintain 8% discount. Monitor inventory weekly.`;
    } else if (growth >= -10) {
      actionColor = [16, 185, 129];
      actionText = 'Stable Demand: Continue normal operations. Apply a 10% discount to maintain steady stock turnover.';
    } else {
      actionColor = [239, 68, 68];
      actionText = `Low Demand: Sales declining ${growthStr}%. Apply 15-20% discount to clear stock and reduce holding costs.`;
    }

    doc.setTextColor(...actionColor);
    const aLines = doc.splitTextToSize(actionText, pageW - 52);
    doc.text(aLines, 52, y);
    y += aLines.length * 5 + 3;

    // Separator
    doc.setDrawColor(220, 225, 230);
    doc.setLineWidth(0.3);
    doc.line(18, y, pageW - 18, y);
    y += 6;
  });

  /* ═══════════════════════════════════════════
     FINAL PAGE: Annual Impact & Summary
     ═══════════════════════════════════════════ */
  doc.addPage();
  y = 20;

  doc.setFillColor(26, 29, 46);
  doc.rect(0, 0, pageW, 22, 'F');
  doc.setTextColor(16, 185, 129);
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text('Annual Impact & Summary', 14, 15);
  y = 30;

  // Festival Impact Table
  doc.setTextColor(26, 29, 46);
  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.text('Festival Impact Analysis', 14, y);
  y += 3;
  doc.setDrawColor(16, 185, 129);
  doc.setLineWidth(0.6);
  doc.line(14, y, pageW - 14, y);
  y += 4;

  const festRows = monthly
    .filter(m => m.festival)
    .map(m => {
      const lift = m.baseline > 0 ? ((m.predicted - m.baseline) / m.baseline * 100).toFixed(0) : '—';
      return [
        m.festival.name,
        MONTHS[m.month],
        m.baseline.toLocaleString('en-IN'),
        m.predicted.toLocaleString('en-IN'),
        `+${lift}%`,
      ];
    });

  if (festRows.length > 0) {
    doc.autoTable({
      startY: y,
      head: [['Festival Name', 'Month', 'Baseline', 'Predicted', 'Sales Lift %']],
      body: festRows,
      styles: { fontSize: 9, cellPadding: 4, textColor: [40, 40, 40] },
      headStyles: { fillColor: [26, 29, 46], textColor: [16, 185, 129], fontStyle: 'bold' },
      alternateRowStyles: { fillColor: [245, 247, 250] },
      columnStyles: {
        2: { halign: 'right' },
        3: { halign: 'right' },
        4: { halign: 'center', textColor: [16, 185, 129], fontStyle: 'bold' },
      },
      margin: { left: 14, right: 14 },
    });
    y = doc.lastAutoTable.finalY + 12;
  } else {
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(120, 120, 130);
    doc.text('No major festivals affect this category in the selected region.', 14, y);
    y += 12;
  }

  // Strategic Conclusion
  ensureSpace(40);
  doc.setFillColor(240, 253, 244);
  doc.roundedRect(14, y, pageW - 28, 32, 3, 3, 'F');
  doc.setDrawColor(16, 185, 129);
  doc.setLineWidth(0.5);
  doc.roundedRect(14, y, pageW - 28, 32, 3, 3, 'S');

  doc.setTextColor(26, 29, 46);
  doc.setFontSize(11);
  doc.setFont('helvetica', 'bold');
  doc.text('Strategic Conclusion', 20, y + 8);

  doc.setFontSize(9.5);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(50, 55, 65);

  let conclusionText;
  if (topFestival) {
    const topLift = topFestival.festival.boost ? ((topFestival.festival.boost - 1) * 100).toFixed(0) : '—';
    conclusionText = `The highest growth of +${topLift}% in ${MONTHS[topFestival.month]} (${topFestival.festival.name}) is the primary area for capital investment. Focus procurement, marketing budgets, and staffing around this peak to maximize revenue for ${selectedCategory}.`;
  } else {
    conclusionText = `Category "${selectedCategory}" shows steady ${overallGrowth}% annual growth. Maintain balanced inventory levels and apply standard discount strategies throughout the year.`;
  }
  const cLines = doc.splitTextToSize(conclusionText, pageW - 44);
  doc.text(cLines, 20, y + 15);

  // Footers
  addFooter();

  doc.save(`InventoryForecast_${(storeName || 'Store').replace(/[^a-zA-Z0-9]/g, '_')}_${selectedCategory.replace(/[^a-zA-Z0-9]/g, '_')}_${year}.pdf`);
}
