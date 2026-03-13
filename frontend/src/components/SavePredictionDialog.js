import React, { useState } from 'react';
import { X, Save } from 'lucide-react';
import { predictionsAPI } from '../services/api';

const STATUS_OPTIONS = [
  { value: 'Draft', label: '📝 Draft' },
  { value: 'Pending Review', label: '📤 Pending Review' },
  { value: 'Approved', label: '✅ Approved' },
  { value: 'Preorder Now', label: '🛒 Preorder Now' },
];

function SavePredictionDialog({ isOpen, onClose, onSaved, predictionData }) {
  const [predictionName, setPredictionName] = useState('');
  const [status, setStatus] = useState('Draft');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen || !predictionData) return null;

  const {
    ownerName, businessName, category, region, state,
    month, year, predicted, baseline, changePct,
    discountPct, stockMin, stockMax, demandLevel,
    festivalName, periodLabel
  } = predictionData;

  const defaultName = `${periodLabel || ''} ${year || ''} ${category || ''} Forecast`.trim();

  const handleSave = async () => {
    setSaving(true);
    setError('');
    try {
      const payload = {
        owner_name: ownerName || '',
        business_name: businessName || '',
        category: category || '',
        region: region || '',
        state: state || '',
        month: month != null ? month + 1 : 1,   // convert 0-indexed to 1-indexed
        year: year || 2026,
        predicted_sales: predicted || 0,
        predicted_range_min: Math.round((predicted || 0) * 0.965),
        predicted_range_max: Math.round((predicted || 0) * 1.03),
        baseline_sales: baseline || 0,
        growth_percent: changePct || 0,
        discount_recommendation: discountPct || '',
        stock_range_min: stockMin || 0,
        stock_range_max: stockMax || 0,
        demand_level: demandLevel || '',
        festival_name: festivalName || null,
        status: status,
        notes: notes,
        prediction_name: predictionName || defaultName,
      };
      const result = await predictionsAPI.create(payload);
      onSaved(result);
      // Reset
      setPredictionName('');
      setStatus('Draft');
      setNotes('');
      onClose();
    } catch (err) {
      console.error('Save prediction error:', err);
      setError('Failed to save prediction. Is the backend running?');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="spd-overlay" onClick={onClose}>
      <div className="spd-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="spd-header">
          <h2>💾 Save Prediction</h2>
          <button className="spd-close" onClick={onClose}><X size={20} /></button>
        </div>

        {/* Preview */}
        <div className="spd-preview">
          <div className="spd-preview-row">
            <span>👤 {ownerName || 'Owner'}</span>
            <span>🏢 {businessName || 'Business'}</span>
          </div>
          <div className="spd-preview-row">
            <span>📦 {category || 'N/A'}</span>
            <span>📅 {periodLabel} {year}</span>
          </div>
          <div className="spd-preview-row">
            <span>📊 Predicted: <strong>{(predicted || 0).toLocaleString('en-IN')}</strong></span>
            <span>📈 Growth: <strong>{changePct >= 0 ? '+' : ''}{changePct}%</strong></span>
          </div>
        </div>

        {/* Form */}
        <div className="spd-form">
          <div className="spd-field">
            <label>Prediction Name (optional)</label>
            <input
              type="text"
              className="so-input"
              placeholder={defaultName}
              value={predictionName}
              onChange={(e) => setPredictionName(e.target.value)}
            />
          </div>

          <div className="spd-field">
            <label>Initial Status</label>
            <div className="spd-status-options">
              {STATUS_OPTIONS.map(opt => (
                <label key={opt.value} className={`spd-status-option${status === opt.value ? ' spd-status-option--active' : ''}`}>
                  <input
                    type="radio"
                    name="status"
                    value={opt.value}
                    checked={status === opt.value}
                    onChange={() => setStatus(opt.value)}
                  />
                  <span>{opt.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="spd-field">
            <label>Add Notes (optional)</label>
            <textarea
              className="so-input spd-textarea"
              placeholder="e.g. High demand expected for Holi..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
            />
          </div>
        </div>

        {error && <div className="spd-error">{error}</div>}

        <div className="spd-actions">
          <button className="so-modify-btn" onClick={onClose}>Cancel</button>
          <button className="spd-save-btn" onClick={handleSave} disabled={saving}>
            <Save size={16} />
            {saving ? 'Saving...' : 'Save Prediction'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default SavePredictionDialog;
