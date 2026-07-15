import React, { useState, useEffect, useCallback } from 'react'
import {
  Search, Filter, X, ChevronUp, ChevronDown,
  AlertCircle, Send, User
} from 'lucide-react'
import { api } from '../api/client'
import toast from 'react-hot-toast'

// ── MOCK DATA ──────────────────────────────────────────────────────────────
const mockIncidents = [
  { id: 1, title: 'Google Drive\'da kredi kartı bilgisi tespit edildi', severity: 'critical', status: 'open', policy_name: 'Finansal Veri Koruma', file_path: '/reports/Q4-2024.xlsx', source: 'google_drive', risk_score: 95, detected_patterns: [{ pattern: 'Kredi Kartı No', count: 3, risk: 'critical' }, { pattern: 'CVV Kodu', count: 3, risk: 'critical' }], assigned_to: null, comments: [], created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: 2, title: 'Gmail\'de TC kimlik numarası paylaşıldı', severity: 'high', status: 'investigating', policy_name: 'Kişisel Veri Koruma', file_path: 'Gelen Kutusu', source: 'gmail', risk_score: 78, detected_patterns: [{ pattern: 'TC Kimlik No', count: 5, risk: 'high' }], assigned_to: 'Ahmet Yılmaz', comments: [{ author: 'Ahmet Yılmaz', text: 'İnceleme başlatıldı.', created_at: new Date(Date.now() - 1800000).toISOString() }], created_at: new Date(Date.now() - 7200000).toISOString() },
  { id: 3, title: 'SharePoint\'te IBAN tespit edildi', severity: 'medium', status: 'open', policy_name: 'Finansal Veri Koruma', file_path: '/documents/contracts/2024.docx', source: 'sharepoint', risk_score: 62, detected_patterns: [{ pattern: 'IBAN', count: 2, risk: 'medium' }], assigned_to: null, comments: [], created_at: new Date(Date.now() - 14400000).toISOString() },
  { id: 4, title: 'OneDrive\'da API anahtarı açık', severity: 'critical', status: 'open', policy_name: 'Kod Güvenliği', file_path: '/dev/config.json', source: 'onedrive', risk_score: 91, detected_patterns: [{ pattern: 'API Anahtarı', count: 4, risk: 'critical' }, { pattern: 'Şifre/Hash', count: 1, risk: 'high' }], assigned_to: null, comments: [], created_at: new Date(Date.now() - 18000000).toISOString() },
  { id: 5, title: 'Outlook\'ta sağlık bilgisi', severity: 'high', status: 'resolved', policy_name: 'Sağlık Bilgisi', file_path: 'Gönderilmiş', source: 'outlook', risk_score: 74, detected_patterns: [{ pattern: 'Sağlık Bilgisi', count: 7, risk: 'high' }], assigned_to: 'Zeynep Kaya', comments: [], created_at: new Date(Date.now() - 86400000).toISOString() },
  { id: 6, title: 'Gmail\'de toplu e-posta adresi', severity: 'low', status: 'false_positive', policy_name: 'İletişim Verisi', file_path: 'Giden Kutusu', source: 'gmail', risk_score: 22, detected_patterns: [{ pattern: 'E-posta Adresi', count: 120, risk: 'low' }], assigned_to: null, comments: [], created_at: new Date(Date.now() - 172800000).toISOString() },
  { id: 7, title: 'Google Drive\'da vergi numarası', severity: 'medium', status: 'investigating', policy_name: 'Kişisel Veri Koruma', file_path: '/hr/employees.xlsx', source: 'google_drive', risk_score: 58, detected_patterns: [{ pattern: 'Vergi No', count: 15, risk: 'medium' }], assigned_to: 'Mehmet Demir', comments: [], created_at: new Date(Date.now() - 259200000).toISOString() }
]

const mockUsers = [
  { id: 1, full_name: 'Ahmet Yılmaz', email: 'ahmet@dlp.local' },
  { id: 2, full_name: 'Zeynep Kaya', email: 'zeynep@dlp.local' },
  { id: 3, full_name: 'Mehmet Demir', email: 'mehmet@dlp.local' }
]

