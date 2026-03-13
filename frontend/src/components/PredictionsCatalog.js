import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { X, Search, Trash2, Download, Eye, Edit3, ChevronDown, ChevronUp, Clock, BarChart3, Filter } from 'lucide-react';
import { predictionsAPI } from '../services/api';

const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const SHORT_MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

const ALL_STATUSES = [
  'Draft', 'Pending Review', 'Forwarded to Review', 'Approved',
  'Preorder Now', 'Print Sales', 'Completed', 'On Hold', 'Rejected',
  'Revision Needed', 'Under Analysis', 'Archived'
];

const STATUS_CONFIG = {
  'Draft':              { icon: '📝', color: '#9ca3af' },
  'Pending Review':     { icon: '📤', color: '#f59e0b' },
  'Forwarded to Review':{ icon: '🟡', color: '#f59e0b' },
  'Approved':           { icon: '✅', color: '#10b981' },
  'Preorder Now':       { icon: '🛒', color: '#06b6d4' },
  'Print Sales':        { icon: '📄', color: '#8b5cf6' },
  'Completed':          { icon: '✔️', color: '#22c55e' },
  'On Hold':            { icon: '⏸️', color: '#6b7280' },
  'Rejected':           { icon: '❌', color: '#ef4444' },
  'Revision Needed':    { icon: '🔄', color: '#f97316' },
  'Under Analysis':     { icon: '📊', color: '#3b82f6' },
  'Archived':           { icon: '🗄️', color: '#6b7280' },
};

/* ═══════════════════════════════════════════════════
   PREDICTION DETAIL VIEW (when user clicks View)
   ═══════════════════════════════════════════════════ */
