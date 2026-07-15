import React, { useState, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Shield, AlertTriangle, Scan,
  BarChart3, Link2, Settings, LogOut, Menu, X
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { api } from '../../api/client'

const navItems = [
  { path: '/', label: 'Ana Sayfa', icon: LayoutDashboard, exact: true },
  { path: '/politikalar', label: 'Politikalar', icon: Shield },
  { path: '/olaylar', label: 'Olaylar', icon: AlertTriangle, badge: true },
  { path: '/tarama', label: 'Tarama Merkezi', icon: Scan },
  { path: '/raporlar', label: 'Raporlar', icon: BarChart3 },
  { path: '/entegrasyonlar', label: 'Entegrasyonlar', icon: Link2 },
]

function roleLabel(role) {
  if (!role) return 'Kullanıcı'
  const map = { admin: 'Yönetici', analyst: 'Analist', viewer: 'İzleme' }
  return map[role] || role
}

function getInitials(user) {
  if (!user) return 'U'
  const name = user.full_name || user.email || ''
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2) || 'U'
}

export default function Sidebar({ mobileOpen, onClose }) {
  const { user, logout } = useAuth()
  const location = useLocation()
  const [incidentCount, setIncidentCount] = useState(0)

  useEffect(() => {
    api.incidents.getSummary()
      .then(res => {
        const data = res.data
        const open = (data.by_status?.open || 0) + (data.by_status?.investigating || 0)
        setIncidentCount(open)
      })
      .catch(() => {})
  }, [location.pathname])

  const isActive = (path, exact) => {
    if (exact) return location.pathname === path
    return location.pathname.startsWith(path)
  }

  return (
    <>
      {mobileOpen && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 99 }}
          onClick={onClose}
        />
      )}
      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
        {/* Logo */}
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <Shield size={20} color="white" />
          </div>
          <div>
            <div className="sidebar-logo-text">DLP Sistemi</div>
            <div className="sidebar-logo-sub">Veri Koruma Platformu</div>
          </div>
          {mobileOpen && (
            <button
              onClick={onClose}
              style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
            >
              <X size={18} />
            </button>
          )}
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav">
          <div className="nav-section-label">Ana Menü</div>

          {navItems.map(({ path, label, icon: Icon, exact, badge }) => (
            <NavLink
              key={path}
              to={path}
              className={`nav-item ${isActive(path, exact) ? 'active' : ''}`}
              onClick={mobileOpen ? onClose : undefined}
              style={{ textDecoration: 'none' }}
            >
              <Icon size={18} className="nav-icon" />
              <span style={{ flex: 1 }}>{label}</span>
              {badge && incidentCount > 0 && (
                <span className="nav-badge">{incidentCount > 99 ? '99+' : incidentCount}</span>
              )}
            </NavLink>
          ))}

          <div className="sidebar-divider" />
          <div className="nav-section-label">Sistem</div>

          <NavLink
            to="/ayarlar"
            className={`nav-item ${isActive('/ayarlar') ? 'active' : ''}`}
            onClick={mobileOpen ? onClose : undefined}
            style={{ textDecoration: 'none' }}
          >
            <Settings size={18} className="nav-icon" />
            <span>Ayarlar</span>
          </NavLink>
        </nav>

        {/* Bottom user section */}
        <div className="sidebar-bottom">
          <div className="user-avatar">
            {getInitials(user)}
          </div>
          <div className="user-info">
            <div className="user-name">{user?.full_name || user?.email || 'Kullanıcı'}</div>
            <div className="user-role">{roleLabel(user?.role)}</div>
          </div>
          <button
            className="logout-btn"
            onClick={logout}
            title="Çıkış Yap"
          >
            <LogOut size={16} />
          </button>
        </div>
      </aside>
    </>
  )
}
