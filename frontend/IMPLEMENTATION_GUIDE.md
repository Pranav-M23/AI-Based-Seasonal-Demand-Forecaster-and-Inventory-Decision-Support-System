# 📥 Smart Export & Document Generation — Implementation Guide

## Overview

The **ExportButton** component adds three export capabilities to the Shop Owner Analytics page:

| Feature          | Output           | Description                                                     |
|------------------|------------------|-----------------------------------------------------------------|
| Excel Workbook   | `.xlsx`          | 3-sheet workbook (Forecast, Inventory, Profile)                 |
| PDF Report       | `.pdf`           | Professional report with chart image & month-by-month table     |
| Purchase Order   | `.pdf`           | Auto-generated PO for items flagged as REORDER NOW              |

---

## Installation

From the `frontend/` directory:

```bash
npm install xlsx@0.18.5 jspdf@2.5.1 jspdf-autotable@3.5.31 html2canvas@1.4.1
```

---

## Files

| File                            | Purpose                                    |
|---------------------------------|--------------------------------------------|
| `src/components/ExportButton.jsx` | Main component + PO dialog + export logic |
| `src/components/ExportButton.css` | Dark-theme styling, animations, responsive |

---

## Usage

The component is already integrated into `ShopOwnerAnalytics.js`. It renders below the greeting header once a CSV has been uploaded and forecasts are generated.

### Props

| Prop            | Type        | Description                                                          |
|-----------------|-------------|----------------------------------------------------------------------|
| `dataType`      | `string`    | `'forecast'` or `'inventory'` (default: `'forecast'`)                |
| `data`          | `object`    | Must contain `{ forecast: { monthly, dailySeries, nextYear, festivals }, category }` |
| `chartRef`      | React ref   | Ref attached to the `<Line>` chart for html2canvas capture           |
| `shopOwnerInfo` | `object`    | `{ name, business, region, state, category }`                        |

### Example

```jsx
import ExportButton from './ExportButton';

// Inside your results view:
<ExportButton
  dataType="forecast"
  data={{ forecast, category: viewCategory }}
  chartRef={chartRef}
  shopOwnerInfo={{
    name: ownerName,
    business: businessName,
    region: region,
    state: state,
    category: viewCategory,
  }}
/>
```

---

## How It Works

### Excel Export
- Uses the `xlsx` library to create a multi-sheet workbook
- **Sheet 1 (Forecast)**: Monthly predicted vs baseline, festival name, boost %, FSI index
- **Sheet 2 (Inventory)**: Stock min/max, days of supply, reorder decision per month
- **Sheet 3 (Profile)**: Owner name, business, region, state, category, generation timestamp

### PDF Report
- Uses `jsPDF` + `jspdf-autotable` for structured tables
- Captures the live forecast chart via `html2canvas` and embeds it as a PNG
- Dark header band with QRS Technologies branding
- Executive summary with overall stats
- Month-by-month breakdown table with festival notes, stock ranges, and discount recommendations
- Professional footer on every page with timestamp and report ID

### Purchase Order Generator
- Automatically filters months where demand growth ≥ 40% (`REORDER NOW`)
- Opens a modal to select supplier and delivery date
- Auto-assigns rates per category (Fresh Produce: ₹45, Dairy: ₹60, Groceries: ₹120, Electronics: ₹500, etc.)
- Calculates Subtotal, GST @5%, and Grand Total in Indian Rupees (₹)
- Generates a professional PO PDF with buyer/supplier info, item table, and totals

---

## Troubleshooting

### html2canvas chart not rendering
- Ensure `chartRef` is passed as a React ref to `<Line ref={chartRef} ...>`
- The component accesses `chartRef.current.canvas` (Chart.js canvas element)
- If the chart uses WebGL or external images, `html2canvas` may fail silently — the PDF will still generate with a fallback message

### Excel file opens with warnings
- This is normal for `xlsx`-generated files in some older Excel versions
- The file content is valid; click "Yes" to open

### Purchase Order button is disabled
- The PO button is disabled when no months have ≥40% growth vs baseline (no REORDER NOW items)
- Upload data that shows significant festival-driven demand to enable it

### Fonts not rendering in PDF
- `jsPDF` uses built-in Helvetica by default
- Custom fonts require `.addFont()` — not needed for this implementation

---

## Data Flow

```
ShopOwnerAnalytics
  ├─ forecastMap[category] = { monthly, dailySeries, nextYear, festivals }
  ├─ chartRef → <Line ref={chartRef}>
  │
  └─ <ExportButton>
       ├─ Excel: monthly[] → xlsx workbook (3 sheets)
       ├─ PDF:   monthly[] + chartRef → jsPDF document
       └─ PO:    monthly.filter(growth≥40%) → POGeneratorDialog → jsPDF
```

---

## Dependencies

| Package            | Version  | Purpose                              |
|--------------------|----------|--------------------------------------|
| `xlsx`             | 0.18.5   | Excel workbook generation            |
| `jspdf`            | 2.5.1    | PDF document creation                |
| `jspdf-autotable`  | 3.5.31   | Styled tables in PDF                 |
| `html2canvas`      | 1.4.1    | Chart screenshot capture             |