function PredictionDetailView({ prediction, onBack, onUpdate }) {
  const [editingNotes, setEditingNotes] = useState(false);
  const [notes, setNotes] = useState(prediction.notes || '');
  const [status, setStatus] = useState(prediction.status);
  const [saving, setSaving] = useState(false);

  const handleStatusChange = async (newStatus) => {
    setSaving(true);
    try {
      const updated = await predictionsAPI.update(prediction.id, { status: newStatus });
      setStatus(newStatus);
      onUpdate(updated);
    } catch (err) {
      console.error('Status update failed:', err);
    }
    setSaving(false);
  };

  const handleNoteSave = async () => {
    setSaving(true);
    try {
      const updated = await predictionsAPI.update(prediction.id, { notes });
      onUpdate(updated);
      setEditingNotes(false);
    } catch (err) {
      console.error('Note update failed:', err);
    }
    setSaving(false);
  };

  const sc = STATUS_CONFIG[status] || STATUS_CONFIG['Draft'];

  return (
    <div className="pc-detail">
      <button className="pc-detail-back" onClick={onBack}>← Back to Catalog</button>

      <div className="pc-detail-header">
        <h3>📋 Prediction #{String(prediction.id).padStart(3, '0')}</h3>
      </div>

      <div className="pc-detail-grid">
        {/* Business Details */}
        <div className="pc-detail-card">
          <h4>Business Details</h4>
          <div className="pc-detail-row"><span>👤 Owner</span><strong>{prediction.owner_name}</strong></div>
          <div className="pc-detail-row"><span>🏢 Business</span><strong>{prediction.business_name}</strong></div>
          <div className="pc-detail-row"><span>📍 Location</span><strong>{prediction.state}{prediction.state && prediction.region ? ', ' : ''}{prediction.region}</strong></div>
          <div className="pc-detail-row"><span>📦 Category</span><strong>{prediction.category}</strong></div>
        </div>

        {/* Forecast Summary */}
        <div className="pc-detail-card">
          <h4>Forecast Summary</h4>
          <div className="pc-detail-row"><span>📅 Period</span><strong>{MONTHS[(prediction.month || 1) - 1]} {prediction.year}</strong></div>
          <div className="pc-detail-row"><span>📊 Predicted</span><strong className="pc-val-teal">{prediction.predicted_sales.toLocaleString('en-IN')}</strong></div>
          <div className="pc-detail-row"><span>📉 Baseline</span><strong>{prediction.baseline_sales.toLocaleString('en-IN')}</strong></div>
          <div className="pc-detail-row">
            <span>📈 Growth</span>
            <strong style={{ color: prediction.growth_percent >= 0 ? '#10b981' : '#ef4444' }}>
              {prediction.growth_percent >= 0 ? '+' : ''}{prediction.growth_percent}%
            </strong>
          </div>
        </div>
      </div>

      <div className="pc-detail-grid">
        {/* Recommendations */}
        <div className="pc-detail-card">
          <h4>Recommendations</h4>
          <div className="pc-detail-row"><span>💰 Discount</span><strong>{prediction.discount_recommendation}</strong></div>
          <div className="pc-detail-row"><span>📦 Stock Range</span><strong>{prediction.stock_range_min.toLocaleString('en-IN')} – {prediction.stock_range_max.toLocaleString('en-IN')}</strong></div>
          <div className="pc-detail-row"><span>🎯 Demand</span><strong>{prediction.demand_level}</strong></div>
          {prediction.festival_name && (
            <div className="pc-detail-row"><span>🎉 Festival</span><strong>{prediction.festival_name}</strong></div>
          )}
        </div>

        {/* Workflow */}
        <div className="pc-detail-card">
          <h4>Workflow</h4>
          <div className="pc-detail-row">
            <span>📌 Status</span>
            <select
              className="pc-status-select"
              value={status}
              onChange={(e) => handleStatusChange(e.target.value)}
              disabled={saving}
              style={{ borderColor: sc.color }}
            >
              {ALL_STATUSES.map(s => (
                <option key={s} value={s}>{STATUS_CONFIG[s]?.icon || ''} {s}</option>
              ))}
            </select>
          </div>
          <div className="pc-detail-row"><span>🕐 Created</span><strong>{prediction.created_at}</strong></div>
          <div className="pc-detail-row"><span>🔄 Updated</span><strong>{prediction.updated_at}</strong></div>
        </div>
      </div>

      {/* Notes */}
      <div className="pc-detail-card pc-detail-card--full">
        <div className="pc-detail-notes-header">
          <h4>Notes</h4>
          {!editingNotes && (
            <button className="pc-edit-note-btn" onClick={() => setEditingNotes(true)}>
              <Edit3 size={14} /> Edit
            </button>
          )}
        </div>
        {editingNotes ? (
          <div>
            <textarea
              className="so-input spd-textarea"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
            />
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              <button className="spd-save-btn" onClick={handleNoteSave} disabled={saving} style={{ fontSize: '0.82rem', padding: '0.4rem 1rem' }}>
                {saving ? 'Saving...' : 'Save Note'}
              </button>
              <button className="so-modify-btn" onClick={() => { setEditingNotes(false); setNotes(prediction.notes || ''); }} style={{ fontSize: '0.82rem', padding: '0.4rem 1rem' }}>
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <p className="pc-notes-text">{prediction.notes || 'No notes added.'}</p>
        )}
      </div>

      {/* History */}
      {prediction.history && prediction.history.length > 0 && (
        <div className="pc-detail-card pc-detail-card--full">
          <h4>History</h4>
          <ul className="pc-history-list">
            {prediction.history.map((h, i) => (
              <li key={i} className="pc-history-item">
                <Clock size={13} />
                <span className="pc-history-time">{h.time}</span>
                <span>{h.action}</span>
                {h.by && <span className="pc-history-by">by {h.by}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}


/* ═══════════════════════════════════════════════════
   MAIN CATALOG COMPONENT
   ═══════════════════════════════════════════════════ */
function PredictionsCatalog({ isOpen, onClose, fullPage }) {
  const [predictions, setPredictions] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState('table');  // table | timeline | stats
  const [detailView, setDetailView] = useState(null);  // prediction object or null

  // Filters
  const [filterStatus, setFilterStatus] = useState('');
  const [filterMonth, setFilterMonth] = useState('');
  const [filterYear, setFilterYear] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterRegion, setFilterRegion] = useState('');
  const [searchText, setSearchText] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [showFilters, setShowFilters] = useState(false);

  // Selection for bulk ops
  const [selected, setSelected] = useState(new Set());

  const fetchPredictions = useCallback(async () => {
    setLoading(true);
    try {
      const filters = {};
      if (filterStatus) filters.status = filterStatus;
      if (filterMonth) filters.month = parseInt(filterMonth);
      if (filterYear) filters.year = parseInt(filterYear);
      if (filterCategory) filters.category = filterCategory;
      if (filterRegion) filters.region = filterRegion;
      if (searchText) filters.search = searchText;
      filters.sort_by = sortBy;
      filters.sort_order = sortOrder;

      const data = await predictionsAPI.getAll(filters);
      setPredictions(data.predictions || []);
    } catch (err) {
      console.error('Error fetching predictions:', err);
    }
    setLoading(false);
  }, [filterStatus, filterMonth, filterYear, filterCategory, filterRegion, searchText, sortBy, sortOrder]);

  const fetchStats = useCallback(async () => {
    try {
      const data = await predictionsAPI.getStats();
      setStats(data);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  }, []);

  useEffect(() => {
    if (isOpen || fullPage) {
      fetchPredictions();
      fetchStats();
    }
  }, [isOpen, fullPage, fetchPredictions, fetchStats]);

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this prediction?')) return;
    try {
      await predictionsAPI.delete(id);
      setPredictions(prev => prev.filter(p => p.id !== id));
      fetchStats();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  const handleBulkDelete = async () => {
    if (selected.size === 0) return;
    if (!window.confirm(`Delete ${selected.size} predictions?`)) return;
    try {
      await predictionsAPI.bulkDelete([...selected]);
      setPredictions(prev => prev.filter(p => !selected.has(p.id)));
      setSelected(new Set());
      fetchStats();
    } catch (err) {
      console.error('Bulk delete failed:', err);
    }
  };

  const handleStatusChange = async (id, newStatus) => {
    try {
      const updated = await predictionsAPI.update(id, { status: newStatus });
      setPredictions(prev => prev.map(p => p.id === id ? updated : p));
      fetchStats();
    } catch (err) {
      console.error('Status update failed:', err);
    }
  };

  const handleUpdate = (updated) => {
    setPredictions(prev => prev.map(p => p.id === updated.id ? updated : p));
    if (detailView && detailView.id === updated.id) setDetailView(updated);
    fetchStats();
  };

  const toggleSelect = (id) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selected.size === predictions.length) setSelected(new Set());
    else setSelected(new Set(predictions.map(p => p.id)));
  };

  const handleSort = (col) => {
    if (sortBy === col) setSortOrder(prev => prev === 'desc' ? 'asc' : 'desc');
    else { setSortBy(col); setSortOrder('desc'); }
  };

  const exportCatalog = () => {
    if (predictions.length === 0) return;
    const headers = ['ID','Owner','Business','Category','Region','Month','Year','Predicted','Baseline','Growth%','Discount','Stock Min','Stock Max','Status','Notes','Created'];
    const rows = predictions.map(p => [
      p.id, p.owner_name, p.business_name, p.category, p.region,
      MONTHS[(p.month || 1) - 1], p.year, p.predicted_sales, p.baseline_sales,
      p.growth_percent, p.discount_recommendation, p.stock_range_min, p.stock_range_max,
      p.status, `"${(p.notes || '').replace(/"/g, '""')}"`, p.created_at
    ]);
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `predictions_catalog_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Unique values for filter dropdowns
  const uniqueCategories = useMemo(() => [...new Set(predictions.map(p => p.category).filter(Boolean))], [predictions]);
  const uniqueRegions = useMemo(() => [...new Set(predictions.map(p => p.region).filter(Boolean))], [predictions]);

  // Timeline grouping
  const timelineGroups = useMemo(() => {
    const groups = {};
    predictions.forEach(p => {
      const key = `${MONTHS[(p.month || 1) - 1]} ${p.year}`;
      if (!groups[key]) groups[key] = [];
      groups[key].push(p);
    });
    return groups;
  }, [predictions]);

  if (!isOpen && !fullPage) return null;

  if (fullPage) {
    return (
      <div className="pc-fullpage">
        {/* Header */}
        <div className="pc-header">
          <div className="pc-header-left">
            <h2>📂 Predictions Catalog</h2>
            {stats && <span className="pc-header-count">{stats.total} predictions</span>}
          </div>
        </div>

        {detailView ? (
          <PredictionDetailView
            prediction={detailView}
            onBack={() => setDetailView(null)}
            onUpdate={handleUpdate}
          />
        ) : (
          <>
            {/* Toolbar */}
            <div className="pc-toolbar">
              <div className="pc-search-row">
                <div className="pc-search-box">
                  <Search size={16} />
                  <input
                    type="text"
                    placeholder="Search predictions..."
                    value={searchText}
                    onChange={(e) => setSearchText(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && fetchPredictions()}
                  />
                </div>
                <button className="pc-filter-toggle" onClick={() => setShowFilters(!showFilters)}>
                  <Filter size={15} /> Filters {showFilters ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
              </div>

              {showFilters && (
                <div className="pc-filters">
                  <select className="pc-filter-select" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
                    <option value="">All Status</option>
                    {ALL_STATUSES.map(s => <option key={s} value={s}>{STATUS_CONFIG[s]?.icon} {s}</option>)}
                  </select>
                  <select className="pc-filter-select" value={filterMonth} onChange={(e) => setFilterMonth(e.target.value)}>
                    <option value="">All Months</option>
                    {MONTHS.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
                  </select>
                  <select className="pc-filter-select" value={filterYear} onChange={(e) => setFilterYear(e.target.value)}>
                    <option value="">All Years</option>
                    <option value="2026">2026</option>
                    <option value="2025">2025</option>
                  </select>
                  <select className="pc-filter-select" value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
                    <option value="">All Categories</option>
                    {uniqueCategories.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                  <select className="pc-filter-select" value={filterRegion} onChange={(e) => setFilterRegion(e.target.value)}>
                    <option value="">All Regions</option>
                    {uniqueRegions.map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                  <button className="pc-reset-btn" onClick={() => {
                    setFilterStatus(''); setFilterMonth(''); setFilterYear('');
                    setFilterCategory(''); setFilterRegion(''); setSearchText('');
                  }}>Reset</button>
                </div>
              )}

              {/* View mode + bulk actions */}
              <div className="pc-actions-bar">
                <div className="pc-view-modes">
                  <button className={`pc-vm-btn${viewMode === 'table' ? ' pc-vm-btn--active' : ''}`} onClick={() => setViewMode('table')}>Table</button>
                  <button className={`pc-vm-btn${viewMode === 'timeline' ? ' pc-vm-btn--active' : ''}`} onClick={() => setViewMode('timeline')}>Timeline</button>
                  <button className={`pc-vm-btn${viewMode === 'stats' ? ' pc-vm-btn--active' : ''}`} onClick={() => setViewMode('stats')}>
                    <BarChart3 size={14} /> Stats
                  </button>
                </div>
                <div className="pc-bulk-actions">
                  <button className="pc-export-btn" onClick={exportCatalog} disabled={predictions.length === 0}>
                    <Download size={14} /> Export CSV
                  </button>
                  {selected.size > 0 && (
                    <button className="pc-bulk-delete-btn" onClick={handleBulkDelete}>
                      <Trash2 size={14} /> Delete ({selected.size})
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="pc-content">
              {loading ? (
                <div className="pc-loading">Loading predictions...</div>
              ) : predictions.length === 0 ? (
                <div className="pc-empty">
                  <div className="pc-empty-icon">📂</div>
                  <h3>No predictions saved yet</h3>
                  <p>Save predictions from the Shop Owner Analytics page to see them here.</p>
                </div>
              ) : viewMode === 'stats' ? (
                <CatalogStats stats={stats} />
              ) : viewMode === 'timeline' ? (
                <div className="pc-timeline">
                  {Object.entries(timelineGroups).map(([period, items]) => (
                    <div key={period} className="pc-tl-group">
                      <h4 className="pc-tl-period">{period}</h4>
                      {items.map(p => {
                        const sc = STATUS_CONFIG[p.status] || STATUS_CONFIG['Draft'];
                        return (
                          <div key={p.id} className="pc-tl-item" onClick={() => setDetailView(p)}>
                            <span className="pc-tl-id">#{String(p.id).padStart(3, '0')}</span>
                            <span className="pc-tl-owner">{p.owner_name} ({p.business_name})</span>
                            <span className="pc-tl-cat">{p.category}</span>
                            <span className="pc-tl-status" style={{ color: sc.color }}>{sc.icon} {p.status}</span>
                          </div>
                        );
                      })}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="pc-table-wrap">
                  <table className="pc-table">
                    <thead>
                      <tr>
                        <th>
                          <input type="checkbox" checked={selected.size === predictions.length && predictions.length > 0} onChange={toggleSelectAll} />
                        </th>
                        <th className="pc-th-sort" onClick={() => handleSort('created_at')}>
                          ID {sortBy === 'created_at' && (sortOrder === 'desc' ? '▼' : '▲')}
                        </th>
                        <th className="pc-th-sort" onClick={() => handleSort('owner_name')}>
                          Owner {sortBy === 'owner_name' && (sortOrder === 'desc' ? '▼' : '▲')}
                        </th>
                        <th>Business</th>
                        <th>Category</th>
                        <th className="pc-th-sort" onClick={() => handleSort('month')}>
                          Period {sortBy === 'month' && (sortOrder === 'desc' ? '▼' : '▲')}
                        </th>
                        <th className="pc-th-sort" onClick={() => handleSort('predicted_sales')}>
                          Sales {sortBy === 'predicted_sales' && (sortOrder === 'desc' ? '▼' : '▲')}
                        </th>
                        <th className="pc-th-sort" onClick={() => handleSort('status')}>
                          Status {sortBy === 'status' && (sortOrder === 'desc' ? '▼' : '▲')}
                        </th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {predictions.map(p => {
                        const sc = STATUS_CONFIG[p.status] || STATUS_CONFIG['Draft'];
                        return (
                          <tr key={p.id} className={selected.has(p.id) ? 'pc-row--selected' : ''}>
                            <td><input type="checkbox" checked={selected.has(p.id)} onChange={() => toggleSelect(p.id)} /></td>
                            <td className="pc-td-id">#{String(p.id).padStart(3, '0')}</td>
                            <td>{p.owner_name}</td>
                            <td>{p.business_name}</td>
                            <td className="pc-td-cat">{p.category}</td>
                            <td>{SHORT_MONTHS[(p.month || 1) - 1]} {p.year}</td>
                            <td className="pc-td-sales">
                              <span>{p.predicted_range_min.toLocaleString('en-IN')}–{p.predicted_range_max.toLocaleString('en-IN')}</span>
                            </td>
                            <td>
                              <select
                                className="pc-inline-status"
                                value={p.status}
                                onChange={(e) => handleStatusChange(p.id, e.target.value)}
                                style={{ borderColor: sc.color, color: sc.color }}
                              >
                                {ALL_STATUSES.map(s => <option key={s} value={s}>{STATUS_CONFIG[s]?.icon} {s}</option>)}
                              </select>
                            </td>
                            <td className="pc-td-actions">
                              <button title="View" onClick={() => setDetailView(p)}><Eye size={15} /></button>
                              <button title="Delete" onClick={() => handleDelete(p.id)}><Trash2 size={15} /></button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="pc-overlay" onClick={onClose}>
      <div className="pc-panel" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="pc-header">
          <div className="pc-header-left">
            <h2>📂 Predictions Catalog</h2>
            {stats && <span className="pc-header-count">{stats.total} predictions</span>}
          </div>
          <button className="pc-close" onClick={onClose}><X size={22} /></button>
        </div>

        {detailView ? (
          <PredictionDetailView
            prediction={detailView}
            onBack={() => setDetailView(null)}
            onUpdate={handleUpdate}
          />
        ) : (
          <>
            {/* Toolbar */}
            <div className="pc-toolbar">
              <div className="pc-search-row">
                <div className="pc-search-box">
                  <Search size={16} />
                  <input
                    type="text"
                    placeholder="Search predictions..."
                    value={searchText}
                    onChange={(e) => setSearchText(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && fetchPredictions()}
                  />
                </div>
                <button className="pc-filter-toggle" onClick={() => setShowFilters(!showFilters)}>
                  <Filter size={15} /> Filters {showFilters ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
              </div>

              {showFilters && (
                <div className="pc-filters">
                  <select className="pc-filter-select" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
                    <option value="">All Status</option>
                    {ALL_STATUSES.map(s => <option key={s} value={s}>{STATUS_CONFIG[s]?.icon} {s}</option>)}
                  </select>
                  <select className="pc-filter-select" value={filterMonth} onChange={(e) => setFilterMonth(e.target.value)}>
                    <option value="">All Months</option>
                    {MONTHS.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
                  </select>
                  <select className="pc-filter-select" value={filterYear} onChange={(e) => setFilterYear(e.target.value)}>
                    <option value="">All Years</option>
                    <option value="2026">2026</option>
                    <option value="2025">2025</option>
                  </select>
                  <select className="pc-filter-select" value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
                    <option value="">All Categories</option>
                    {uniqueCategories.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                  <select className="pc-filter-select" value={filterRegion} onChange={(e) => setFilterRegion(e.target.value)}>
                    <option value="">All Regions</option>
                    {uniqueRegions.map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                  <button className="pc-reset-btn" onClick={() => {
                    setFilterStatus(''); setFilterMonth(''); setFilterYear('');
                    setFilterCategory(''); setFilterRegion(''); setSearchText('');
                  }}>Reset</button>
                </div>
              )}

              {/* View mode + bulk actions */}
              <div className="pc-actions-bar">
                <div className="pc-view-modes">
                  <button className={`pc-vm-btn${viewMode === 'table' ? ' pc-vm-btn--active' : ''}`} onClick={() => setViewMode('table')}>Table</button>
                  <button className={`pc-vm-btn${viewMode === 'timeline' ? ' pc-vm-btn--active' : ''}`} onClick={() => setViewMode('timeline')}>Timeline</button>
                  <button className={`pc-vm-btn${viewMode === 'stats' ? ' pc-vm-btn--active' : ''}`} onClick={() => setViewMode('stats')}>
                    <BarChart3 size={14} /> Stats
                  </button>
                </div>
                <div className="pc-bulk-actions">
                  <button className="pc-export-btn" onClick={exportCatalog} disabled={predictions.length === 0}>
                    <Download size={14} /> Export CSV
                  </button>
                  {selected.size > 0 && (
                    <button className="pc-bulk-delete-btn" onClick={handleBulkDelete}>
                      <Trash2 size={14} /> Delete ({selected.size})
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="pc-content">
              {loading ? (
                <div className="pc-loading">Loading predictions...</div>
              ) : predictions.length === 0 ? (
                <div className="pc-empty">
                  <div className="pc-empty-icon">📂</div>
                  <h3>No predictions saved yet</h3>
                  <p>Save predictions from the Shop Owner Analytics page to see them here.</p>
                </div>
              ) : viewMode === 'stats' ? (
                /* ═══ STATS VIEW ═══ */
                <CatalogStats stats={stats} />
              ) : viewMode === 'timeline' ? (
                /* ═══ TIMELINE VIEW ═══ */
                <div className="pc-timeline">
                  {Object.entries(timelineGroups).map(([period, items]) => (
                    <div key={period} className="pc-tl-group">
                      <h4 className="pc-tl-period">{period}</h4>
                      {items.map(p => {
                        const sc = STATUS_CONFIG[p.status] || STATUS_CONFIG['Draft'];
                        return (
                          <div key={p.id} className="pc-tl-item" onClick={() => setDetailView(p)}>
                            <span className="pc-tl-id">#{String(p.id).padStart(3, '0')}</span>
                            <span className="pc-tl-owner">{p.owner_name} ({p.business_name})</span>
                            <span className="pc-tl-cat">{p.category}</span>
                            <span className="pc-tl-status" style={{ color: sc.color }}>{sc.icon} {p.status}</span>
                          </div>
                        );
                      })}
                    </div>
                  ))}
                </div>
              ) : (
                /* ═══ TABLE VIEW ═══ */
                <div className="pc-table-wrap">
                  <table className="pc-table">
                    <thead>
                      <tr>
                        <th>
                          <input type="checkbox" checked={selected.size === predictions.length && predictions.length > 0} onChange={toggleSelectAll} />
                        </th>
                        <th className="pc-th-sort" onClick={() => handleSort('created_at')}>
                          ID {sortBy === 'created_at' && (sortOrder === 'desc' ? '▼' : '▲')}
                        </th>
                        <th className="pc-th-sort" onClick={() => handleSort('owner_name')}>
                          Owner {sortBy === 'owner_name' && (sortOrder === 'desc' ? '▼' : '▲')}
                        </th>
                        <th>Business</th>
                        <th>Category</th>
                        <th className="pc-th-sort" onClick={() => handleSort('month')}>
                          Period {sortBy === 'month' && (sortOrder === 'desc' ? '▼' : '▲')}
                        </th>
                        <th className="pc-th-sort" onClick={() => handleSort('predicted_sales')}>
                          Sales {sortBy === 'predicted_sales' && (sortOrder === 'desc' ? '▼' : '▲')}
                        </th>
                        <th className="pc-th-sort" onClick={() => handleSort('status')}>
                          Status {sortBy === 'status' && (sortOrder === 'desc' ? '▼' : '▲')}
                        </th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {predictions.map(p => {
                        const sc = STATUS_CONFIG[p.status] || STATUS_CONFIG['Draft'];
                        return (
                          <tr key={p.id} className={selected.has(p.id) ? 'pc-row--selected' : ''}>
                            <td><input type="checkbox" checked={selected.has(p.id)} onChange={() => toggleSelect(p.id)} /></td>
                            <td className="pc-td-id">#{String(p.id).padStart(3, '0')}</td>
                            <td>{p.owner_name}</td>
                            <td>{p.business_name}</td>
                            <td className="pc-td-cat">{p.category}</td>
                            <td>{SHORT_MONTHS[(p.month || 1) - 1]} {p.year}</td>
                            <td className="pc-td-sales">
                              <span>{p.predicted_range_min.toLocaleString('en-IN')}–{p.predicted_range_max.toLocaleString('en-IN')}</span>
                            </td>
                            <td>
                              <select
                                className="pc-inline-status"
                                value={p.status}
                                onChange={(e) => handleStatusChange(p.id, e.target.value)}
                                style={{ borderColor: sc.color, color: sc.color }}
                              >
                                {ALL_STATUSES.map(s => <option key={s} value={s}>{STATUS_CONFIG[s]?.icon} {s}</option>)}
                              </select>
                            </td>
                            <td className="pc-td-actions">
                              <button title="View" onClick={() => setDetailView(p)}><Eye size={15} /></button>
                              <button title="Delete" onClick={() => handleDelete(p.id)}><Trash2 size={15} /></button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}


/* ═══════════════════════════════════════════════════
   CATALOG STATS COMPONENT
   ═══════════════════════════════════════════════════ */
function CatalogStats({ stats }) {
  if (!stats) return <div className="pc-loading">Loading stats...</div>;

  return (
    <div className="pc-stats">
      <div className="pc-stats-header">
        <h3>📊 Catalog Dashboard</h3>
      </div>

      <div className="pc-stats-top">
        <div className="pc-stats-card">
          <span className="pc-stats-num">{stats.total}</span>
          <span className="pc-stats-label">Total Predictions</span>
        </div>
        <div className="pc-stats-card">
          <span className="pc-stats-num">{stats.this_month}</span>
          <span className="pc-stats-label">This Month</span>
        </div>
      </div>

      <div className="pc-stats-section">
        <h4>Status Breakdown</h4>
        <div className="pc-stats-bars">
          {Object.entries(stats.status_breakdown || {}).map(([status, count]) => {
            const sc = STATUS_CONFIG[status] || STATUS_CONFIG['Draft'];
            const pct = stats.total > 0 ? Math.round((count / stats.total) * 100) : 0;
            return (
              <div key={status} className="pc-stats-bar-row">
                <span className="pc-stats-bar-label">{sc.icon} {status}</span>
                <div className="pc-stats-bar-track">
                  <div className="pc-stats-bar-fill" style={{ width: `${pct}%`, background: sc.color }} />
                </div>
                <span className="pc-stats-bar-val">{count}</span>
              </div>
            );
          })}
        </div>
      </div>

      {stats.top_categories && stats.top_categories.length > 0 && (
        <div className="pc-stats-section">
          <h4>Top Categories</h4>
          <ol className="pc-stats-list">
            {stats.top_categories.map((c, i) => (
              <li key={i}>{c.category} <span>({c.count})</span></li>
            ))}
          </ol>
        </div>
      )}

      {stats.region_breakdown && Object.keys(stats.region_breakdown).length > 0 && (
        <div className="pc-stats-section">
          <h4>By Region</h4>
          <div className="pc-stats-bars">
            {Object.entries(stats.region_breakdown).map(([region, count]) => {
              const pct = stats.total > 0 ? Math.round((count / stats.total) * 100) : 0;
              return (
                <div key={region} className="pc-stats-bar-row">
                  <span className="pc-stats-bar-label">📍 {region}</span>
                  <div className="pc-stats-bar-track">
                    <div className="pc-stats-bar-fill" style={{ width: `${pct}%`, background: '#06b6d4' }} />
                  </div>
                  <span className="pc-stats-bar-val">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}


export default PredictionsCatalog;