const mockPolicies = ['Finansal Veri Koruma', 'Kişisel Veri Koruma', 'Kod Güvenliği', 'Sağlık Bilgisi', 'İletişim Verisi']

// ── CONSTANTS ──────────────────────────────────────────────────────────────
const sevColor = { critical: '#dc2626', high: '#f97316', medium: '#f59e0b', low: '#10b981' }
const sevLabel = { critical: 'Kritik', high: 'Yüksek', medium: 'Orta', low: 'Düşük' }
const sevBg = { critical: 'rgba(220,38,38,0.12)', high: 'rgba(249,115,22,0.12)', medium: 'rgba(245,158,11,0.12)', low: 'rgba(16,185,129,0.12)' }
const stColor = { open: '#3b82f6', investigating: '#f59e0b', resolved: '#10b981', false_positive: '#6b7280' }
const stLabel = { open: 'Açık', investigating: 'İnceleniyor', resolved: 'Çözüldü', false_positive: 'Yanlış Pozitif' }
const srcLabel = { google_drive: '📁 Drive', gmail: '📧 Gmail', onedrive: '💼 OneDrive', sharepoint: '🏗️ SharePoint', outlook: '📮 Outlook' }

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins} dk önce`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs} sa önce`
  return `${Math.floor(hrs / 24)} gün önce`
}

