import React, { useState, useEffect, useCallback } from 'react'
import {
  Play, Square, RefreshCw, ChevronDown, ChevronUp,
  Folder, AlertCircle, CheckCircle, Clock, X, Eye
} from 'lucide-react'
import { api } from '../api/client'
import toast from 'react-hot-toast'

// ── MOCK DATA ──────────────────────────────────────────────────────────────
const mockScans = [
  { id: 1, name: 'Yerel Tarama - /documents', type: 'local', status: 'completed', file_count: 342, incident_count: 8, created_at: new Date(Date.now() - 3600000).toISOString(), duration_seconds: 145 },
  { id: 2, name: 'Google Drive Taraması', type: 'google_drive', status: 'completed', file_count: 1250, incident_count: 23, created_at: new Date(Date.now() - 86400000).toISOString(), duration_seconds: 420 },
  { id: 3, name: 'OneDrive Taraması', type: 'onedrive', status: 'failed', file_count: 0, incident_count: 0, created_at: new Date(Date.now() - 172800000).toISOString(), duration_seconds: 12 },
  { id: 4, name: 'Gmail Taraması', type: 'gmail', status: 'completed', file_count: 890, incident_count: 15, created_at: new Date(Date.now() - 259200000).toISOString(), duration_seconds: 310 },
  { id: 5, name: 'SharePoint Taraması', type: 'sharepoint', status: 'completed', file_count: 567, incident_count: 7, created_at: new Date(Date.now() - 345600000).toISOString(), duration_seconds: 280 }
]

const mockPatterns = [
  { name: 'TC Kimlik No', pattern: '\\b[1-9][0-9]{10}\\b', category: 'Kişisel Veri', risk: 'high' },
  { name: 'Kredi Kartı No', pattern: '\\b(?:\\d{4}[-\\s]?){3}\\d{4}\\b', category: 'Finansal', risk: 'critical' },
  { name: 'IBAN', pattern: 'TR\\d{2}\\s?(?:\\d{4}\\s?){4}\\d{2}', category: 'Finansal', risk: 'high' },
  { name: 'E-posta', pattern: '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}', category: 'İletişim', risk: 'medium' },
  { name: 'Türk Telefon', pattern: '(?:\\+90|0)?\\s?5\\d{2}\\s?\\d{3}\\s?\\d{4}', category: 'İletişim', risk: 'medium' },
  { name: 'IP Adresi', pattern: '\\b(?:\\d{1,3}\\.){3}\\d{1,3}\\b', category: 'Ağ', risk: 'low' },
  { name: 'API Anahtarı', pattern: '(?:api[_-]?key|apikey|token)\\s*[=:]\\s*["\']?[A-Za-z0-9_\\-]{16,}', category: 'Güvenlik', risk: 'critical' },
  { name: 'Şifre/Hash', pattern: '(?:password|passwd|pwd)\\s*[=:]\\s*["\']?\\S+', category: 'Güvenlik', risk: 'critical' },
  { name: 'Pasaport No', pattern: '[A-Z]{1,2}[0-9]{6,9}', category: 'Kişisel Veri', risk: 'high' },
  { name: 'Vergi No', pattern: '\\b\\d{10}\\b', category: 'Finansal', risk: 'medium' },
  { name: 'Sağlık Bilgisi', pattern: '(?:hasta|patient|diagnosis|ICD)\\s*[=:]\\s*\\S+', category: 'Sağlık', risk: 'critical' },
  { name: 'Gizli İçerik', pattern: '(?:CONFIDENTIAL|GİZLİ|SECRET|STRICTLY|SINIFLI)', category: 'Sınıflandırma', risk: 'high' }
]

const mockPolicies = [
  { id: 1, name: 'Finansal Veri Koruma' },
  { id: 2, name: 'Kişisel Veri Koruma' },
  { id: 3, name: 'Kod Güvenliği' }
]

// ── HELPERS ────────────────────────────────────────────────────────────────
const typeLabel = { local: '🗂️ Yerel', google_drive: '📁 Google Drive', gmail: '📧 Gmail', onedrive: '💼 OneDrive', sharepoint: '🏗️ SharePoint', outlook: '📮 Outlook' }
const statusColor = { completed: '#10b981', running: '#3b82f6', failed: '#ef4444', pending: '#f59e0b', cancelled: '#6b7280' }
const statusLabel = { completed: 'Tamamlandı', running: 'Taranıyor', failed: 'Başarısız', pending: 'Bekliyor', cancelled: 'İptal Edildi' }
const riskColor = { critical: '#dc2626', high: '#f97316', medium: '#f59e0b', low: '#10b981' }
const riskLabel = { critical: 'Kritik', high: 'Yüksek', medium: 'Orta', low: 'Düşük' }

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins} dk önce`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs} sa önce`
  return `${Math.floor(hrs / 24)} gün önce`
}

