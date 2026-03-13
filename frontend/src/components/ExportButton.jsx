import React, { useState, useEffect, useRef, useCallback } from 'react';
import * as XLSX from 'xlsx';
import { jsPDF } from 'jspdf';
import 'jspdf-autotable';
import html2canvas from 'html2canvas';
import './ExportButton.css';

/* ── Constants ───────────────────────────────────────── */
const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];

/* ── Category-aware supplier mapping ─────────────────── */
const CATEGORY_SUPPLIERS = {
  'fresh produce':       ['Fresh Farms Ltd', 'Green Valley Agro', 'Organic India Traders', 'Farm Direct Suppliers', 'Nature Fresh Co.'],
  'dairy':               ['Amul Distributors', 'Mother Dairy Wholesale', 'Nandini Dairy Supply', 'Dairy Direct India', 'Fresh Dairy Traders'],
  'groceries':           ['India FMCG Distributors', 'Kerala Wholesale Traders', 'National Goods Corp', 'Reliance FMCG Supply', 'Big Basket Wholesale'],
  'electronics':         ['Vijay Electronics Wholesale', 'Tech India Distributors', 'Samsung Authorized Supply', 'ElecMart Wholesale', 'Digital India Traders'],
  'clothing':            ['Raymond Wholesale', 'Textile India Traders', 'Fashion Hub Distributors', 'Bombay Clothing Supply', 'Style India Wholesale'],
  'beverages':           ['Coca-Cola Distributors', 'Pepsi India Supply', 'Beverage India Wholesale', 'Fresh Juice Traders', 'National Beverages Corp'],
  'snacks':              ['Haldiram Distributors', 'ITC Foods Wholesale', 'Balaji Snacks Supply', 'Parle Agro Traders', 'Snack India Corp'],
  'personal care':       ['HUL Distributors', 'P&G India Wholesale', 'Dabur Supply Chain', 'Himalaya Wholesale', 'Personal Care India'],
  'household':           ['Godrej Distributors', 'Prestige India Supply', 'TTK Wholesale Traders', 'Home Essentials Corp', 'Household India Wholesale'],
};
const DEFAULT_SUPPLIERS = ['India FMCG Distributors', 'National Goods Corp', 'South Star Suppliers', 'Kerala Wholesale Traders', 'General Trade Suppliers'];

function getSuppliersForCategory(category) {
  if (!category) return DEFAULT_SUPPLIERS;
  const lower = category.toLowerCase();
  for (const [key, suppliers] of Object.entries(CATEGORY_SUPPLIERS)) {
    if (lower.includes(key)) return suppliers;
  }
  return DEFAULT_SUPPLIERS;
}

const CATEGORY_RATES = {
  'Fresh Produce': 45,
  'Dairy':         60,
  'Groceries':     120,
  'Electronics':   500,
  'Clothing':      350,
  'Beverages':     80,
  'Snacks':        90,
  'Personal Care': 150,
  'Household':     200,
};
const DEFAULT_RATE = 100;
const GST_RATE = 0.05;

/* ── Helper: get rate for a category string ─────────── */
function getRate(category) {
  if (!category) return DEFAULT_RATE;
  const lower = category.toLowerCase();
  for (const [key, rate] of Object.entries(CATEGORY_RATES)) {
    if (lower.includes(key.toLowerCase())) return rate;
  }
  return DEFAULT_RATE;
}

/* ── Helper: generate report ID ─────────────────────── */
function reportId(prefix = 'FR') {
  const now = new Date();
  const yy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const seq = String(Math.floor(Math.random() * 900) + 100);
  return `${prefix}-${yy}-${mm}-${seq}`;
}

/* ── Helper: timestamp string ───────────────────────── */
function timestamp() {
  return new Date().toLocaleString('en-IN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hour12: true,
  });
}

/* ══════════════════════════════════════════════════════════════
   PO GENERATOR DIALOG — with month tick-mark selection
   ══════════════════════════════════════════════════════════════ */