// ── INCIDENT DRAWER ────────────────────────────────────────────────────────
function IncidentDrawer({ incident, onClose, onUpdate }) {
  const [comment, setComment] = useState('')
  const [sending, setSending] = useState(false)
  const [inc, setInc] = useState(incident)

  useEffect(() => setInc(incident), [incident])

  const changeStatus = async (status) => {
    try {
      await api.incidents.changeStatus(inc.id, status)
    } catch { }
    const updated = { ...inc, status }
    setInc(updated)
    onUpdate(updated)
    toast.success(`Durum güncellendi: ${stLabel[status]}`)
  }

  const sendComment = async () => {
    if (!comment.trim()) return
    setSending(true)
    try {
      await api.incidents.addComment(inc.id, comment)
    } catch { }
    const newComment = { author: 'Siz', text: comment, created_at: new Date().toISOString() }
    const updated = { ...inc, comments: [...(inc.comments || []), newComment] }
    setInc(updated)
    onUpdate(updated)
    setComment('')
    setSending(false)
    toast.success('Yorum eklendi.')
  }

  const riskColor = inc.risk_score >= 80 ? '#dc2626' : inc.risk_score >= 50 ? '#f59e0b' : '#10b981'

  return (
    <>
      <div className="drawer-overlay" onClick={onClose} />
      <div className="drawer">
        <div className="drawer-header">
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
              <span style={{
                padding: '3px 10px', borderRadius: 20, fontSize: '0.72rem', fontWeight: 700,
                background: sevBg[inc.severity], color: sevColor[inc.severity],
                border: `1px solid ${sevColor[inc.severity]}30`
              }}>{sevLabel[inc.severity]}</span>
              <span style={{
                padding: '3px 10px', borderRadius: 20, fontSize: '0.72rem', fontWeight: 600,
                background: `${stColor[inc.status]}12`, color: stColor[inc.status],
                border: `1px solid ${stColor[inc.status]}25`
              }}>● {stLabel[inc.status]}</span>
            </div>
            <h3 style={{ fontSize: '1rem', lineHeight: 1.4 }}>{inc.title}</h3>
          </div>
          <button className="modal-close" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="drawer-body">
          {/* Status actions */}
          <div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 8, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px' }}>Durum Değiştir</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {Object.entries(stLabel).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => changeStatus(key)}
                  style={{
                    padding: '6px 12px', borderRadius: 20, fontSize: '0.78rem', fontWeight: 600,
                    border: `1px solid ${inc.status === key ? stColor[key] : 'var(--border-color)'}`,
                    background: inc.status === key ? `${stColor[key]}18` : 'transparent',
                    color: inc.status === key ? stColor[key] : 'var(--text-muted)',
                    cursor: 'pointer', transition: 'var(--transition)', fontFamily: 'inherit'
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* File info */}
          <div style={{ background: 'rgba(10,14,26,0.4)', borderRadius: 10, padding: 14, border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px' }}>Dosya Bilgisi</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {[
                ['Kaynak', srcLabel[inc.source] || inc.source],
                ['Politika', inc.policy_name],
                ['Dosya/Konum', inc.file_path],
                ['Tespit Tarihi', new Date(inc.created_at).toLocaleString('tr-TR')]
              ].map(([k, v]) => (
                <div key={k} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', minWidth: 90, flexShrink: 0 }}>{k}</span>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>{v}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Risk score */}
          <div style={{ background: 'rgba(10,14,26,0.4)', borderRadius: 10, padding: 14, border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px' }}>Risk Skoru</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{
                width: 64, height: 64, borderRadius: '50%',
                background: `conic-gradient(${riskColor} ${inc.risk_score * 3.6}deg, var(--border-color) 0deg)`,
                display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}>
                <div style={{
                  width: 48, height: 48, borderRadius: '50%',
                  background: 'var(--bg-surface)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.95rem', fontWeight: 800, color: riskColor
                }}>
                  {inc.risk_score}
                </div>
              </div>
              <div>
                <div style={{ color: riskColor, fontWeight: 700, marginBottom: 4 }}>
                  {inc.risk_score >= 80 ? 'Yüksek Risk' : inc.risk_score >= 50 ? 'Orta Risk' : 'Düşük Risk'}
                </div>
                <div className="progress" style={{ width: 160 }}>
                  <div className="progress-bar" style={{
                    width: `${inc.risk_score}%`,
                    background: `linear-gradient(to right, ${riskColor}, ${riskColor}99)`
                  }} />
                </div>
              </div>
            </div>
          </div>

          {/* Detected patterns */}
          {inc.detected_patterns?.length > 0 && (
            <div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px' }}>Tespit Edilen Desenler</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {inc.detected_patterns.map((p, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    background: 'rgba(10,14,26,0.4)', borderRadius: 8, padding: '10px 12px',
                    border: '1px solid var(--border-color)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{ width: 8, height: 8, borderRadius: '50%', background: sevColor[p.risk] || '#3b82f6', flexShrink: 0 }} />
                      <span style={{ fontSize: '0.82rem', color: 'var(--text-primary)' }}>{p.pattern}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{p.count} adet</span>
                      <span style={{ fontSize: '0.7rem', color: sevColor[p.risk], background: sevBg[p.risk], padding: '2px 8px', borderRadius: 10, fontWeight: 600 }}>
                        {sevLabel[p.risk]}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Assign */}
          <div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 8, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px' }}>Atama</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <User size={16} color="var(--text-muted)" />
              <select className="form-select" style={{ flex: 1 }}
                value={inc.assigned_to || ''}
                onChange={async (e) => {
                  const val = e.target.value
                  try { await api.incidents.assign(inc.id, val) } catch { }
                  const updated = { ...inc, assigned_to: val }
                  setInc(updated)
                  onUpdate(updated)
                  toast.success(val ? `Atandı: ${val}` : 'Atama kaldırıldı.')
                }}
              >
                <option value="">Atanmamış</option>
                {mockUsers.map(u => <option key={u.id} value={u.full_name}>{u.full_name}</option>)}
              </select>
            </div>
          </div>

          {/* Comments */}
          <div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px' }}>
              Yorumlar ({(inc.comments || []).length})
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 12 }}>
              {(inc.comments || []).length === 0 ? (
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>Henüz yorum yok.</p>
              ) : (
                (inc.comments || []).map((c, i) => (
                  <div key={i} style={{
                    background: 'rgba(59,130,246,0.05)', border: '1px solid rgba(59,130,246,0.1)',
                    borderRadius: 8, padding: '10px 12px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                      <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--primary-light)' }}>{c.author}</span>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{timeAgo(c.created_at)}</span>
                    </div>
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{c.text}</p>
                  </div>
                ))
              )}
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <textarea
                className="form-textarea"
                placeholder="Yorum ekle..."
                value={comment}
                onChange={e => setComment(e.target.value)}
                style={{ flex: 1, minHeight: 60 }}
                onKeyDown={e => { if (e.ctrlKey && e.key === 'Enter') sendComment() }}
              />
              <button className="btn btn-primary" onClick={sendComment} disabled={sending || !comment.trim()}
                style={{ alignSelf: 'flex-end', padding: '10px' }}>
                {sending ? <div className="loading-spinner" style={{ width: 16, height: 16 }} /> : <Send size={16} />}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

// ── MAIN COMPONENT ─────────────────────────────────────────────────────────
export default function Incidents() {
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterSeverity, setFilterSeverity] = useState('')
  const [filterPolicy, setFilterPolicy] = useState('')
  const [sortField, setSortField] = useState('created_at')
  const [sortDir, setSortDir] = useState('desc')
  const [selected, setSelected] = useState(null)

  const load = useCallback(async () => {
    try {
      const res = await api.incidents.list({ limit: 100 })
      setIncidents(res.data?.items || res.data || mockIncidents)
    } catch {
      setIncidents(mockIncidents)
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const handleSort = (field) => {
    if (sortField === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortField(field); setSortDir('desc') }
  }

  const SortIcon = ({ field }) => {
    if (sortField !== field) return <ChevronUp size={12} style={{ opacity: 0.3 }} />
    return sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />
  }

  const filtered = incidents.filter(inc => {
    const matchSearch = !search || inc.title.toLowerCase().includes(search.toLowerCase()) || (inc.policy_name || '').toLowerCase().includes(search.toLowerCase())
    const matchStatus = !filterStatus || inc.status === filterStatus
    const matchSev = !filterSeverity || inc.severity === filterSeverity
    const matchPolicy = !filterPolicy || inc.policy_name === filterPolicy
    return matchSearch && matchStatus && matchSev && matchPolicy
  }).sort((a, b) => {
    let av = a[sortField], bv = b[sortField]
    if (sortField === 'created_at') { av = new Date(av).getTime(); bv = new Date(bv).getTime() }
    if (sortField === 'risk_score') { av = Number(av); bv = Number(bv) }
    if (av < bv) return sortDir === 'asc' ? -1 : 1
    if (av > bv) return sortDir === 'asc' ? 1 : -1
    return 0
  })

  const statusCounts = {
    open: incidents.filter(i => i.status === 'open').length,
    investigating: incidents.filter(i => i.status === 'investigating').length,
    resolved: incidents.filter(i => i.status === 'resolved').length,
    false_positive: incidents.filter(i => i.status === 'false_positive').length
  }

  return (
    <div style={{ animation: 'fadeInUp 0.4s ease' }}>
      <div className="page-header">
        <div>
          <h2>Olay Yönetimi</h2>
          <p>{incidents.length} toplam olay</p>
        </div>
      </div>

      {/* Stats strip */}
      <div className="stats-strip">
        {Object.entries(stLabel).map(([key, label]) => (
          <div key={key} className="stats-strip-item" style={{ borderColor: `${stColor[key]}20`, cursor: 'pointer' }}
            onClick={() => setFilterStatus(filterStatus === key ? '' : key)}>
            <div className="count" style={{ color: stColor[key] }}>{statusCounts[key]}</div>
            <span>{label}</span>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="filter-row">
        <div className="search-input-wrap">
          <Search size={15} className="search-icon" />
          <input className="form-input" placeholder="Olay ara..." value={search} onChange={e => setSearch(e.target.value)} style={{ paddingLeft: 36 }} />
        </div>
        <select className="form-select" value={filterStatus} onChange={e => setFilterStatus(e.target.value)} style={{ width: 140 }}>
          <option value="">Tüm Durumlar</option>
          {Object.entries(stLabel).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select className="form-select" value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)} style={{ width: 130 }}>
          <option value="">Tüm Önemler</option>
          {Object.entries(sevLabel).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select className="form-select" value={filterPolicy} onChange={e => setFilterPolicy(e.target.value)} style={{ width: 180 }}>
          <option value="">Tüm Politikalar</option>
          {mockPolicies.map(p => <option key={p} value={p}>{p}</option>)}
        </select>
        {(search || filterStatus || filterSeverity || filterPolicy) && (
          <button className="btn btn-ghost btn-sm" onClick={() => { setSearch(''); setFilterStatus(''); setFilterSeverity(''); setFilterPolicy('') }}>
            <X size={14} /> Temizle
          </button>
        )}
      </div>

      {/* Table */}
      {loading ? (
        <div className="loading-center"><div className="loading-spinner lg" /><span>Olaylar yükleniyor...</span></div>
      ) : (
        <div className="table-container">
          <table className="dlp-table">
            <thead>
              <tr>
                <th style={{ width: 50 }}>#</th>
                <th className="sortable" onClick={() => handleSort('title')}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>Başlık <SortIcon field="title" /></span>
                </th>
                <th className="sortable" onClick={() => handleSort('severity')}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>Önem <SortIcon field="severity" /></span>
                </th>
                <th>Durum</th>
                <th>Politika</th>
                <th>Kaynak</th>
                <th className="sortable" onClick={() => handleSort('risk_score')}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>Risk <SortIcon field="risk_score" /></span>
                </th>
                <th className="sortable" onClick={() => handleSort('created_at')}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>Tarih <SortIcon field="created_at" /></span>
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr><td colSpan={8} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                  <AlertCircle size={24} style={{ marginBottom: 8, display: 'block', margin: '0 auto 8px' }} />
                  Olay bulunamadı
                </td></tr>
              ) : filtered.map(inc => (
                <tr key={inc.id} className="clickable" onClick={() => setSelected(inc)}>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>#{inc.id}</td>
                  <td>
                    <div style={{ fontWeight: 500, color: 'var(--text-primary)', marginBottom: 2 }}>{inc.title}</div>
                    {inc.assigned_to && <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>→ {inc.assigned_to}</div>}
                  </td>
                  <td>
                    <span style={{
                      padding: '3px 10px', borderRadius: 20, fontSize: '0.72rem', fontWeight: 600,
                      background: sevBg[inc.severity], color: sevColor[inc.severity],
                      border: `1px solid ${sevColor[inc.severity]}30`
                    }}>{sevLabel[inc.severity]}</span>
                  </td>
                  <td>
                    <span style={{
                      padding: '3px 10px', borderRadius: 20, fontSize: '0.72rem', fontWeight: 600,
                      background: `${stColor[inc.status]}12`, color: stColor[inc.status],
                      border: `1px solid ${stColor[inc.status]}25`
                    }}>● {stLabel[inc.status]}</span>
                  </td>
                  <td style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', maxWidth: 150 }}>
                    <div className="truncate">{inc.policy_name}</div>
                  </td>
                  <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{srcLabel[inc.source] || inc.source}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div className="progress" style={{ width: 50 }}>
                        <div className="progress-bar" style={{
                          width: `${inc.risk_score}%`,
                          background: inc.risk_score >= 80 ? 'var(--critical)' : inc.risk_score >= 50 ? 'var(--warning)' : 'var(--success)'
                        }} />
                      </div>
                      <span style={{ fontSize: '0.78rem', fontWeight: 600, color: inc.risk_score >= 80 ? 'var(--danger)' : inc.risk_score >= 50 ? 'var(--warning)' : 'var(--success)' }}>
                        {inc.risk_score}
                      </span>
                    </div>
                  </td>
                  <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {timeAgo(inc.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Drawer */}
      {selected && (
        <IncidentDrawer
          incident={selected}
          onClose={() => setSelected(null)}
          onUpdate={(updated) => {
            setIncidents(p => p.map(inc => inc.id === updated.id ? updated : inc))
            setSelected(updated)
          }}
        />
      )}
    </div>
  )
}
