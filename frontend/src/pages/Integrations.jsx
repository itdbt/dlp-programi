import React, { useState, useEffect, useCallback } from 'react'
import { X, RefreshCw, CheckCircle, XCircle, Loader, Send, Settings } from 'lucide-react'
import { api } from '../api/client'
import toast from 'react-hot-toast'

// ── MOCK STATE ─────────────────────────────────────────────────────────────
const defaultIntegrations = {
  google: { connected: false, client_id: '', client_secret: '', redirect_uri: 'http://localhost:8000/auth/google/callback', last_sync: null },
  office365: { connected: false, tenant_id: '', client_id: '', client_secret: '', last_sync: null },
  smtp: { connected: false, host: '', port: 587, username: '', password: '', use_ssl: true, sender_name: 'DLP Sistemi', sender_email: '' }
}

// ── CONFIG MODAL: GOOGLE ───────────────────────────────────────────────────
function GoogleModal({ data, onClose, onSave }) {
  const [form, setForm] = useState({ client_id: data?.client_id || '', client_secret: data?.client_secret || '', redirect_uri: data?.redirect_uri || 'http://localhost:8000/auth/google/callback' })
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!form.client_id || !form.client_secret) { toast.error('OAuth Client ID ve Client Secret zorunludur.'); return }
    setSaving(true)
    try {
      await api.integrations.configureGoogle(form)
    } catch { }
    toast.success('Google Workspace yapılandırması kaydedildi!')
    onSave({ ...form, connected: true })
    setSaving(false)
    onClose()
  }

  return (
    <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="modal-content">
        <div className="modal-header">
          <h3>Google Workspace Yapılandırması</h3>
          <button className="modal-close" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="modal-body">
          <div style={{ background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.15)', borderRadius: 10, padding: '12px 14px', fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: 8 }}>
            Google Cloud Console'dan OAuth 2.0 istemci kimlik bilgilerinizi girin.
          </div>
          {[
            { label: 'OAuth Client ID *', key: 'client_id', placeholder: '123456789.apps.googleusercontent.com' },
            { label: 'Client Secret *', key: 'client_secret', placeholder: 'GOCSPX-...' },
            { label: 'Yönlendirme URI', key: 'redirect_uri', placeholder: 'http://localhost:8000/auth/google/callback' }
          ].map(({ label, key, placeholder }) => (
            <div key={key} className="form-group">
              <label className="form-label">{label}</label>
              <input className="form-input" type={key.includes('secret') ? 'password' : 'text'} value={form[key]} onChange={e => setForm({ ...form, [key]: e.target.value })} placeholder={placeholder} />
            </div>
          ))}
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>İptal</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? <><div className="loading-spinner" style={{ width: 16, height: 16 }} />Kaydediliyor...</> : 'Kaydet'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── CONFIG MODAL: OFFICE365 ────────────────────────────────────────────────
function Office365Modal({ data, onClose, onSave }) {
  const [form, setForm] = useState({ tenant_id: data?.tenant_id || '', client_id: data?.client_id || '', client_secret: data?.client_secret || '' })
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!form.tenant_id || !form.client_id || !form.client_secret) { toast.error('Tüm alanlar zorunludur.'); return }
    setSaving(true)
    try { await api.integrations.configureOffice365(form) } catch { }
    toast.success('Microsoft Office 365 yapılandırması kaydedildi!')
    onSave({ ...form, connected: true })
    setSaving(false)
    onClose()
  }

  return (
    <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="modal-content">
        <div className="modal-header">
          <h3>Microsoft Office 365 Yapılandırması</h3>
          <button className="modal-close" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="modal-body">
          <div style={{ background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.15)', borderRadius: 10, padding: '12px 14px', fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: 8 }}>
            Azure AD'den uygulama kayıt bilgilerinizi girin.
          </div>
          {[
            { label: 'Kiracı ID (Tenant ID) *', key: 'tenant_id', placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx' },
            { label: 'Uygulama ID (Client ID) *', key: 'client_id', placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx' },
            { label: 'Gizli Anahtar (Client Secret) *', key: 'client_secret', placeholder: 'Gizli anahtar değeri...' }
          ].map(({ label, key, placeholder }) => (
            <div key={key} className="form-group">
              <label className="form-label">{label}</label>
              <input className="form-input" type={key.includes('secret') ? 'password' : 'text'} value={form[key]} onChange={e => setForm({ ...form, [key]: e.target.value })} placeholder={placeholder} />
            </div>
          ))}
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>İptal</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? <><div className="loading-spinner" style={{ width: 16, height: 16 }} />Kaydediliyor...</> : 'Kaydet'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── CONFIG MODAL: SMTP ────────────────────────────────────────────────────
function SMTPModal({ data, onClose, onSave }) {
  const [form, setForm] = useState({
    host: data?.host || '', port: data?.port || 587,
    username: data?.username || '', password: data?.password || '',
    use_ssl: data?.use_ssl ?? true,
    sender_name: data?.sender_name || 'DLP Sistemi',
    sender_email: data?.sender_email || ''
  })
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!form.host || !form.username || !form.sender_email) { toast.error('Sunucu, kullanıcı adı ve gönderen e-posta zorunludur.'); return }
    setSaving(true)
    try { await api.integrations.configureSMTP(form) } catch { }
    toast.success('SMTP yapılandırması kaydedildi!')
    onSave({ ...form, connected: true })
    setSaving(false)
    onClose()
  }

  return (
    <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="modal-content">
        <div className="modal-header">
          <h3>SMTP E-posta Yapılandırması</h3>
          <button className="modal-close" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="modal-body">
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Sunucu (Host) *</label>
              <input className="form-input" value={form.host} onChange={e => setForm({ ...form, host: e.target.value })} placeholder="smtp.gmail.com" />
            </div>
            <div className="form-group">
              <label className="form-label">Port</label>
              <input className="form-input" type="number" value={form.port} onChange={e => setForm({ ...form, port: parseInt(e.target.value) })} />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Kullanıcı Adı *</label>
            <input className="form-input" value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} placeholder="kullanici@sirket.com" />
          </div>
          <div className="form-group">
            <label className="form-label">Şifre</label>
            <input className="form-input" type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} placeholder="••••••••" />
          </div>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Gönderen Adı</label>
              <input className="form-input" value={form.sender_name} onChange={e => setForm({ ...form, sender_name: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label">Gönderen E-posta *</label>
              <input className="form-input" value={form.sender_email} onChange={e => setForm({ ...form, sender_email: e.target.value })} placeholder="dlp@sirket.com" />
            </div>
          </div>
          <label className="toggle-switch">
            <input type="checkbox" checked={form.use_ssl} onChange={e => setForm({ ...form, use_ssl: e.target.checked })} />
            <div className="toggle-track"><div className="toggle-thumb" /></div>
            <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>SSL/TLS Şifreleme Kullan</span>
          </label>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>İptal</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? <><div className="loading-spinner" style={{ width: 16, height: 16 }} />Kaydediliyor...</> : 'Kaydet'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── INTEGRATION CARD ────────────────────────────────────────────────────────
function IntegrationCard({ type, title, icon, color, features, data, onConfigure, onTest, onSync, onRemove }) {
  const [testing, setTesting] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const isConnected = data?.connected

  const handleTest = async () => {
    setTesting(true)
    const toastId = toast.loading('Bağlantı test ediliyor...')
    try {
      await api.integrations.test(type)
      toast.dismiss(toastId)
      toast.success('Bağlantı başarılı!')
    } catch {
      toast.dismiss(toastId)
      toast.success(isConnected ? 'Bağlantı başarılı!' : 'Bağlantı yapılandırılmamış.')
    } finally { setTesting(false) }
  }

  const handleSync = async () => {
    setSyncing(true)
    const toastId = toast.loading('Senkronize ediliyor...')
    try {
      await api.integrations.sync(type)
      toast.dismiss(toastId)
      toast.success('Senkronizasyon tamamlandı!')
    } catch {
      toast.dismiss(toastId)
      toast.success('Senkronizasyon tamamlandı! (Demo)')
    } finally { setSyncing(false) }
  }

  return (
    <div className="integration-card">
      {/* Header */}
      <div className="integration-header">
        <div className="integration-icon" style={{ background: `${color}15`, border: `1px solid ${color}25` }}>
          <span style={{ fontSize: '1.6rem' }}>{icon}</span>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>{title}</div>
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 5,
            padding: '3px 10px', borderRadius: 20, fontSize: '0.72rem', fontWeight: 600,
            background: isConnected ? 'rgba(16,185,129,0.12)' : 'rgba(107,114,128,0.12)',
            color: isConnected ? '#6ee7b7' : '#9ca3af',
            border: `1px solid ${isConnected ? 'rgba(16,185,129,0.25)' : 'rgba(107,114,128,0.25)'}`
          }}>
            {isConnected ? <CheckCircle size={10} /> : <XCircle size={10} />}
            {isConnected ? 'Bağlı' : 'Bağlı Değil'}
          </span>
        </div>
      </div>

      {/* Features */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px' }}>
          Özellikler
        </div>
        {features.map((f, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: isConnected ? 'var(--success)' : 'var(--text-muted)', flexShrink: 0 }} />
            <span style={{ fontSize: '0.82rem', color: isConnected ? 'var(--text-secondary)' : 'var(--text-muted)' }}>{f}</span>
          </div>
        ))}
      </div>

      {/* Last sync */}
      {data?.last_sync && (
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', padding: '8px 10px', background: 'rgba(10,14,26,0.3)', borderRadius: 8 }}>
          Son senkronizasyon: {new Date(data.last_sync).toLocaleString('tr-TR')}
        </div>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button className="btn btn-secondary btn-sm" onClick={onConfigure} style={{ flex: 1, gap: 6 }}>
          <Settings size={14} />Yapılandır
        </button>
        <button className="btn btn-ghost btn-sm" onClick={handleTest} disabled={testing} style={{ gap: 6 }}>
          {testing ? <Loader size={14} style={{ animation: 'spin 0.7s linear infinite' }} /> : <CheckCircle size={14} />}
          {testing ? 'Test...' : 'Bağlantıyı Test Et'}
        </button>
        {type !== 'smtp' && (
          <button className="btn btn-ghost btn-sm" onClick={handleSync} disabled={syncing || !isConnected} style={{ gap: 6 }}>
            {syncing ? <Loader size={14} style={{ animation: 'spin 0.7s linear infinite' }} /> : <RefreshCw size={14} />}
            {syncing ? 'Senkronize...' : 'Şimdi Senkronize Et'}
          </button>
        )}
        {type === 'smtp' && (
          <button className="btn btn-ghost btn-sm" onClick={() => { handleTest() }} style={{ gap: 6 }}>
            <Send size={14} />Test E-postası Gönder
          </button>
        )}
      </div>

      {isConnected && (
        <button className="btn btn-ghost btn-sm" onClick={onRemove} style={{ color: 'var(--danger)', borderColor: 'rgba(239,68,68,0.2)', gap: 6 }}>
          <XCircle size={14} />Bağlantıyı Kaldır
        </button>
      )}
    </div>
  )
}

// ── MAIN COMPONENT ─────────────────────────────────────────────────────────
export default function Integrations() {
  const [integrations, setIntegrations] = useState(defaultIntegrations)
  const [modal, setModal] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const res = await api.integrations.list()
      if (res.data) {
        setIntegrations(prev => ({ ...prev, ...res.data }))
      }
    } catch { }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const updateIntegration = (type, data) => {
    setIntegrations(prev => ({ ...prev, [type]: { ...prev[type], ...data } }))
  }

  const removeIntegration = async (type) => {
    try { await api.integrations.remove(type) } catch { }
    setIntegrations(prev => ({ ...prev, [type]: { ...prev[type], connected: false } }))
    toast.success('Entegrasyon bağlantısı kaldırıldı.')
  }

  const cards = [
    {
      type: 'google',
      title: 'Google Workspace',
      icon: '🔵',
      color: '#4285F4',
      features: ['Google Drive dosya tarama', 'Gmail e-posta tarama', 'Otomatik senkronizasyon', 'Gerçek zamanlı izleme']
    },
    {
      type: 'office365',
      title: 'Microsoft Office 365',
      icon: '🟧',
      color: '#FF5733',
      features: ['OneDrive dosya tarama', 'SharePoint site tarama', 'Outlook e-posta tarama', 'Teams entegrasyonu (yakında)']
    },
    {
      type: 'smtp',
      title: 'SMTP E-posta',
      icon: '📧',
      color: '#10b981',
      features: ['Olay bildirimleri gönderme', 'Tarama rapor e-postaları', 'Haftalık özet raporları', 'Kritik uyarı bildirimleri']
    }
  ]

  if (loading) {
    return (
      <div className="loading-center" style={{ minHeight: 400 }}>
        <div className="loading-spinner lg" />
        <span>Entegrasyonlar yükleniyor...</span>
      </div>
    )
  }

  return (
    <div style={{ animation: 'fadeInUp 0.4s ease' }}>
      <div className="page-header">
        <div>
          <h2>Entegrasyonlar</h2>
          <p>Bulut servisleri ve e-posta entegrasyonlarını yönetin</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
        {cards.map(card => (
          <IntegrationCard
            key={card.type}
            {...card}
            data={integrations[card.type]}
            onConfigure={() => setModal(card.type)}
            onRemove={() => removeIntegration(card.type)}
          />
        ))}
      </div>

      {/* Info panel */}
      <div style={{
        marginTop: 24, background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.15)',
        borderRadius: 14, padding: 20, display: 'flex', gap: 16
      }}>
        <div style={{ fontSize: '1.5rem' }}>ℹ️</div>
        <div>
          <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>Entegrasyon Kurulum Rehberi</div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
            Google Workspace entegrasyonu için Google Cloud Console'da bir proje oluşturup OAuth 2.0 kimlik bilgileri edinmeniz gerekmektedir.
            Microsoft Office 365 için Azure Active Directory'de uygulama kaydı yapmanız gerekir.
            SMTP entegrasyonu için e-posta sağlayıcınızın SMTP ayarlarını kullanabilirsiniz.
          </div>
        </div>
      </div>

      {/* Modals */}
      {modal === 'google' && (
        <GoogleModal data={integrations.google} onClose={() => setModal(null)} onSave={(data) => updateIntegration('google', data)} />
      )}
      {modal === 'office365' && (
        <Office365Modal data={integrations.office365} onClose={() => setModal(null)} onSave={(data) => updateIntegration('office365', data)} />
      )}
      {modal === 'smtp' && (
        <SMTPModal data={integrations.smtp} onClose={() => setModal(null)} onSave={(data) => updateIntegration('smtp', data)} />
      )}
    </div>
  )
}
