import React, { useState, useEffect, useCallback } from 'react'
import { Plus, Shield, Pencil, Trash2, Search, ToggleLeft, ToggleRight, X, Check } from 'lucide-react'
import { api } from '../api/client'
import toast from 'react-hot-toast'

// ── MOCK DATA ──────────────────────────────────────────────────────────────
const mockPolicies = [
  {
    id: 1, name: 'Finansal Veri Koruma', description: 'Kredi kartı, IBAN ve banka hesap bilgilerinin korunması',
    severity: 'critical', is_active: true, incident_count: 45,
    data_types: ['Kredi Kartı', 'IBAN', 'Banka Hesabı'],
    sources: ['google_drive', 'gmail'],
    action: 'block', file_types: ['pdf', 'xlsx', 'csv']
  },
  {
    id: 2, name: 'Kişisel Veri Koruma (KVKK)', description: 'TC kimlik no ve kişisel bilgilerin KVKK kapsamında korunması',
    severity: 'high', is_active: true, incident_count: 67,
    data_types: ['TC Kimlik', 'Pasaport', 'Telefon'],
    sources: ['onedrive', 'sharepoint'],
    action: 'warn', file_types: ['pdf', 'docx']
  },
  {
    id: 3, name: 'Gizli İçerik Politikası', description: 'Gizli ve şirket içi dökümanların takibi',
    severity: 'high', is_active: true, incident_count: 23,
    data_types: ['Gizli İçerik', 'API Anahtarı'],
    sources: ['google_drive', 'onedrive', 'sharepoint'],
    action: 'quarantine', file_types: ['txt', 'json', 'py', 'js']
  },
  {
    id: 4, name: 'Sağlık Bilgisi Koruması', description: 'Hasta ve sağlık verilerinin korunması',
    severity: 'critical', is_active: false, incident_count: 8,
    data_types: ['Sağlık Bilgisi'],
    sources: ['gmail', 'outlook'],
    action: 'block', file_types: ['pdf', 'docx', 'xlsx']
  },
  {
    id: 5, name: 'Kod ve API Güvenliği', description: 'Kaynak kod ve API anahtarlarının tespit edilmesi',
    severity: 'medium', is_active: true, incident_count: 34,
    data_types: ['API Anahtarı', 'Şifre/Hash'],
    sources: ['google_drive', 'onedrive'],
    action: 'warn', file_types: ['py', 'js', 'json', 'yaml']
  },
  {
    id: 6, name: 'İletişim Verisi', description: 'E-posta ve telefon numaralarının toplu paylaşımının önlenmesi',
    severity: 'low', is_active: true, incident_count: 12,
    data_types: ['E-posta', 'Telefon'],
    sources: ['gmail', 'outlook'],
    action: 'allow', file_types: ['csv', 'xlsx']
  }
]

const DATA_TYPE_OPTIONS = [
  'TC Kimlik', 'Kredi Kartı', 'IBAN', 'E-posta', 'Telefon', 'IP Adresi',
  'API Anahtarı', 'Şifre/Hash', 'Pasaport', 'Vergi No', 'Sağlık Bilgisi', 'Gizli İçerik'
]

const FILE_TYPE_OPTIONS = [
  { label: 'PDF', value: 'pdf' },
  { label: 'Word (docx)', value: 'docx' },
  { label: 'Excel (xlsx)', value: 'xlsx' },
  { label: 'TXT', value: 'txt' },
  { label: 'CSV', value: 'csv' },
  { label: 'JSON', value: 'json' },
  { label: 'Python', value: 'py' },
  { label: 'JavaScript', value: 'js' },
  { label: 'YAML', value: 'yaml' },
  { label: 'XML', value: 'xml' }
]

const SOURCE_OPTIONS = [
  { label: 'Google Drive', value: 'google_drive' },
  { label: 'Gmail', value: 'gmail' },
  { label: 'OneDrive', value: 'onedrive' },
  { label: 'SharePoint', value: 'sharepoint' },
  { label: 'Outlook', value: 'outlook' }
]

const SEVERITY_OPTIONS = [
  { label: 'Kritik', value: 'critical' },
  { label: 'Yüksek', value: 'high' },
  { label: 'Orta', value: 'medium' },
  { label: 'Düşük', value: 'low' }
]

const ACTION_OPTIONS = [
  { label: 'Engelle', value: 'block' },
  { label: 'Uyar', value: 'warn' },
  { label: 'İzin Ver', value: 'allow' },
  { label: 'Karantinaya Al', value: 'quarantine' }
]

