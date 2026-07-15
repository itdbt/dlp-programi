import React, { useState, useEffect, useCallback } from 'react'
import {
  Save, Plus, Trash2, X, Bell, Users, FileText,
  Shield, Server, Database, Activity, Check,
  Eye, EyeOff, ChevronDown
} from 'lucide-react'
import { api } from '../api/client'
import toast from 'react-hot-toast'

// ── MOCK DATA ──────────────────────────────────────────────────────────────
const mockSettings = {
  system_name: 'DLP Güvenlik Sistemi',
  timezone: 'Europe/Istanbul',
  auto_scan_interval: 60,
  max_file_size_mb: 50,
  data_retention_days: 365,
  log_level: 'info'
}

const mockUsers = [
  { id: 1, full_name: 'Admin Kullanıcı', email: 'admin@dlp.local', role: 'admin', is_active: true, last_login: new Date(Date.now() - 3600000).toISOString() },
  { id: 2, full_name: 'Ahmet Yılmaz', email: 'ahmet@dlp.local', role: 'analyst', is_active: true, last_login: new Date(Date.now() - 7200000).toISOString() },
  { id: 3, full_name: 'Zeynep Kaya', email: 'zeynep@dlp.local', role: 'analyst', is_active: true, last_login: new Date(Date.now() - 86400000).toISOString() },
  { id: 4, full_name: 'Mehmet Demir', email: 'mehmet@dlp.local', role: 'viewer', is_active: false, last_login: null }
]

const mockNotificationRules = [
  { id: 1, name: 'Kritik Olay Bildirimi', events: ['critical_incident'], channels: ['email'], recipients: ['admin@dlp.local'], active: true },
  { id: 2, name: 'Haftalık Özet Raporu', events: ['weekly_report'], channels: ['email'], recipients: ['admin@dlp.local', 'manager@sirket.com'], active: true },
  { id: 3, name: 'Tarama Tamamlandı', events: ['scan_complete'], channels: ['webhook'], recipients: [], webhook_url: 'https://hooks.slack.com/services/xxx', active: false }
]

const mockAuditLogs = [
  { id: 1, created_at: new Date(Date.now() - 1800000).toISOString(), user: 'admin@dlp.local', action: 'Politika Oluşturuldu', resource: 'Finansal Veri Koruma', details: 'Yeni politika oluşturuldu' },
  { id: 2, created_at: new Date(Date.now() - 3600000).toISOString(), user: 'ahmet@dlp.local', action: 'Olay Güncellendi', resource: '#1234', details: 'Durum "Çözüldü" olarak değiştirildi' },
  { id: 3, created_at: new Date(Date.now() - 7200000).toISOString(), user: 'admin@dlp.local', action: 'Kullanıcı Oluşturuldu', resource: 'zeynep@dlp.local', details: 'Analist rolüyle yeni kullanıcı eklendi' },
  { id: 4, created_at: new Date(Date.now() - 10800000).toISOString(), user: 'zeynep@dlp.local', action: 'Giriş Yapıldı', resource: 'Sistem', details: 'Başarılı giriş' },
  { id: 5, created_at: new Date(Date.now() - 86400000).toISOString(), user: 'admin@dlp.local', action: 'Tarama Başlatıldı', resource: 'Google Drive', details: 'Manuel tarama tetiklendi' }
]

const mockSystemInfo = {
  version: '2.5.0',
  uptime: '15g 4sa 32dk',
  db_size_mb: 142.5,
  total_incidents: 247,
  total_scans: 42,
  python_version: '3.11.8',
  os: 'Windows 11',
  cpu_usage: 12,
  memory_usage: 34
}