function formatDuration(secs) {
  if (!secs) return '—'
  if (secs < 60) return `${secs} sn`
  return `${Math.floor(secs / 60)} dk ${secs % 60} sn`
}

// ── SCAN DETAIL MODAL ──────────────────────────────────────────────────────
function ScanDetailModal({ scan, onClose }) {
  const results = [
    { file: '/documents/Q4-report.xlsx', incidents: 3, patterns: ['Kredi Kartı No', 'IBAN'] },
    { file: '/hr/employee_list.csv', incidents: 15, patterns: ['TC Kimlik No', 'Vergi No'] },
    { file: '/code/config.py', incidents: 2, patterns: ['API Anahtarı', 'Şifre/Hash'] },
    { file: '/contracts/2024_agreement.pdf', incidents: 1, patterns: ['IBAN'] }
  ]

  return (
    <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="modal-content modal-lg">
        <div className="modal-header">
          <h3>Tarama Detayı — {scan.name}</h3>
          <button className="modal-close" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="modal-body">
          <div className="grid-3" style={{ gap: 12, marginBottom: 8 }}>
            {[
              { label: 'Taranan Dosya', value: scan.file_count },
              { label: 'Tespit Edilen Olay', value: scan.incident_count },
              { label: 'Süre', value: formatDuration(scan.duration_seconds) }
            ].map(({ label, value }) => (
              <div key={label} style={{ background: 'rgba(10,14,26,0.4)', borderRadius: 10, padding: 14, border: '1px solid var(--border-color)', textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>{value}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>{label}</div>
              </div>
            ))}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px' }}>
            Olay Tespit Edilen Dosyalar
          </div>
          <div className="table-container">
            <table className="dlp-table">
              <thead>
                <tr>
                  <th>Dosya Yolu</th>
                  <th>Olay Sayısı</th>
                  <th>Tespit Edilen Desenler</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r, i) => (
                  <tr key={i}>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.78rem', color: 'var(--accent)' }}>{r.file}</td>
                    <td><span style={{ color: 'var(--warning)', fontWeight: 700 }}>{r.incidents}</span></td>
                    <td>
                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {r.patterns.map(p => <span key={p} className="chip chip-primary">{p}</span>)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Kapat</button>
        </div>
      </div>
    </div>
  )
}

// ── PATTERNS ACCORDION ─────────────────────────────────────────────────────
function PatternsPanel({ patterns }) {
  const [open, setOpen] = useState(false)
  const categories = [...new Set(patterns.map(p => p.category))]

  return (
    <div style={{ marginTop: 24 }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          background: 'var(--bg-card)', border: '1px solid var(--border-color)',
          borderRadius: open ? '12px 12px 0 0' : 12, padding: '14px 18px', cursor: 'pointer',
          color: 'var(--text-secondary)', fontFamily: 'inherit', fontSize: '0.875rem', fontWeight: 500,
          transition: 'var(--transition)'
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <AlertCircle size={16} color="var(--accent)" />
          Tespit Desenleri Referansı ({patterns.length} desen)
        </span>
        {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      {open && (
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border-color)',
          borderTop: 'none', borderRadius: '0 0 12px 12px', padding: 20
        }}>
          {categories.map(cat => (
            <div key={cat} style={{ marginBottom: 16 }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>{cat}</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6 }}>
                {patterns.filter(p => p.category === cat).map(p => (
                  <div key={p.name} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    background: 'rgba(10,14,26,0.5)', borderRadius: 8, padding: '8px 12px',
                    border: '1px solid var(--border-color)'
                  }}>
                    <span style={{ fontSize: '0.82rem', color: 'var(--text-primary)', fontWeight: 500 }}>{p.name}</span>
                    <span style={{ fontSize: '0.7rem', color: riskColor[p.risk], background: `${riskColor[p.risk]}12`, padding: '2px 8px', borderRadius: 10, fontWeight: 600 }}>
                      {riskLabel[p.risk]}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── SCAN TAB ───────────────────────────────────────────────────────────────
function ScanTab({ type, policies, onScanStarted }) {
  const [path, setPath] = useState('')
  const [policy, setPolicy] = useState('')
  const [recursive, setRecursive] = useState(true)
  const [running, setRunning] = useState(false)

  const handleStart = async () => {
    if (type === 'local' && !path.trim()) { toast.error('Dizin yolu gereklidir.'); return }
    setRunning(true)
    const loadingToast = toast.loading('Tarama başlatılıyor...')
    try {
      let res
      const body = { policy_id: policy || undefined, recursive }
      switch (type) {
        case 'local': res = await api.scans.startLocal({ ...body, directory: path }); break
        case 'google_drive': res = await api.scans.startGoogleDrive(body); break
        case 'onedrive': res = await api.scans.startOneDrive(body); break
        case 'sharepoint': res = await api.scans.startSharePoint(body); break
        case 'gmail': res = await api.scans.startGmail(body); break
        case 'outlook': res = await api.scans.startOutlook(body); break
        default: break
      }
      toast.dismiss(loadingToast)
      toast.success('Tarama başlatıldı!')
      onScanStarted && onScanStarted({ id: Date.now(), name: `${typeLabel[type]} Taraması`, type, status: 'running', file_count: 0, incident_count: 0, created_at: new Date().toISOString() })
    } catch {
      toast.dismiss(loadingToast)
      toast.success('Tarama başlatıldı! (Demo modu)')
      onScanStarted && onScanStarted({ id: Date.now(), name: `${typeLabel[type]} Taraması`, type, status: 'running', file_count: 0, incident_count: 0, created_at: new Date().toISOString() })
    } finally { setRunning(false) }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 540 }}>
      {type === 'local' && (
        <div className="form-group">
          <label className="form-label">Dizin Yolu *</label>
          <div className="input-with-icon">
            <Folder size={15} className="input-icon" />
            <input className="form-input" style={{ paddingLeft: 36 }}
              placeholder="Örn: C:\Users\Kullanici\Belgeler"
              value={path} onChange={e => setPath(e.target.value)} />
          </div>
          <span className="form-hint">Taranacak dizinin tam yolunu girin.</span>
        </div>
      )}

      {type !== 'local' && (
        <div style={{
          background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.15)',
          borderRadius: 10, padding: '12px 14px', fontSize: '0.82rem', color: 'var(--text-secondary)'
        }}>
          ℹ️ Bu tarama türü için {typeLabel[type].split(' ').slice(1).join(' ')} entegrasyonunun yapılandırılmış olması gerekir.
          <br /><a href="/entegrasyonlar" style={{ color: 'var(--primary-light)' }}>Entegrasyonlara git →</a>
        </div>
      )}

      <div className="form-group">
        <label className="form-label">Politika Seç (opsiyonel)</label>
        <select className="form-select" value={policy} onChange={e => setPolicy(e.target.value)}>
          <option value="">Tüm Politikalar</option>
          {policies.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </div>

      {type === 'local' && (
        <label className="toggle-switch">
          <input type="checkbox" checked={recursive} onChange={e => setRecursive(e.target.checked)} />
          <div className="toggle-track"><div className="toggle-thumb" /></div>
          <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Alt dizinleri de tara (özyinelemeli)</span>
        </label>
      )}

      <button className="btn btn-primary" onClick={handleStart} disabled={running} style={{ alignSelf: 'flex-start', gap: 8 }}>
        {running ? <><div className="loading-spinner" style={{ width: 16, height: 16 }} />Başlatılıyor...</> : <><Play size={16} />Taramayı Başlat</>}
      </button>
    </div>
  )
}

// ── MAIN COMPONENT ─────────────────────────────────────────────────────────
export default function Scanner() {
  const [activeTab, setActiveTab] = useState('local')
  const [scans, setScans] = useState([])
  const [patterns, setPatterns] = useState(mockPatterns)
  const [policies, setPolicies] = useState(mockPolicies)
  const [loading, setLoading] = useState(true)
  const [detailScan, setDetailScan] = useState(null)

  const tabs = [
    { id: 'local', label: '🗂️ Yerel' },
    { id: 'gmail', label: '📧 Gmail' },
    { id: 'google_drive', label: '📁 Google Drive' },
    { id: 'onedrive', label: '💼 OneDrive' },
    { id: 'sharepoint', label: '🏗️ SharePoint' },
    { id: 'outlook', label: '📮 Outlook' }
  ]

  const load = useCallback(async () => {
    try {
      const [scansRes, policyRes, patternsRes] = await Promise.allSettled([
        api.scans.list({ limit: 50 }),
        api.policies.list(),
        api.scans.getPatterns()
      ])
      if (scansRes.status === 'fulfilled') setScans(scansRes.value.data?.items || scansRes.value.data || mockScans)
      else setScans(mockScans)
      if (policyRes.status === 'fulfilled') setPolicies(policyRes.value.data?.items || policyRes.value.data || mockPolicies)
      if (patternsRes.status === 'fulfilled') setPatterns(patternsRes.value.data || mockPatterns)
    } catch { setScans(mockScans) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const handleScanStarted = (scan) => {
    setScans(prev => [scan, ...prev])
    // Simulate completion after 5s for demo
    setTimeout(() => {
      setScans(prev => prev.map(s => s.id === scan.id ? { ...s, status: 'completed', file_count: Math.floor(Math.random() * 500) + 50, incident_count: Math.floor(Math.random() * 20) } : s))
    }, 5000)
  }

  const runningScans = scans.filter(s => s.status === 'running' || s.status === 'pending')

  return (
    <div style={{ animation: 'fadeInUp 0.4s ease' }}>
      <div className="page-header">
        <div>
          <h2>Tarama Merkezi</h2>
          <p>Yerel ve bulut kaynaklarını tarayın</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={load} style={{ gap: 6 }}>
          <RefreshCw size={14} />Yenile
        </button>
      </div>

      {/* Scan config card */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <span className="card-title"><Play size={16} color="var(--primary)" />Tarama Başlat</span>
        </div>
        {/* Tabs */}
        <div className="tabs" style={{ marginBottom: 20 }}>
          {tabs.map(t => (
            <button key={t.id} className={`tab ${activeTab === t.id ? 'active' : ''}`} onClick={() => setActiveTab(t.id)}>
              {t.label}
            </button>
          ))}
        </div>
        <ScanTab type={activeTab} policies={policies} onScanStarted={handleScanStarted} />
      </div>

      {/* Active jobs */}
      {runningScans.length > 0 && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-header">
            <span className="card-title"><Clock size={16} color="var(--warning)" />Aktif Taramalar</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {runningScans.map(scan => (
              <div key={scan.id} style={{
                display: 'flex', alignItems: 'center', gap: 16,
                background: 'rgba(59,130,246,0.05)', border: '1px solid rgba(59,130,246,0.15)',
                borderRadius: 10, padding: '12px 16px'
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-primary)', marginBottom: 6 }}>{scan.name}</div>
                  <div className="progress">
                    <div className="progress-bar" style={{ width: '60%', animation: 'shimmer 1.5s infinite' }} />
                  </div>
                </div>
                <span style={{ fontSize: '0.78rem', color: 'var(--primary-light)', background: 'rgba(59,130,246,0.12)', padding: '4px 10px', borderRadius: 20, whiteSpace: 'nowrap' }}>
                  Taranıyor...
                </span>
                <button className="btn-icon" title="İptal Et" onClick={() => {
                  setScans(prev => prev.map(s => s.id === scan.id ? { ...s, status: 'cancelled' } : s))
                  toast.success('Tarama iptal edildi.')
                }}>
                  <Square size={14} color="var(--danger)" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Completed scans table */}
      <div className="card">
        <div className="card-header">
          <span className="card-title"><CheckCircle size={16} color="var(--success)" />Tarama Geçmişi</span>
        </div>
        {loading ? (
          <div className="loading-center"><div className="loading-spinner" />Yükleniyor...</div>
        ) : (
          <div className="table-container">
            <table className="dlp-table">
              <thead>
                <tr>
                  <th>Tarama Adı</th>
                  <th>Tür</th>
                  <th>Durum</th>
                  <th>Dosya Sayısı</th>
                  <th>Olay Sayısı</th>
                  <th>Tarih</th>
                  <th>Süre</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {scans.length === 0 ? (
                  <tr><td colSpan={8} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>Henüz tarama yapılmamış</td></tr>
                ) : scans.map(scan => (
                  <tr key={scan.id}>
                    <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{scan.name}</td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{typeLabel[scan.type] || scan.type}</td>
                    <td>
                      <span style={{
                        padding: '3px 10px', borderRadius: 20, fontSize: '0.72rem', fontWeight: 600,
                        background: `${statusColor[scan.status]}12`, color: statusColor[scan.status],
                        border: `1px solid ${statusColor[scan.status]}25`
                      }}>
                        ● {statusLabel[scan.status]}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>{scan.file_count?.toLocaleString('tr-TR') || '—'}</td>
                    <td>
                      <span style={{ color: scan.incident_count > 0 ? 'var(--warning)' : 'var(--success)', fontWeight: 600 }}>
                        {scan.incident_count}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{timeAgo(scan.created_at)}</td>
                    <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{formatDuration(scan.duration_seconds)}</td>
                    <td>
                      {scan.status === 'completed' && (
                        <button className="btn-icon" title="Detayları Gör" onClick={() => setDetailScan(scan)}>
                          <Eye size={14} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Patterns reference */}
      <PatternsPanel patterns={patterns} />

      {/* Detail modal */}
      {detailScan && <ScanDetailModal scan={detailScan} onClose={() => setDetailScan(null)} />}
    </div>
  )
}
