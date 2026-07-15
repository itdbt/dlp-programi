import React, { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Menu, ChevronRight, LogOut, User } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

const routeMap = {
  '/': { title: 'Kontrol Paneli', breadcrumb: ['Ana Sayfa'] },
  '/politikalar': { title: 'Politika Yönetimi', breadcrumb: ['Ana Sayfa', 'Politikalar'] },
  '/olaylar': { title: 'Olay Yönetimi', breadcrumb: ['Ana Sayfa', 'Olaylar'] },
  '/tarama': { title: 'Tarama Merkezi', breadcrumb: ['Ana Sayfa', 'Tarama'] },
  '/raporlar': { title: 'Raporlar & Analitik', breadcrumb: ['Ana Sayfa', 'Raporlar'] },
  '/entegrasyonlar': { title: 'Entegrasyonlar', breadcrumb: ['Ana Sayfa', 'Entegrasyonlar'] },
  '/ayarlar': { title: 'Sistem Ayarları', breadcrumb: ['Ana Sayfa', 'Ayarlar'] },
}

function getInitials(user) {
  if (!user) return 'U'
  const name = user.full_name || user.email || ''
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2) || 'U'
}

export default function Header({ onMenuClick }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [time, setTime] = useState(new Date())
  const [dropdownOpen, setDropdownOpen] = useState(false)

  const route = routeMap[location.pathname] || { title: 'DLP Sistemi', breadcrumb: ['Ana Sayfa'] }

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    const close = () => setDropdownOpen(false)
    if (dropdownOpen) document.addEventListener('click', close)
    return () => document.removeEventListener('click', close)
  }, [dropdownOpen])

  const formatTime = (d) => {
    return d.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  const formatDate = (d) => {
    return d.toLocaleDateString('tr-TR', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })
  }

  return (
    <header className="header">
      <button
        onClick={onMenuClick}
        className="btn-icon"
        style={{ display: 'none' }}
        id="menu-toggle"
      >
        <Menu size={18} />
      </button>

      <div className="header-title">
        <h1>{route.title}</h1>
        <div className="header-breadcrumb">
          {route.breadcrumb.map((item, i) => (
            <React.Fragment key={i}>
              {i > 0 && <ChevronRight size={12} />}
              <span style={{ color: i === route.breadcrumb.length - 1 ? 'var(--text-secondary)' : 'var(--text-muted)' }}>
                {item}
              </span>
            </React.Fragment>
          ))}
        </div>
      </div>

      <div className="header-actions">
        {/* System status */}
        <div className="system-status">
          <span className="status-dot" />
          <span>Sistem Aktif</span>
        </div>

        {/* Clock */}
        <div className="header-clock" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{formatTime(time)}</span>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{formatDate(time)}</span>
        </div>

        {/* User dropdown */}
        <div style={{ position: 'relative' }}>
          <div
            className="header-user"
            onClick={(e) => { e.stopPropagation(); setDropdownOpen(!dropdownOpen) }}
          >
            <div className="user-avatar" style={{ width: 32, height: 32, fontSize: '0.7rem' }}>
              {getInitials(user)}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.2 }}>
                {user?.full_name || 'Kullanıcı'}
              </span>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                {user?.email}
              </span>
            </div>
          </div>

          {dropdownOpen && (
            <div style={{
              position: 'absolute',
              top: 'calc(100% + 8px)',
              right: 0,
              width: 180,
              background: 'var(--bg-card)',
              border: '1px solid var(--border-glow)',
              borderRadius: 'var(--radius-md)',
              boxShadow: 'var(--shadow-lg)',
              zIndex: 200,
              overflow: 'hidden',
              animation: 'fadeInUp 0.15s ease'
            }}>
              <button
                onClick={() => { navigate('/ayarlar'); setDropdownOpen(false) }}
                style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  width: '100%', padding: '10px 14px', background: 'none',
                  border: 'none', color: 'var(--text-secondary)', cursor: 'pointer',
                  fontSize: '0.82rem', transition: 'var(--transition)', fontFamily: 'inherit'
                }}
                onMouseEnter={e => e.target.style.background = 'rgba(59,130,246,0.08)'}
                onMouseLeave={e => e.target.style.background = 'none'}
              >
                <User size={15} />
                Profil & Ayarlar
              </button>
              <div style={{ height: 1, background: 'var(--border-color)' }} />
              <button
                onClick={() => { logout(); setDropdownOpen(false) }}
                style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  width: '100%', padding: '10px 14px', background: 'none',
                  border: 'none', color: 'var(--danger)', cursor: 'pointer',
                  fontSize: '0.82rem', transition: 'var(--transition)', fontFamily: 'inherit'
                }}
                onMouseEnter={e => e.target.style.background = 'rgba(239,68,68,0.08)'}
                onMouseLeave={e => e.target.style.background = 'none'}
              >
                <LogOut size={15} />
                Çıkış Yap
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