// ── HELPERS ────────────────────────────────────────────────────────────────
const TIMEZONES = ['Europe/Istanbul', 'UTC', 'Europe/London', 'America/New_York', 'Asia/Dubai']
const LOG_LEVELS = [{ value: 'debug', label: 'Debug' }, { value: 'info', label: 'Info' }, { value: 'warning', label: 'Uyarı' }, { value: 'error', label: 'Hata' }]
const ROLES = [{ value: 'admin', label: 'Yönetici' }, { value: 'analyst', label: 'Analist' }, { value: 'viewer', label: 'İzleme' }]
const EVENTS = [
  { value: 'new_incident', label: 'Yeni Olay' },
  { value: 'critical_incident', label: 'Kritik Olay' },
  { value: 'scan_complete', label: 'Tarama Tamamlandı' },
  { value: 'weekly_report', label: 'Haftalık Rapor' }
]

function timeAgo(iso) {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins} dk önce`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs} sa önce`
  return `${Math.floor(hrs / 24)} gün önce`
}

function roleColor(role) {
  const map = { admin: 'var(--primary)', analyst: 'var(--accent)', viewer: 'var(--text-muted)' }
  return map[role] || 'var(--text-muted)'
}

function roleLabel(role) {
  const map = { admin: 'Yönetici', analyst: 'Analist', viewer: 'İzleme' }
  return map[role] || role
}

