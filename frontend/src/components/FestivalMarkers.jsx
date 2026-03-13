import React from 'react';

export const FESTIVAL_COLORS = {
  local: '#10b981',
  'pan-indian': '#f59e0b',
};

function getWeekStart(dateStr) {
  const d = new Date(`${dateStr}T00:00:00`);
  const day = d.getDay();
  d.setDate(d.getDate() + (day === 0 ? -6 : 1 - day));
  return d.toISOString().split('T')[0];
}

export function buildFestivalMarkers(weeklyStarts, festivals = [], weekFsiByStart = new Map()) {
  return (festivals || []).map((fest) => {
    const festWS = getWeekStart(fest.date);
    let closestIdx = -1;
    let minDiff = Infinity;

    weeklyStarts.forEach((ws, i) => {
      const diff = Math.abs(new Date(ws) - new Date(festWS));
      if (diff < minDiff) {
        minDiff = diff;
        closestIdx = i;
      }
    });

    if (closestIdx < 0 || minDiff > 8 * 86400000) return null;

    const kind = fest.type === 'pan-indian' ? 'pan-indian' : 'local';
    const markerColor = FESTIVAL_COLORS[kind];
    const short = fest.name.length > 12 ? fest.name.slice(0, 11).trim() : fest.name;

    return {
      index: closestIdx,
      name: fest.name,
      short,
      date: fest.date,
      type: kind,
      impactMultiplier: Number(fest.impact_multiplier || 1),
      color: markerColor,
      markerEmoji: fest.marker_emoji || '🎉',
      fsi: Number(weekFsiByStart.get(weeklyStarts[closestIdx]) || 0),
    };
  }).filter(Boolean);
}

export function FestivalMarkersLegend({ festivals = [] }) {
  if (!festivals.length) return null;

  return (
    <div className="festival-legend" aria-label="Festival marker legend">
      <span className="festival-legend-item">
        <span className="festival-legend-dot" style={{ backgroundColor: FESTIVAL_COLORS.local }} />
        Local Festival
      </span>
      <span className="festival-legend-item">
        <span className="festival-legend-dot" style={{ backgroundColor: FESTIVAL_COLORS['pan-indian'] }} />
        Pan-Indian Festival
      </span>
    </div>
  );
}
