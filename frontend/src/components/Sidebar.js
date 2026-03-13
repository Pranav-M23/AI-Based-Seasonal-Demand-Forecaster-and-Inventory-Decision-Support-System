import React from 'react';
import { Warehouse, UserCircle, FolderOpen } from 'lucide-react';

function Sidebar({ activePage, onPageChange, catalogCount }) {
  return (
    <nav className="sidebar">
      <div className="sidebar-logo">
        <span className="sidebar-logo-icon">📈</span>
        <span className="sidebar-logo-text">SDF</span>
      </div>

      <ul className="sidebar-menu">
        <li
          className={`sidebar-item${activePage === 'inventory' ? ' sidebar-item--active' : ''}`}
          onClick={() => onPageChange('inventory')}
        >
          <Warehouse size={20} />
          <span className="sidebar-label">Inventory Dashboard Analytics</span>
        </li>
        <li
          className={`sidebar-item${activePage === 'shop-owner' ? ' sidebar-item--active' : ''}`}
          onClick={() => onPageChange('shop-owner')}
        >
          <UserCircle size={20} />
          <span className="sidebar-label">Shop Owner Analytics</span>
        </li>
        <li
          className={`sidebar-item sidebar-item--catalog${activePage === 'predictions-catalog' ? ' sidebar-item--active' : ''}`}
          onClick={() => onPageChange('predictions-catalog')}
        >
          <FolderOpen size={20} />
          <span className="sidebar-label">Predictions Catalog</span>
          {catalogCount > 0 && (
            <span className="sidebar-badge">{catalogCount}</span>
          )}
        </li>
      </ul>
    </nav>
  );
}

export default Sidebar;