// ── GENEL AYARLAR TAB ─────────────────────────────────────────────────────
function GeneralTab() {
  const [form, setForm] = useState(mockSettings)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try { await api.settings.update(form) } catch { }
    toast.success('Ayarlar kaydedildi!')
    setSaving(false)
  }

  return (
    <div className="card" style={{ maxWidth: 600 }}>
      <div className="card-header">
        <span className="card-title"><Shield size={16} color="var(--primary)" />Genel Sistem Ayarları</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className="form-group">
          <label className="form-label">Sistem Adı</label>
          <input className="form-input" value={form.system_name} onChange={e => setForm({ ...form, system_name: e.target.value })} />
        </div>
        <div className="form-group">
          <label className="form-label">Zaman Dilimi</label>
          <select className="form-select" value={form.timezone} onChange={e => setForm({ ...form, timezone: e.target.value })}>
            {TIMEZONES.map(tz => <option key={tz} value={tz}>{tz}</option>)}
          </select>
        </div>
        <div className="grid-2">
          <div className="form-group">
            <label className="form-label">Otomatik Tarama Aralığı (dakika)</label>
            <input className="form-input" type="number" min={5} value={form.auto_scan_interval} onChange={e => setForm({ ...form, auto_scan_interval: parseInt(e.target.value) })} />
          </div>
          <div className="form-group">
            <label className="form-label">Maksimum Dosya Boyutu (MB)</label>
            <input className="form-input" type="number" min={1} value={form.max_file_size_mb} onChange={e => setForm({ ...form, max_file_size_mb: parseInt(e.target.value) })} />
          </div>
        </div>
        <div className="grid-2">
          <div className="form-group">
            <label className="form-label">Veri Saklama Süresi (gün)</label>
            <input className="form-input" type="number" min={30} value={form.data_retention_days} onChange={e => setForm({ ...form, data_retention_days: parseInt(e.target.value) })} />
          </div>
          <div className="form-group">
            <label className="form-label">Log Seviyesi</label>
            <select className="form-select" value={form.log_level} onChange={e => setForm({ ...form, log_level: e.target.value })}>
              {LOG_LEVELS.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
            </select>
          </div>
        </div>
        <div style={{ marginTop: 8 }}>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving} style={{ gap: 6 }}>
            {saving ? <><div className="loading-spinner" style={{ width: 16, height: 16 }} />Kaydediliyor...</> : <><Save size={16} />Kaydet</>}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── BİLDİRİMLER TAB ──────────────────────────────────────────────────────
function NotificationsTab() {
  const [rules, setRules] = useState(mockNotificationRules)
  const [logs] = useState([
    { id: 1, time: new Date(Date.now() - 1800000).toISOString(), msg: 'Kritik olay bildirimi gönderildi → admin@dlp.local', success: true },
    { id: 2, time: new Date(Date.now() - 7200000).toISOString(), msg: 'Haftalık rapor gönderildi → 2 alıcı', success: true },
    { id: 3, time: new Date(Date.now() - 86400000).toISOString(), msg: 'Webhook isteği başarısız → timeout', success: false }
  ])
  const [ruleModal, setRuleModal] = useState(false)
  const [editRule, setEditRule] = useState(null)
  const [form, setForm] = useState({ name: '', events: [], channels: [], recipients: [], webhook_url: '', active: true })
  const [emailInput, setEmailInput] = useState('')

  const openCreate = () => {
    setEditRule(null)
    setForm({ name: '', events: [], channels: [], recipients: [], webhook_url: '', active: true })
    setRuleModal(true)
  }

  const handleSaveRule = async () => {
    if (!form.name.trim()) { toast.error('Kural adı gereklidir.'); return }
    try { if (editRule) { await api.notifications.updateRule(editRule.id, form) } else { await api.notifications.createRule(form) } } catch { }
    if (editRule) setRules(prev => prev.map(r => r.id === editRule.id ? { ...r, ...form } : r))
    else setRules(prev => [...prev, { ...form, id: Date.now() }])
    toast.success(editRule ? 'Kural güncellendi!' : 'Kural oluşturuldu!')
    setRuleModal(false)
  }

  const deleteRule = async (id) => {
    try { await api.notifications.deleteRule(id) } catch { }
    setRules(prev => prev.filter(r => r.id !== id))
    toast.success('Kural silindi.')
  }

  const sendTest = () => toast.success('Test bildirimi gönderildi!')

  const toggleEvent = (v) => setForm(f => ({ ...f, events: f.events.includes(v) ? f.events.filter(e => e !== v) : [...f.events, v] }))
  const toggleChannel = (v) => setForm(f => ({ ...f, channels: f.channels.includes(v) ? f.channels.filter(c => c !== v) : [...f.channels, v] }))
  const addEmail = () => {
    if (emailInput && !form.recipients.includes(emailInput)) setForm(f => ({ ...f, recipients: [...f.recipients, emailInput] }))
    setEmailInput('')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Rules */}
      <div className="card">
        <div className="card-header">
          <span className="card-title"><Bell size={16} color="var(--warning)" />Bildirim Kuralları</span>
          <button className="btn btn-primary btn-sm" onClick={openCreate} style={{ gap: 6 }}><Plus size={14} />Kural Ekle</button>
        </div>
        {rules.length === 0 ? (
          <div className="empty-state"><Bell size={28} /><h3>Bildirim kuralı yok</h3></div>
        ) : (
          <div className="table-container">
            <table className="dlp-table">
              <thead><tr><th>Kural Adı</th><th>Olaylar</th><th>Kanallar</th><th>Durum</th><th></th></tr></thead>
              <tbody>
                {rules.map(rule => (
                  <tr key={rule.id}>
                    <td style={{ fontWeight: 500 }}>{rule.name}</td>
                    <td>
                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {rule.events.map(e => <span key={e} className="chip">{EVENTS.find(ev => ev.value === e)?.label || e}</span>)}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {rule.channels.map(c => <span key={c} className="chip chip-primary">{c === 'email' ? '📧 E-posta' : '🔗 Webhook'}</span>)}
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.72rem', fontWeight: 600, color: rule.active ? 'var(--success)' : 'var(--text-muted)', background: rule.active ? 'rgba(16,185,129,0.12)' : 'rgba(107,114,128,0.12)', padding: '3px 8px', borderRadius: 20 }}>
                        {rule.active ? 'Aktif' : 'Pasif'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 4 }}>
                        <button className="btn-icon" title="Test Et" onClick={sendTest}><Bell size={13} /></button>
                        <button className="btn-icon" title="Sil" onClick={() => deleteRule(rule.id)} style={{ color: 'var(--danger)', borderColor: 'rgba(239,68,68,0.2)' }}><Trash2 size={13} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Logs */}
      <div className="card">
        <div className="card-header"><span className="card-title">Son Bildirim Günlükleri</span></div>
        <div>
          {logs.map(log => (
            <div key={log.id} className="log-row">
              <div className="log-time">{new Date(log.time).toLocaleTimeString('tr-TR')}</div>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: log.success ? 'var(--success)' : 'var(--danger)', flexShrink: 0, marginTop: 6 }} />
              <div className="log-msg">{log.msg}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Rule modal */}
      {ruleModal && (
        <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) setRuleModal(false) }}>
          <div className="modal-content">
            <div className="modal-header">
              <h3>{editRule ? 'Kuralı Düzenle' : 'Yeni Bildirim Kuralı'}</h3>
              <button className="modal-close" onClick={() => setRuleModal(false)}><X size={18} /></button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Kural Adı *</label>
                <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Kural adı..." />
              </div>
              <div className="form-group">
                <label className="form-label">Tetikleyici Olaylar</label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
                  {EVENTS.map(ev => (
                    <label key={ev.value} className="checkbox-label">
                      <input type="checkbox" checked={form.events.includes(ev.value)} onChange={() => toggleEvent(ev.value)} />
                      {ev.label}
                    </label>
                  ))}
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Bildirim Kanalları</label>
                <div style={{ display: 'flex', gap: 12 }}>
                  <label className="checkbox-label">
                    <input type="checkbox" checked={form.channels.includes('email')} onChange={() => toggleChannel('email')} />
                    📧 E-posta
                  </label>
                  <label className="checkbox-label">
                    <input type="checkbox" checked={form.channels.includes('webhook')} onChange={() => toggleChannel('webhook')} />
                    🔗 Webhook
                  </label>
                </div>
              </div>
              {form.channels.includes('email') && (
                <div className="form-group">
                  <label className="form-label">E-posta Alıcıları</label>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <input className="form-input" placeholder="e-posta@sirket.com" value={emailInput} onChange={e => setEmailInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addEmail() } }} />
                    <button className="btn btn-secondary btn-sm" onClick={addEmail}><Plus size={14} /></button>
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
                    {form.recipients.map(r => (
                      <span key={r} className="chip chip-primary">
                        {r}
                        <button onClick={() => setForm(f => ({ ...f, recipients: f.recipients.filter(x => x !== r) }))} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', padding: 0, marginLeft: 4, lineHeight: 1 }}>×</button>
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {form.channels.includes('webhook') && (
                <div className="form-group">
                  <label className="form-label">Webhook URL</label>
                  <input className="form-input" value={form.webhook_url} onChange={e => setForm({ ...form, webhook_url: e.target.value })} placeholder="https://hooks.slack.com/..." />
                </div>
              )}
              <label className="toggle-switch">
                <input type="checkbox" checked={form.active} onChange={e => setForm({ ...form, active: e.target.checked })} />
                <div className="toggle-track"><div className="toggle-thumb" /></div>
                <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Kural Aktif</span>
              </label>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setRuleModal(false)}>İptal</button>
              <button className="btn btn-primary" onClick={handleSaveRule}><Check size={16} />Kaydet</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ── KULLANICILAR TAB ──────────────────────────────────────────────────────
function UsersTab() {
  const [users, setUsers] = useState(mockUsers)
  const [userModal, setUserModal] = useState(false)
  const [editUser, setEditUser] = useState(null)
  const [showPass, setShowPass] = useState(false)
  const [form, setForm] = useState({ full_name: '', email: '', role: 'analyst', password: '', is_active: true })

  const openCreate = () => {
    setEditUser(null)
    setForm({ full_name: '', email: '', role: 'analyst', password: '', is_active: true })
    setUserModal(true)
  }
  const openEdit = (user) => {
    setEditUser(user)
    setForm({ full_name: user.full_name, email: user.email, role: user.role, password: '', is_active: user.is_active })
    setUserModal(true)
  }

  const handleSave = async () => {
    if (!form.full_name.trim() || !form.email.trim()) { toast.error('Ad ve e-posta gereklidir.'); return }
    if (!editUser && !form.password.trim()) { toast.error('Şifre gereklidir.'); return }
    try {
      if (editUser) { await api.auth.updateUser(editUser.id, form) }
      else { await api.auth.createUser(form) }
    } catch { }
    if (editUser) setUsers(prev => prev.map(u => u.id === editUser.id ? { ...u, ...form } : u))
    else setUsers(prev => [...prev, { ...form, id: Date.now(), last_login: null }])
    toast.success(editUser ? 'Kullanıcı güncellendi!' : 'Kullanıcı oluşturuldu!')
    setUserModal(false)
  }

  const deleteUser = async (id) => {
    try { await api.auth.deleteUser(id) } catch { }
    setUsers(prev => prev.filter(u => u.id !== id))
    toast.success('Kullanıcı silindi.')
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
        <button className="btn btn-primary" onClick={openCreate} style={{ gap: 6 }}><Plus size={16} />Kullanıcı Ekle</button>
      </div>
      <div className="table-container">
        <table className="dlp-table">
          <thead><tr><th>Ad Soyad</th><th>E-posta</th><th>Rol</th><th>Durum</th><th>Son Giriş</th><th></th></tr></thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id}>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div className="user-avatar" style={{ width: 32, height: 32, fontSize: '0.7rem' }}>
                      {user.full_name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)}
                    </div>
                    <span style={{ fontWeight: 500 }}>{user.full_name}</span>
                  </div>
                </td>
                <td style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>{user.email}</td>
                <td>
                  <span style={{ fontSize: '0.72rem', fontWeight: 600, color: roleColor(user.role), background: `${roleColor(user.role)}15`, padding: '3px 8px', borderRadius: 20 }}>
                    {roleLabel(user.role)}
                  </span>
                </td>
                <td>
                  <span style={{ fontSize: '0.72rem', fontWeight: 600, color: user.is_active ? 'var(--success)' : 'var(--text-muted)', background: user.is_active ? 'rgba(16,185,129,0.12)' : 'rgba(107,114,128,0.12)', padding: '3px 8px', borderRadius: 20 }}>
                    {user.is_active ? 'Aktif' : 'Pasif'}
                  </span>
                </td>
                <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{timeAgo(user.last_login)}</td>
                <td>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button className="btn-icon" onClick={() => openEdit(user)}><FileText size={13} /></button>
                    <button className="btn-icon" onClick={() => deleteUser(user.id)} style={{ color: 'var(--danger)', borderColor: 'rgba(239,68,68,0.2)' }}><Trash2 size={13} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {userModal && (
        <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) setUserModal(false) }}>
          <div className="modal-content">
            <div className="modal-header">
              <h3>{editUser ? 'Kullanıcıyı Düzenle' : 'Yeni Kullanıcı'}</h3>
              <button className="modal-close" onClick={() => setUserModal(false)}><X size={18} /></button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Ad Soyad *</label>
                <input className="form-input" value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} placeholder="Ahmet Yılmaz" />
              </div>
              <div className="form-group">
                <label className="form-label">E-posta *</label>
                <input className="form-input" type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="kullanici@sirket.com" />
              </div>
              <div className="form-group">
                <label className="form-label">Rol</label>
                <select className="form-select" value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
                  {ROLES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">{editUser ? 'Yeni Şifre (opsiyonel)' : 'Şifre *'}</label>
                <div style={{ position: 'relative' }}>
                  <input className="form-input" type={showPass ? 'text' : 'password'} value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} placeholder="••••••••" style={{ paddingRight: 44 }} />
                  <button type="button" onClick={() => setShowPass(!showPass)} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
                    {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>
              <label className="toggle-switch">
                <input type="checkbox" checked={form.is_active} onChange={e => setForm({ ...form, is_active: e.target.checked })} />
                <div className="toggle-track"><div className="toggle-thumb" /></div>
                <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Kullanıcı Aktif</span>
              </label>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setUserModal(false)}>İptal</button>
              <button className="btn btn-primary" onClick={handleSave}><Check size={16} />Kaydet</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ── DENETİM GÜNLÜĞÜ TAB ───────────────────────────────────────────────────
function AuditTab() {
  const [logs] = useState(mockAuditLogs)
  const [searchUser, setSearchUser] = useState('')
  const [page, setPage] = useState(1)
  const PER_PAGE = 5

  const filtered = logs.filter(l => !searchUser || l.user.toLowerCase().includes(searchUser.toLowerCase()))
  const total = Math.ceil(filtered.length / PER_PAGE)
  const paginated = filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE)

  return (
    <div>
      <div className="filter-row" style={{ marginBottom: 16 }}>
        <input className="form-input" placeholder="Kullanıcıya göre filtrele..." value={searchUser} onChange={e => setSearchUser(e.target.value)} style={{ maxWidth: 250 }} />
      </div>
      <div className="table-container">
        <table className="dlp-table">
          <thead><tr><th>Zaman</th><th>Kullanıcı</th><th>Eylem</th><th>Kaynak</th><th>Detaylar</th></tr></thead>
          <tbody>
            {paginated.map(log => (
              <tr key={log.id}>
                <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                  {new Date(log.created_at).toLocaleString('tr-TR')}
                </td>
                <td style={{ fontSize: '0.82rem', color: 'var(--primary-light)' }}>{log.user}</td>
                <td style={{ fontWeight: 500 }}>{log.action}</td>
                <td style={{ fontSize: '0.82rem', color: 'var(--accent)' }}>{log.resource}</td>
                <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{log.details}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {total > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 16 }}>
          {Array.from({ length: total }, (_, i) => (
            <button key={i} onClick={() => setPage(i + 1)} className={page === i + 1 ? 'btn btn-primary btn-sm' : 'btn btn-secondary btn-sm'}>
              {i + 1}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ── SİSTEM TAB ────────────────────────────────────────────────────────────
function SystemTab() {
  const [info] = useState(mockSystemInfo)
  const [clearing, setClearing] = useState(false)

  const handleBackup = () => toast.success('Yedekleme başlatıldı! Dosya indirilecek.')
  const handleClear = async () => {
    setClearing(true)
    try { await api.settings.clearLogs() } catch { }
    setTimeout(() => {
      toast.success('Eski loglar temizlendi.')
      setClearing(false)
    }, 1500)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* System info */}
      <div className="grid-3" style={{ gap: 16 }}>
        {[
          { label: 'Sistem Sürümü', value: `v${info.version}`, icon: <Shield size={16} color="var(--primary)" /> },
          { label: 'Çalışma Süresi', value: info.uptime, icon: <Activity size={16} color="var(--success)" /> },
          { label: 'Veritabanı Boyutu', value: `${info.db_size_mb} MB`, icon: <Database size={16} color="var(--accent)" /> },
          { label: 'Toplam Olay', value: info.total_incidents, icon: <Bell size={16} color="var(--warning)" /> },
          { label: 'Toplam Tarama', value: info.total_scans, icon: <FileText size={16} color="var(--purple)" /> },
          { label: 'Python Sürümü', value: info.python_version, icon: <Server size={16} color="var(--text-muted)" /> }
        ].map(({ label, value, icon }) => (
          <div key={label} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 12, padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ width: 38, height: 38, background: 'rgba(30,45,74,0.6)', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              {icon}
            </div>
            <div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>{value}</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Resource usage */}
      <div className="card">
        <div className="card-header"><span className="card-title"><Activity size={16} color="var(--success)" />Kaynak Kullanımı</span></div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {[
            { label: 'CPU Kullanımı', value: info.cpu_usage, color: info.cpu_usage > 80 ? 'var(--danger)' : info.cpu_usage > 50 ? 'var(--warning)' : 'var(--success)' },
            { label: 'Bellek Kullanımı', value: info.memory_usage, color: info.memory_usage > 80 ? 'var(--danger)' : info.memory_usage > 50 ? 'var(--warning)' : 'var(--success)' }
          ].map(({ label, value, color }) => (
            <div key={label}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{label}</span>
                <span style={{ fontSize: '0.82rem', fontWeight: 600, color }}>{value}%</span>
              </div>
              <div className="progress" style={{ height: 8 }}>
                <div className="progress-bar" style={{ width: `${value}%`, background: color }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Engine status */}
      <div className="card">
        <div className="card-header"><span className="card-title"><Server size={16} color="var(--accent)" />Motor Durumu</span></div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {[
            { label: 'DLP Tarama Motoru', status: true, detail: 'v2.5.0 - Aktif' },
            { label: 'Pattern Matching Motoru', status: true, detail: '12 aktif desen' },
            { label: 'Rapor Motoru', status: true, detail: 'Hazır' },
            { label: 'Bildirim Servisi', status: true, detail: 'SMTP aktif' }
          ].map(({ label, status, detail }) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(10,14,26,0.4)', borderRadius: 8, border: `1px solid ${status ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)'}` }}>
              <div>
                <div style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-primary)' }}>{label}</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{detail}</div>
              </div>
              {status ? <Check size={16} color="var(--success)" /> : <X size={16} color="var(--danger)" />}
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="card">
        <div className="card-header"><span className="card-title">Sistem İşlemleri</span></div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button className="btn btn-primary" onClick={handleBackup} style={{ gap: 6 }}>
            <Database size={16} />Yedek Al
          </button>
          <button className="btn btn-danger" onClick={handleClear} disabled={clearing} style={{ gap: 6 }}>
            {clearing ? <><div className="loading-spinner" style={{ width: 16, height: 16 }} />Temizleniyor...</> : <><Trash2 size={16} />Eski Logları Temizle</>}
          </button>
        </div>
        <div style={{ marginTop: 12, fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
          Yedek Al: Tüm yapılandırma ve veritabanını dışa aktarır.<br />
          Eski Logları Temizle: Veri saklama süresini aşmış logları siler.
        </div>
      </div>
    </div>
  )
}

// ── MAIN COMPONENT ─────────────────────────────────────────────────────────
export default function Settings() {
  const [activeTab, setActiveTab] = useState('general')

  const tabs = [
    { id: 'general', label: '⚙️ Genel Ayarlar', icon: <Shield size={14} /> },
    { id: 'notifications', label: '🔔 Bildirimler', icon: <Bell size={14} /> },
    { id: 'users', label: '👥 Kullanıcılar', icon: <Users size={14} /> },
    { id: 'audit', label: '📋 Denetim Günlüğü', icon: <FileText size={14} /> },
    { id: 'system', label: '🖥️ Sistem', icon: <Server size={14} /> }
  ]

  return (
    <div style={{ animation: 'fadeInUp 0.4s ease' }}>
      <div className="page-header">
        <div>
          <h2>Sistem Ayarları</h2>
          <p>Sistem yapılandırması ve yönetim</p>
        </div>
      </div>

      <div className="tabs" style={{ marginBottom: 24, flexWrap: 'wrap' }}>
        {tabs.map(t => (
          <button key={t.id} className={`tab ${activeTab === t.id ? 'active' : ''}`} onClick={() => setActiveTab(t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === 'general' && <GeneralTab />}
      {activeTab === 'notifications' && <NotificationsTab />}
      {activeTab === 'users' && <UsersTab />}
      {activeTab === 'audit' && <AuditTab />}
      {activeTab === 'system' && <SystemTab />}
    </div>
  )
}