function POGeneratorDialog({ open, onClose, allMonthlyRows, shopOwnerInfo, category }) {
  const suppliers = getSuppliersForCategory(category);
  const [supplier, setSupplier]             = useState(suppliers[0]);
  const [deliveryDate, setDeliveryDate]     = useState('');
  const [generating, setGenerating]         = useState(false);
  const [selectedMonths, setSelectedMonths] = useState({});

  useEffect(() => {
    if (open) {
      const d = new Date();
      d.setDate(d.getDate() + 7);
      setDeliveryDate(d.toISOString().split('T')[0]);
      setSupplier(suppliers[0]);
      // Pre-select all REORDER NOW months
      const preSelected = {};
      allMonthlyRows.forEach(row => {
        if (row.decision === 'REORDER NOW') preSelected[row.month] = true;
      });
      setSelectedMonths(preSelected);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  if (!open) return null;

  const toggleMonth = (month) => {
    setSelectedMonths(prev => ({ ...prev, [month]: !prev[month] }));
  };

  const toggleAll = () => {
    const allSelected = allMonthlyRows.every(r => selectedMonths[r.month]);
    if (allSelected) {
      setSelectedMonths({});
    } else {
      const all = {};
      allMonthlyRows.forEach(r => { all[r.month] = true; });
      setSelectedMonths(all);
    }
  };

  const selectedRows = allMonthlyRows.filter(r => selectedMonths[r.month]);

  const subtotal = selectedRows.reduce((s, row) => {
    const rate = getRate(row.category || category);
    return s + (row.reorderQty * rate);
  }, 0);
  const gst = Math.round(subtotal * GST_RATE);
  const grandTotal = subtotal + gst;

  const handleGenerate = async () => {
    if (selectedRows.length === 0) { alert('Please select at least one month.'); return; }
    setGenerating(true);
    try {
      await generatePO(selectedRows, shopOwnerInfo, supplier, deliveryDate, category);
    } finally {
      setGenerating(false);
      onClose();
    }
  };

  return (
    <div className="po-overlay" onClick={onClose}>
      <div className="po-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="po-dialog-header">
          <h3>📋 Generate Purchase Order</h3>
          <button className="po-close" onClick={onClose}>✕</button>
        </div>

        <div className="po-dialog-body">
          <p className="po-item-count">
            Category: <strong>{category}</strong> — Select months to include in PO
          </p>

          <label className="po-label">Select Supplier ({category})</label>
          <select className="po-select" value={supplier} onChange={(e) => setSupplier(e.target.value)}>
            {suppliers.map(s => <option key={s} value={s}>{s}</option>)}
          </select>

          <label className="po-label">Expected Delivery Date</label>
          <input
            type="date"
            className="po-date"
            value={deliveryDate}
            onChange={(e) => setDeliveryDate(e.target.value)}
            min={new Date().toISOString().split('T')[0]}
          />

          {/* Month selection table with checkboxes */}
          <div className="po-preview">
            <table className="po-table">
              <thead>
                <tr>
                  <th style={{ width: 36 }}>
                    <input
                      type="checkbox"
                      checked={allMonthlyRows.length > 0 && allMonthlyRows.every(r => selectedMonths[r.month])}
                      onChange={toggleAll}
                      className="po-checkbox"
                      title="Select all"
                    />
                  </th>
                  <th>Month</th>
                  <th>Decision</th>
                  <th>Qty</th>
                  <th>Rate (₹)</th>
                  <th>Amount (₹)</th>
                </tr>
              </thead>
              <tbody>
                {allMonthlyRows.map((row, i) => {
                  const rate = getRate(row.category || category);
                  const isReorder = row.decision === 'REORDER NOW';
                  return (
                    <tr key={i} className={selectedMonths[row.month] ? 'po-row-selected' : ''}>
                      <td>
                        <input
                          type="checkbox"
                          checked={!!selectedMonths[row.month]}
                          onChange={() => toggleMonth(row.month)}
                          className="po-checkbox"
                        />
                      </td>
                      <td>
                        {row.monthLabel}
                        {row.festival ? <span className="po-fest-badge">{row.festival.name}</span> : null}
                      </td>
                      <td>
                        <span className={`po-decision-tag ${isReorder ? 'po-decision-reorder' : row.decision === 'WATCHLIST' ? 'po-decision-watch' : 'po-decision-ok'}`}>
                          {row.decision}
                        </span>
                      </td>
                      <td>{row.reorderQty.toLocaleString('en-IN')}</td>
                      <td>{rate.toLocaleString('en-IN')}</td>
                      <td>{(row.reorderQty * rate).toLocaleString('en-IN')}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Totals summary */}
          {selectedRows.length > 0 && (
            <div className="po-totals">
              <div className="po-total-line"><span>Subtotal:</span><span>₹{subtotal.toLocaleString('en-IN')}</span></div>
              <div className="po-total-line"><span>GST @5%:</span><span>₹{gst.toLocaleString('en-IN')}</span></div>
              <div className="po-total-line po-total-grand"><span>Grand Total:</span><span>₹{grandTotal.toLocaleString('en-IN')}</span></div>
            </div>
          )}
        </div>

        <div className="po-dialog-footer">
          <span className="po-selected-info">{selectedRows.length} of {allMonthlyRows.length} month(s) selected</span>
          <button className="po-btn po-btn--cancel" onClick={onClose}>Cancel</button>
          <button className="po-btn po-btn--generate" onClick={handleGenerate} disabled={generating || selectedRows.length === 0}>
            {generating ? 'Generating…' : `📄 Generate PO (${selectedRows.length} items)`}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── PO PDF generation logic ─────────────────────────── */
async function generatePO(selectedRows, info, supplier, deliveryDate, category) {
  const doc = new jsPDF('p', 'mm', 'a4');
  const pageW = doc.internal.pageSize.getWidth();
  const poId = reportId('PO');

  // Header
  doc.setFillColor(26, 29, 46);
  doc.rect(0, 0, pageW, 38, 'F');
  doc.setTextColor(16, 185, 129);
  doc.setFontSize(18);
  doc.setFont('helvetica', 'bold');
  doc.text('PURCHASE ORDER', 14, 18);
  doc.setFontSize(10);
  doc.setTextColor(200, 200, 200);
  doc.text(`PO #: ${poId}`, 14, 28);
  doc.text(`Date: ${timestamp()}`, 14, 34);
  doc.text('QRS Technologies', pageW - 14, 18, { align: 'right' });
  doc.text(`Category: ${category}`, pageW - 14, 28, { align: 'right' });
  doc.text(`Delivery: ${deliveryDate}`, pageW - 14, 34, { align: 'right' });

  let y = 48;

  // Buyer / Supplier
  doc.setTextColor(40, 40, 40);
  doc.setFontSize(10);
  doc.setFont('helvetica', 'bold');
  doc.text('BUYER:', 14, y);
  doc.setFont('helvetica', 'normal');
  doc.text(`${info.name || 'Shop Owner'}  —  ${info.business || 'Business'}`, 14, y + 6);
  doc.text(`${info.region || ''}, ${info.state || ''}`, 14, y + 12);

  doc.setFont('helvetica', 'bold');
  doc.text('SUPPLIER:', pageW / 2 + 10, y);
  doc.setFont('helvetica', 'normal');
  doc.text(supplier, pageW / 2 + 10, y + 6);

  y += 24;

  // Table
  const rows = selectedRows.map((row, i) => {
    const cat = row.category || category || 'General';
    const rate = getRate(cat);
    const qty = row.reorderQty;
    const amt = qty * rate;
    return [i + 1, `${row.monthLabel} — ${cat}`, qty.toLocaleString('en-IN'), `₹${rate.toLocaleString('en-IN')}`, `₹${amt.toLocaleString('en-IN')}`];
  });

  const subtotal = selectedRows.reduce((s, row) => {
    const rate = getRate(row.category || category);
    return s + row.reorderQty * rate;
  }, 0);
  const gst = Math.round(subtotal * GST_RATE);
  const grandTotal = subtotal + gst;

  doc.autoTable({
    startY: y,
    head: [['#', 'Item Description', 'Qty', 'Rate', 'Amount']],
    body: rows,
    styles: { fontSize: 9, cellPadding: 4 },
    headStyles: { fillColor: [26, 29, 46], textColor: [16, 185, 129], fontStyle: 'bold' },
    alternateRowStyles: { fillColor: [245, 247, 250] },
    margin: { left: 14, right: 14 },
  });

  y = doc.lastAutoTable.finalY + 10;

  // Totals
  const totalsX = pageW - 70;
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(40, 40, 40);
  doc.text('Subtotal:', totalsX, y);
  doc.text(`₹${subtotal.toLocaleString('en-IN')}`, pageW - 14, y, { align: 'right' });
  y += 7;
  doc.text(`GST @${GST_RATE * 100}%:`, totalsX, y);
  doc.text(`₹${gst.toLocaleString('en-IN')}`, pageW - 14, y, { align: 'right' });
  y += 7;
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(12);
  doc.text('Grand Total:', totalsX, y);
  doc.setTextColor(16, 185, 129);
  doc.text(`₹${grandTotal.toLocaleString('en-IN')}`, pageW - 14, y, { align: 'right' });

  // Footer
  const pageH = doc.internal.pageSize.getHeight();
  doc.setFillColor(26, 29, 46);
  doc.rect(0, pageH - 14, pageW, 14, 'F');
  doc.setTextColor(150, 150, 150);
  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  doc.text(`Generated by Seasonal Demand Forecaster  |  ${timestamp()}`, pageW / 2, pageH - 5, { align: 'center' });

  doc.save(`PurchaseOrder_${category.replace(/[^a-zA-Z0-9]/g, '_')}_${poId}.pdf`);
}

/* ══════════════════════════════════════════════════════════════
   EXCEL EXPORT — now supports all categories from forecastMap
   ══════════════════════════════════════════════════════════════ */
function exportExcel(forecastMap, shopOwnerInfo, activeCategory) {
  const wb = XLSX.utils.book_new();
  const categories = Object.keys(forecastMap);

  // One Forecast sheet per category
  categories.forEach(cat => {
    const forecast = forecastMap[cat];
    if (!forecast?.monthly) return;
    const forecastRows = forecast.monthly.map(m => ({
      Month:           MONTHS[m.month],
      'Predicted Sales': m.predicted,
      'Baseline Sales':  m.baseline,
      'Growth (%)':      m.baseline > 0 ? Math.round(((m.predicted - m.baseline) / m.baseline) * 100) : 0,
      Festival:          m.festival ? m.festival.name : '—',
      'Festival Boost':  m.festival ? `${((m.festival.boost - 1) * 100).toFixed(0)}%` : '—',
      'FSI Index':       m.festival ? m.festival.boost.toFixed(2) : '1.00',
    }));
    const ws = XLSX.utils.json_to_sheet(forecastRows);
    ws['!cols'] = [{ wch: 12 }, { wch: 16 }, { wch: 14 }, { wch: 10 }, { wch: 20 }, { wch: 14 }, { wch: 10 }];
    const sheetName = `Forecast - ${cat}`.substring(0, 31);
    XLSX.utils.book_append_sheet(wb, ws, sheetName);
  });

  // One Inventory sheet per category
  categories.forEach(cat => {
    const forecast = forecastMap[cat];
    if (!forecast?.monthly) return;
    const invRows = forecast.monthly.map(m => {
      const stockMin = Math.round(m.predicted * 0.75);
      const stockMax = Math.round(m.predicted * 1.10);
      const changePct = m.baseline > 0 ? Math.round(((m.predicted - m.baseline) / m.baseline) * 100) : 0;
      let decision;
      if (changePct >= 40) decision = 'REORDER NOW';
      else if (changePct >= 15) decision = 'WATCHLIST';
      else decision = 'OK';
      return {
        Month:             MONTHS[m.month],
        'Predicted Sales': m.predicted,
        'Stock Min':       stockMin,
        'Stock Max':       stockMax,
        'Days of Supply':  Math.round(stockMax / (m.predicted / 30)),
        Decision:          decision,
        Festival:          m.festival ? m.festival.name : '—',
      };
    });
    const ws = XLSX.utils.json_to_sheet(invRows);
    ws['!cols'] = [{ wch: 12 }, { wch: 16 }, { wch: 10 }, { wch: 10 }, { wch: 14 }, { wch: 14 }, { wch: 20 }];
    const sheetName = `Inventory - ${cat}`.substring(0, 31);
    XLSX.utils.book_append_sheet(wb, ws, sheetName);
  });

  // Profile sheet
  const profileData = [
    { Field: 'Owner Name',       Value: shopOwnerInfo.name || '—' },
    { Field: 'Business Name',    Value: shopOwnerInfo.business || '—' },
    { Field: 'Region',           Value: shopOwnerInfo.region || '—' },
    { Field: 'State',            Value: shopOwnerInfo.state || '—' },
    { Field: 'Categories',       Value: categories.join(', ') },
    { Field: 'Forecast Year',    Value: forecastMap[categories[0]]?.nextYear || '—' },
    { Field: 'Generated',        Value: timestamp() },
  ];
  const ws3 = XLSX.utils.json_to_sheet(profileData);
  ws3['!cols'] = [{ wch: 16 }, { wch: 50 }];
  XLSX.utils.book_append_sheet(wb, ws3, 'Profile');

  XLSX.writeFile(wb, `SalesForecast_${shopOwnerInfo.business || 'Report'}_${new Date().getFullYear()}.xlsx`);
}

/* ══════════════════════════════════════════════════════════════
   PDF REPORT — Strategic Executive Playbook Format
   ══════════════════════════════════════════════════════════════ */
async function exportPDF(forecastMap, shopOwnerInfo, activeCategory, chartRef) {
  const doc = new jsPDF('p', 'mm', 'a4');
  const pageW = doc.internal.pageSize.getWidth();
  const pageH = doc.internal.pageSize.getHeight();
  const rid = reportId('FR');
  const forecast = forecastMap[activeCategory];
  const monthly = forecast?.monthly || [];
  const year = forecast?.nextYear || new Date().getFullYear();
  const allCategories = Object.keys(forecastMap);
  const footerH = 14;

  // Gather aggregated stats across ALL categories
  let grandTotalPredicted = 0, grandTotalBaseline = 0;
  allCategories.forEach(cat => {
    const f = forecastMap[cat];
    if (f?.monthly) {
      grandTotalPredicted += f.monthly.reduce((s, m) => s + m.predicted, 0);
      grandTotalBaseline  += f.monthly.reduce((s, m) => s + m.baseline, 0);
    }
  });

  // Active category stats
  const totalPredicted = monthly.reduce((s, m) => s + m.predicted, 0);
  const totalBaseline  = monthly.reduce((s, m) => s + m.baseline, 0);
  const overallGrowth  = totalBaseline > 0 ? ((totalPredicted - totalBaseline) / totalBaseline * 100).toFixed(1) : '0.0';
  const peakMonth      = [...monthly].sort((a, b) => b.predicted - a.predicted)[0];
  const festivalMonths = monthly.filter(m => m.festival);
  const topFestival    = [...festivalMonths].sort((a, b) => (b.festival?.boost || 0) - (a.festival?.boost || 0))[0];

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

  /* ══════════════════════════════════════════════
     PAGE 1: Strategic Executive Summary
     ══════════════════════════════════════════════ */
  // Dark header band
  doc.setFillColor(26, 29, 46);
  doc.rect(0, 0, pageW, 42, 'F');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(18);
  doc.setTextColor(16, 185, 129);
  doc.text('SALES DEMAND FORECAST REPORT', 14, 16);
  doc.setFontSize(11);
  doc.setTextColor(200, 200, 220);
  doc.text(`${shopOwnerInfo.business || 'QRS Technologies'}  |  ${year}`, 14, 26);
  doc.setFontSize(9);
  doc.setTextColor(160, 165, 180);
  doc.text(`Report: ${rid}  |  Generated: ${timestamp()}`, 14, 34);
  doc.text(`Category: ${activeCategory}  |  Region: ${shopOwnerInfo.region || '—'}`, pageW - 14, 34, { align: 'right' });
  doc.text(`Owner: ${shopOwnerInfo.name || '—'}`, pageW - 14, 26, { align: 'right' });

  let y = 52;

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
    `Peak Demand Month: ${peakMonth ? MONTHS[peakMonth.month] : '—'} (${peakMonth ? peakMonth.predicted.toLocaleString('en-IN') : 0} units)${topFestival ? ` driven by ${topFestival.festival.name} festival` : ''}`,
    `Overall Inventory Strategy: Maintain annual stock between ${Math.round(totalPredicted * 0.75).toLocaleString('en-IN')} and ${Math.round(totalPredicted * 1.10).toLocaleString('en-IN')} units to avoid stockouts`,
    allCategories.length > 1
      ? `Multi-Category Report: ${allCategories.length} categories analyzed (${allCategories.join(', ')})`
      : `Single Category: ${activeCategory}`,
    `Business: ${shopOwnerInfo.business || '—'}  |  Region: ${shopOwnerInfo.region || '—'}  |  State: ${shopOwnerInfo.state || '—'}`,
  ];

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(10);
  doc.setTextColor(40, 40, 50);
  bullets.forEach(line => {
    const lines = doc.splitTextToSize(`•  ${line}`, pageW - 32);
    lines.forEach(l => {
      doc.text(l, 18, y);
      y += 6;
    });
    y += 1;
  });

  y += 4;

  // Annual Visual Trend — embed chart
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

  /* ══════════════════════════════════════════════
     PAGES 2–4: Monthly Execution Playbook
     ══════════════════════════════════════════════ */
  doc.addPage();
  y = 20;

  // Section header
  doc.setFillColor(26, 29, 46);
  doc.rect(0, 0, pageW, 22, 'F');
  doc.setTextColor(16, 185, 129);
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text('Monthly Execution Playbook', 14, 15);
  doc.setTextColor(200, 200, 220);
  doc.setFontSize(9);
  doc.text(`${activeCategory}  |  ${year}`, pageW - 14, 15, { align: 'right' });
  y = 30;

  monthly.forEach((m, idx) => {
    const growth = m.baseline > 0 ? ((m.predicted - m.baseline) / m.baseline * 100) : 0;
    const growthStr = growth.toFixed(0);
    const stockMin = Math.round(m.predicted * 0.75).toLocaleString('en-IN');
    const stockMax = Math.round(m.predicted * 1.10).toLocaleString('en-IN');
    const hasFestival = !!m.festival;

    // Check space: each card needs ~48mm
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
      actionColor = [245, 158, 11]; // amber
      actionText = `High Demand (Festival: ${m.festival.name}): Increase stock levels 2 weeks prior. Limit discount to 5% to protect margins.`;
    } else if (growth >= 40) {
      actionColor = [239, 68, 68]; // red
      actionText = `REORDER NOW: Extreme demand surge (+${growthStr}%). Pre-order immediately. Keep discount at 5% maximum.`;
    } else if (hasFestival) {
      actionColor = [245, 158, 11]; // amber
      actionText = `Festival Prep (${m.festival.name}): Stock up in advance. Apply 8% discount to drive early sales.`;
    } else if (growth >= 15) {
      actionColor = [16, 185, 129]; // teal
      actionText = `Growing Demand: Sales trending up ${growthStr}%. Maintain 8% discount. Monitor inventory weekly.`;
    } else if (growth >= -10) {
      actionColor = [16, 185, 129]; // teal
      actionText = 'Stable Demand: Continue normal operations. Apply a 10% discount to maintain steady stock turnover.';
    } else {
      actionColor = [239, 68, 68]; // red
      actionText = `Low Demand: Sales declining ${growthStr}%. Apply 15-20% discount to clear stock and reduce holding costs.`;
    }

    doc.setTextColor(...actionColor);
    const aLines = doc.splitTextToSize(actionText, pageW - 52);
    doc.text(aLines, 52, y);
    y += aLines.length * 5 + 3;

    // Separator line
    doc.setDrawColor(220, 225, 230);
    doc.setLineWidth(0.3);
    doc.line(18, y, pageW - 18, y);
    y += 6;
  });

  /* ══════════════════════════════════════════════
     FINAL PAGE: Annual Impact & Summary
     ══════════════════════════════════════════════ */
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
    conclusionText = `The highest growth of +${topLift}% in ${MONTHS[topFestival.month]} (${topFestival.festival.name}) is the primary area for capital investment. Focus procurement, marketing budgets, and staffing around this peak to maximize revenue for ${activeCategory}.`;
  } else {
    conclusionText = `Category "${activeCategory}" shows steady ${overallGrowth}% annual growth. Maintain balanced inventory levels and apply standard discount strategies throughout the year.`;
  }
  const cLines = doc.splitTextToSize(conclusionText, pageW - 44);
  doc.text(cLines, 20, y + 15);

  // Add footers to all pages
  addFooter();

  doc.save(`SalesForecast_${shopOwnerInfo.business || 'Report'}_${activeCategory.replace(/[^a-zA-Z0-9]/g, '_')}_${year}.pdf`);
}

/* ══════════════════════════════════════════════════════════════
   MAIN EXPORT BUTTON COMPONENT
   Props: forecastMap (all categories), activeCategory, chartRef, shopOwnerInfo
   ══════════════════════════════════════════════════════════════ */
export default function ExportButton({ dataType = 'forecast', data, forecastMap, activeCategory, chartRef, shopOwnerInfo = {} }) {
  const [open, setOpen]       = useState(false);
  const [poOpen, setPOOpen]   = useState(false);
  const [busy, setBusy]       = useState(null);
  const dropRef               = useRef(null);

  // Backwards-compat: support old `data` prop or new `forecastMap` prop
  const fMap = forecastMap || (data?.forecast ? { [data.category || 'All Products']: data.forecast } : {});
  const category = activeCategory || data?.category || shopOwnerInfo?.category || Object.keys(fMap)[0] || 'All Products';
  const forecast = fMap[category];

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (dropRef.current && !dropRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Build ALL monthly rows with decision for PO (not just reorder ones)
  const allMonthlyRows = React.useMemo(() => {
    if (!forecast?.monthly) return [];
    return forecast.monthly.map(m => {
      const changePct = m.baseline > 0 ? ((m.predicted - m.baseline) / m.baseline * 100) : 0;
      let decision;
      if (changePct >= 40) decision = 'REORDER NOW';
      else if (changePct >= 15) decision = 'WATCHLIST';
      else decision = 'OK';
      return {
        monthLabel: MONTHS[m.month],
        month: m.month,
        predicted: m.predicted,
        baseline: m.baseline,
        category: category,
        reorderQty: Math.round(m.predicted * 1.10),
        festival: m.festival,
        decision,
      };
    });
  }, [forecast, category]);

  const reorderCount = allMonthlyRows.filter(r => r.decision === 'REORDER NOW').length;

  const handleExcel = useCallback(async () => {
    setBusy('excel');
    try {
      exportExcel(fMap, shopOwnerInfo, category);
    } finally {
      setBusy(null);
      setOpen(false);
    }
  }, [fMap, shopOwnerInfo, category]);

  const handlePDF = useCallback(async () => {
    setBusy('pdf');
    try {
      await exportPDF(fMap, shopOwnerInfo, category, chartRef);
    } finally {
      setBusy(null);
      setOpen(false);
    }
  }, [fMap, shopOwnerInfo, category, chartRef]);

  const handlePO = useCallback(() => {
    setOpen(false);
    setPOOpen(true);
  }, []);

  return (
    <div className="export-wrapper" ref={dropRef}>
      <button className="export-toggle" onClick={() => setOpen(prev => !prev)}>
        📥 Export {open ? '▲' : '▼'}
      </button>

      <div className={`export-dropdown ${open ? 'export-dropdown--open' : ''}`}>
        <div className="export-category-label">Exporting: <strong>{category}</strong></div>

        <button className="export-option" onClick={handleExcel} disabled={!!busy}>
          <span className="export-option-icon">📊</span>
          <span className="export-option-text">
            <strong>{busy === 'excel' ? 'Generating…' : 'Excel Workbook'}</strong>
            <small>All {Object.keys(fMap).length} categories — Forecast, Inventory &amp; Profile sheets</small>
          </span>
        </button>

        <button className="export-option" onClick={handlePDF} disabled={!!busy}>
          <span className="export-option-icon">📄</span>
          <span className="export-option-text">
            <strong>{busy === 'pdf' ? 'Generating…' : 'PDF Report'}</strong>
            <small>Executive playbook for {category} with chart &amp; monthly strategy</small>
          </span>
        </button>

        <div className="export-divider" />

        <button
          className="export-option export-option--po"
          onClick={handlePO}
          disabled={!!busy}
        >
          <span className="export-option-icon">🧾</span>
          <span className="export-option-text">
            <strong>Purchase Order</strong>
            <small>
              {reorderCount > 0
                ? `${reorderCount} REORDER month(s) · Select months to include`
                : 'Select any month(s) to generate PO'}
            </small>
          </span>
        </button>
      </div>

      <POGeneratorDialog
        open={poOpen}
        onClose={() => setPOOpen(false)}
        allMonthlyRows={allMonthlyRows}
        shopOwnerInfo={shopOwnerInfo}
        category={category}
      />
    </div>
  );
}