const severityColor = { critical: '#dc2626', high: '#f97316', medium: '#f59e0b', low: '#10b981' }
const severityBg = { critical: 'rgba(220,38,38,0.15)', high: 'rgba(249,115,22,0.15)', medium: 'rgba(245,158,11,0.15)', low: 'rgba(16,185,129,0.15)' }
const severityLabel = { critical: 'Kritik', high: 'Yüksek', medium: 'Orta', low: 'Düşük' }
const actionLabel = { block: 'Engelle', warn: 'Uyar', allow: 'İzin Ver', quarantine: 'Karantina' }
const sourceIcon = { google_drive: '📁', gmail: '📧', onedrive: '💼', sharepoint: '🏗️', outlook: '📮' }
const sourceLabel = { google_drive: 'Drive', gmail: 'Gmail', onedrive: 'OneDrive', sharepoint: 'SharePoint', outlook: 'Outlook' }

// ── POLICY FORM ────────────────────────────────────────────────────────────
const emptyForm = {
  name: '', description: '', severity: 'medium', is_active: true,
  data_types: [], action: 'warn', file_types: [], sources: []
}

function PolicyForm({ form, setForm }) {
  const toggle = (field, value) => {
    setForm(f => ({
      ...f,
      [field]: f[field].includes(value) ? f[field].filter(v => v !== value) : [...f[field], value]
    }))
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      <div className="grid-2">
        <div className="form-group">
          <label className="form-label">Politika Adı *</label>
          <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Örn: Finansal Veri Koruma" />
        </div>
        <div className="form-group">
          <label className="form-label">Önem Derecesi</label>
          <select className="form-select" value={form.severity} onChange={e => setForm({ ...form, severity: e.target.value })}>
            {SEVERITY_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Açıklama</label>
        <textarea className="form-textarea" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Politika hakkında kısa açıklama..." />
      </div>

      <div className="form-group">
        <label className="form-label">Aksiyon</label>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {ACTION_OPTIONS.map(o => (
            <label key={o.value} className="radio-label">
              <input type="radio" name="action" value={o.value} checked={form.action === o.value} onChange={() => setForm({ ...form, action: o.value })} />
              {o.label}
            </label>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Tespit Edilecek Veri Türleri</label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
          {DATA_TYPE_OPTIONS.map(dt => (
            <label key={dt} className="checkbox-label">
              <input type="checkbox" checked={form.data_types.includes(dt)} onChange={() => toggle('data_types', dt)} />
              {dt}
            </label>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Dosya Türleri</label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
          {FILE_TYPE_OPTIONS.map(ft => (
            <label key={ft.value} className="checkbox-label">
              <input type="checkbox" checked={form.file_types.includes(ft.value)} onChange={() => toggle('file_types', ft.value)} />
              {ft.label}
            </label>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Bulut Kaynakları</label>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {SOURCE_OPTIONS.map(s => (
            <label key={s.value} className="checkbox-label">
              <input type="checkbox" checked={form.sources.includes(s.value)} onChange={() => toggle('sources', s.value)} />
              {s.label}
            </label>
          ))}
        </div>
      </div>

      <label className="toggle-switch">
        <input type="checkbox" checked={form.is_active} onChange={e => setForm({ ...form, is_active: e.target.checked })} />
        <div className="toggle-track">
          <div className="toggle-thumb" />
        </div>
        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Politika Aktif</span>
      </label>
    </div>
  )
}

// ── MAIN COMPONENT ─────────────────────────────────────────────────────────
export default function Policies() {
  const [policies, setPolicies] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterSeverity, setFilterSeverity] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editPolicy, setEditPolicy] = useState(null)
  const [deletePolicy, setDeletePolicy] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const load = useCallback(async () => {
    try {
      const res = await api.policies.list()
      setPolicies(res.data?.items || res.data || mockPolicies)
    } catch {
      setPolicies(mockPolicies)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const openCreate = () => {
    setEditPolicy(null)
    setForm(emptyForm)
    setModalOpen(true)
  }

  const openEdit = (policy) => {
    setEditPolicy(policy)
    setForm({
      name: policy.name,
      description: policy.description || '',
      severity: policy.severity,
      is_active: policy.is_active,
      data_types: policy.data_types || [],
      action: policy.action || 'warn',
      file_types: policy.file_types || [],
      sources: policy.sources || []
    })
    setModalOpen(true)
  }

  const handleSave = async () => {
    if (!form.name.trim()) { toast.error('Politika adı gereklidir.'); return }
    setSaving(true)
    try {
      if (editPolicy) {
        await api.policies.update(editPolicy.id, form)
        setPolicies(p => p.map(pol => pol.id === editPolicy.id ? { ...pol, ...form } : pol))
        toast.success('Politika güncellendi!')
      } else {
        const res = await api.policies.create(form)
        const newPol = res.data || { ...form, id: Date.now(), incident_count: 0 }
        setPolicies(p => [newPol, ...p])
        toast.success('Politika oluşturuldu!')
      }
      setModalOpen(false)
    } catch {
      // Optimistic UI for demo
      if (editPolicy) {
        setPolicies(p => p.map(pol => pol.id === editPolicy.id ? { ...pol, ...form } : pol))
        toast.success('Politika güncellendi!')
      } else {
        setPolicies(p => [{ ...form, id: Date.now(), incident_count: 0 }, ...p])
        toast.success('Politika oluşturuldu!')
      }
      setModalOpen(false)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!deletePolicy) return
    setDeleting(true)
    try {
      await api.policies.remove(deletePolicy.id)
    } catch { }
    setPolicies(p => p.filter(pol => pol.id !== deletePolicy.id))
    toast.success('Politika silindi.')
    setDeletePolicy(null)
    setDeleting(false)
  }

  const handleToggle = async (policy) => {
    try {
      await api.policies.toggle(policy.id)
    } catch { }
    setPolicies(p => p.map(pol => pol.id === policy.id ? { ...pol, is_active: !pol.is_active } : pol))
    toast.success(`Politika ${!policy.is_active ? 'etkinleştirildi' : 'devre dışı bırakıldı'}.`)
  }

  const filtered = policies.filter(p => {
    const matchSearch = !search || p.name.toLowerCase().includes(search.toLowerCase()) || (p.description || '').toLowerCase().includes(search.toLowerCase())
    const matchSev = !filterSeverity || p.severity === filterSeverity
    const matchStatus = !filterStatus || (filterStatus === 'active' ? p.is_active : !p.is_active)
    return matchSearch && matchSev && matchStatus
  })

  return (
    <div style={{ animation: 'fadeInUp 0.4s ease' }}>
      {/* Header */}
      <div className="page-header">
        <div>
          <h2>Politika Yönetimi</h2>
          <p>{policies.length} politika tanımlı</p>
        </div>
        <button className="btn btn-primary" onClick={openCreate}>
          <Plus size={16} /> Yeni Politika
        </button>
      </div>

      {/* Filters */}
      <div className="filter-row">
        <div className="search-input-wrap">
          <Search size={15} className="search-icon" />
          <input className="form-input" placeholder="Politika ara..." value={search} onChange={e => setSearch(e.target.value)} style={{ paddingLeft: 36 }} />
        </div>
        <select className="form-select" value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)} style={{ width: 140 }}>
          <option value="">Tüm Önemler</option>
          {SEVERITY_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <select className="form-select" value={filterStatus} onChange={e => setFilterStatus(e.target.value)} style={{ width: 130 }}>
          <option value="">Tüm Durumlar</option>
          <option value="active">Aktif</option>
          <option value="inactive">Pasif</option>
        </select>
        {(search || filterSeverity || filterStatus) && (
          <button className="btn btn-ghost btn-sm" onClick={() => { setSearch(''); setFilterSeverity(''); setFilterStatus('') }}>
            <X size={14} /> Temizle
          </button>
        )}
      </div>

      {/* Policies Grid */}
      {loading ? (
        <div className="grid-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="skeleton" style={{ height: 200, borderRadius: 14 }} />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon"><Shield size={28} /></div>
          <h3>Politika bulunamadı</h3>
          <p>Filtrelerinizi değiştirin veya yeni bir politika oluşturun.</p>
        </div>
      ) : (
        <div className="grid-3">
          {filtered.map(policy => (
            <div key={policy.id} style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: 14,
              overflow: 'hidden',
              transition: 'var(--transition-slow)',
              display: 'flex', flexDirection: 'column'
            }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--border-glow)'; e.currentTarget.style.transform = 'translateY(-2px)' }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-color)'; e.currentTarget.style.transform = 'translateY(0)' }}
            >
              {/* Severity accent bar */}
              <div style={{ height: 3, background: severityColor[policy.severity] }} />

              <div style={{ padding: '16px 18px', flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
                {/* Header */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4, lineHeight: 1.3 }}>
                      {policy.name}
                    </div>
                    <span style={{
                      display: 'inline-flex', alignItems: 'center', gap: 4,
                      padding: '2px 8px', borderRadius: 20, fontSize: '0.7rem', fontWeight: 600,
                      background: severityBg[policy.severity], color: severityColor[policy.severity],
                      border: `1px solid ${severityColor[policy.severity]}30`
                    }}>
                      {severityLabel[policy.severity]}
                    </span>
                  </div>
                  <div onClick={() => handleToggle(policy)} style={{ cursor: 'pointer', flexShrink: 0 }}>
                    {policy.is_active
                      ? <ToggleRight size={24} color="var(--success)" />
                      : <ToggleLeft size={24} color="var(--text-muted)" />
                    }
                  </div>
                </div>

                {/* Description */}
                {policy.description && (
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {policy.description}
                  </p>
                )}

                {/* Data types */}
                {policy.data_types?.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {policy.data_types.slice(0, 3).map(dt => (
                      <span key={dt} className="chip chip-primary">{dt}</span>
                    ))}
                    {policy.data_types.length > 3 && (
                      <span className="chip">+{policy.data_types.length - 3}</span>
                    )}
                  </div>
                )}

                {/* Sources */}
                {policy.sources?.length > 0 && (
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {policy.sources.map(src => (
                      <span key={src} style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }} title={sourceLabel[src]}>
                        {sourceIcon[src]} {sourceLabel[src]}
                      </span>
                    ))}
                  </div>
                )}

                {/* Footer */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 'auto', paddingTop: 8, borderTop: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '0.78rem' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Olay: </span>
                    <span style={{ color: 'var(--warning)', fontWeight: 600 }}>{policy.incident_count || 0}</span>
                    {' • '}
                    <span style={{ color: severityColor[policy.severity === 'block' ? 'critical' : 'medium'] }}>
                      {actionLabel[policy.action]}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button className="btn-icon" onClick={() => openEdit(policy)} title="Düzenle">
                      <Pencil size={14} />
                    </button>
                    <button className="btn-icon" onClick={() => setDeletePolicy(policy)} title="Sil"
                      style={{ color: 'var(--danger)', borderColor: 'rgba(239,68,68,0.2)' }}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CREATE/EDIT MODAL */}
      {modalOpen && (
        <div className="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) setModalOpen(false) }}>
          <div className="modal-content modal-lg">
            <div className="modal-header">
              <h3>{editPolicy ? 'Politikayı Düzenle' : 'Yeni Politika Oluştur'}</h3>
              <button className="modal-close" onClick={() => setModalOpen(false)}><X size={18} /></button>
            </div>
            <div className="modal-body">
              <PolicyForm form={form} setForm={setForm} />
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setModalOpen(false)}>İptal</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                {saving ? <><div className="loading-spinner" style={{ width: 16, height: 16 }} />Kaydediliyor...</> : <><Check size={16} />Kaydet</>}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DELETE CONFIRM */}
      {deletePolicy && (
        <div className="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) setDeletePolicy(null) }}>
          <div className="modal-content modal-sm">
            <div className="modal-header">
              <h3>Politikayı Sil</h3>
              <button className="modal-close" onClick={() => setDeletePolicy(null)}><X size={18} /></button>
            </div>
            <div className="modal-body">
              <div style={{ textAlign: 'center', padding: '8px 0' }}>
                <div style={{ width: 56, height: 56, background: 'rgba(239,68,68,0.12)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                  <Trash2 size={24} color="var(--danger)" />
                </div>
                <h3 style={{ marginBottom: 8 }}>Emin misiniz?</h3>
                <p style={{ fontSize: '0.875rem' }}>
                  <strong style={{ color: 'var(--text-primary)' }}>{deletePolicy.name}</strong> politikası kalıcı olarak silinecek. Bu işlem geri alınamaz.
                </p>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setDeletePolicy(null)}>İptal</button>
              <button className="btn btn-danger" onClick={handleDelete} disabled={deleting}>
                {deleting ? <><div className="loading-spinner" style={{ width: 16, height: 16 }} />Siliniyor...</> : <><Trash2 size={15} />Sil</>}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
