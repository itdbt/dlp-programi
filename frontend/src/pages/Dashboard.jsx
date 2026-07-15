import React, { useState, useEffect, useCallback } from 'react'
import {
  AlertCircle, ShieldAlert, Clock, Search, Activity,
  Shield, TrendingUp, TrendingDown, Minus,
  CheckCircle, XCircle, Database, RefreshCw
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, BarChart, Bar
} from 'recharts'
import { api } from '../api/client'
import { format, parseISO } from 'date-fns'
import { tr } from 'date-fns/locale'

// ── MOCK DATA (used when API is not available) ─────────────────────────────
const mockStats = {
  total_incidents: 247,
  critical_incidents: 18,
  open_incidents: 43,
  today_scans: 12,
  avg_risk_score: 62.4,
  active_policies: 9,
  trends: { incidents: 12, critical: -2, open: 5, scans: 3, risk: 4, policies: 0 }
}

const mockTrend = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 86400000).toISOString().split('T')[0],
  count: Math.floor(Math.random() * 15) + 2
}))

const mockSeverity = [
  { name: 'Kritik', value: 18, color: '#dc2626' },
  { name: 'Yüksek', value: 56, color: '#f97316' },
  { name: 'Orta', value: 98, color: '#f59e0b' },
  { name: 'Düşük', value: 75, color: '#10b981' }
]

const mockDataTypes = [
  { name: 'TC Kimlik No', count: 89 },
  { name: 'Kredi Kartı', count: 67 },
  { name: 'IBAN', count: 54 },
  { name: 'E-posta', count: 43 },
  { name: 'Telefon', count: 38 },
  { name: 'API Anahtarı', count: 29 },
  { name: 'Şifre/Hash', count: 21 }
]

const mockIncidents = [
  { id: 1, title: 'Kredi kartı verisi tespit edildi', severity: 'critical', status: 'open', policy_name: 'Finansal Veri Koruma', created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: 2, title: 'TC kimlik numarası sızdırıldı', severity: 'high', status: 'investigating', policy_name: 'Kişisel Veri Koruma', created_at: new Date(Date.now() - 7200000).toISOString() },
  { id: 3, title: 'IBAN bilgisi tespit edildi', severity: 'medium', status: 'open', policy_name: 'Banka Hesap Güvenliği', created_at: new Date(Date.now() - 14400000).toISOString() },
  { id: 4, title: 'API anahtarı açık bırakıldı', severity: 'critical', status: 'open', policy_name: 'Kod Güvenliği', created_at: new Date(Date.now() - 18000000).toISOString() },
  { id: 5, title: 'Toplu e-posta adresi paylaşıldı', severity: 'low', status: 'resolved', policy_name: 'İletişim Verisi', created_at: new Date(Date.now() - 86400000).toISOString() }
]

const mockHealth = {
  database: { status: 'healthy', latency_ms: 12 },
  scan_engine: { status: 'healthy' },
  google_integration: { status: 'connected' },
  office365_integration: { status: 'disconnected' },
  last_scan: new Date(Date.now() - 1800000).toISOString()
}

// ── HELPERS ────────────────────────────────────────────────────────────────
const severityColor = { critical: '#dc2626', high: '#f97316', medium: '#f59e0b', low: '#10b981' }
const severityLabel = { critical: 'Kritik', high: 'Yüksek', medium: 'Orta', low: 'Düşük' }
const statusLabel = { open: 'Açık', investigating: 'İnceleniyor', resolved: 'Çözüldü', false_positive: 'Yanlış Pozitif' }
const statusColor = { open: '#3b82f6', investigating: '#f59e0b', resolved: '#10b981', false_positive: '#6b7280' }

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins} dk önce`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs} sa önce`
  return `${Math.floor(hrs / 24)} gün önce`
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-glow)', borderRadius: 10, padding: '10px 14px' }}>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.78rem', marginBottom: 4 }}>{label}</p>
      <p style={{ color: 'var(--primary-light)', fontWeight: 600 }}>{payload[0]?.value} olay</p>
    </div>
  )
}

function PieTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-glow)', borderRadius: 10, padding: '10px 14px' }}>
      <p style={{ color: payload[0].payload.color, fontWeight: 600 }}>{payload[0].name}: {payload[0].value}</p>
    </div>
  )
}

// ── STAT CARD ──────────────────────────────────────────────────────────────
function StatCard({ icon: Icon, label, value, color, trend, trendLabel, loading }) {
  const trendDir = trend > 0 ? 'up' : trend < 0 ? 'down' : 'neutral'

  if (loading) {
    return (
      <div className="stat-card" style={{ '--card-accent': color }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <div className="skeleton" style={{ width: 38, height: 38, borderRadius: 10 }} />
          <div className="skeleton" style={{ width: 60, height: 22, borderRadius: 10 }} />
        </div>
        <div className="skeleton" style={{ width: '60%', height: 32, borderRadius: 6, marginTop: 8 }} />
        <div className="skeleton" style={{ width: '40%', height: 14, borderRadius: 4 }} />
      </div>
    )
  }

  return (
    <div className="stat-card" style={{ '--card-accent': color }}>
      <div className="stat-header">
        <div className="stat-icon" style={{ background: `${color}20`, border: `1px solid ${color}30` }}>
          <Icon size={18} color={color} />
        </div>
        {trend !== undefined && (
          <div className={`stat-trend ${trendDir}`}>
            {trendDir === 'up' ? <TrendingUp size={12} /> : trendDir === 'down' ? <TrendingDown size={12} /> : <Minus size={12} />}
            {Math.abs(trend)}%
          </div>
        )}
      </div>
      <div className="stat-value" style={{ color }}>{value ?? '—'}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}

// ── MAIN DASHBOARD ─────────────────────────────────────────────────────────
export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [trend, setTrend] = useState([])
  const [severity, setSeverity] = useState([])
  const [dataTypes, setDataTypes] = useState([])
  const [incidents, setIncidents] = useState([])
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState(new Date())

  const loadData = useCallback(async () => {
    try {
      const [statsRes, incRes, healthRes] = await Promise.allSettled([
        api.dashboard.getStats(),
        api.incidents.list({ limit: 5, sort: 'created_at', order: 'desc' }),
        api.dashboard.getHealth()
      ])

      if (statsRes.status === 'fulfilled') {
        const d = statsRes.value.data
        setStats(d)
        setTrend(d.trend_data || mockTrend)
        setSeverity(d.severity_distribution || mockSeverity)
        setDataTypes(d.data_type_distribution || mockDataTypes)
      } else {
        setStats(mockStats)
        setTrend(mockTrend)
        setSeverity(mockSeverity)
        setDataTypes(mockDataTypes)
      }

      if (incRes.status === 'fulfilled') setIncidents(incRes.value.data?.items || incRes.value.data || mockIncidents)
      else setIncidents(mockIncidents)

      if (healthRes.status === 'fulfilled') setHealth(healthRes.value.data)
      else setHealth(mockHealth)

      setLastRefresh(new Date())
    } catch {
      setStats(mockStats)
      setTrend(mockTrend)
      setSeverity(mockSeverity)
      setDataTypes(mockDataTypes)
      setIncidents(mockIncidents)
      setHealth(mockHealth)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [loadData])

  const s = stats || mockStats
  const riskColor = s.avg_risk_score >= 70 ? '#dc2626' : s.avg_risk_score >= 40 ? '#f59e0b' : '#10b981'

  const statCards = [
    { icon: AlertCircle, label: 'Toplam Olay', value: s.total_incidents, color: '#3b82f6', trend: s.trends?.incidents },
    { icon: ShieldAlert, label: 'Kritik Olaylar', value: s.critical_incidents, color: '#dc2626', trend: s.trends?.critical },
    { icon: Clock, label: 'Açık Olaylar', value: s.open_incidents, color: '#f97316', trend: s.trends?.open },
    { icon: Search, label: 'Bugünkü Tarama', value: s.today_scans, color: '#06b6d4', trend: s.trends?.scans },
    { icon: Activity, label: 'Ort. Risk Skoru', value: s.avg_risk_score?.toFixed(1), color: riskColor, trend: s.trends?.risk },
    { icon: Shield, label: 'Aktif Politika', value: s.active_policies, color: '#10b981', trend: s.trends?.policies }
  ]

  const trendFormatted = trend.map(d => ({
    ...d,
    label: d.date ? format(new Date(d.date), 'd MMM', { locale: tr }) : d.label
  }))

  return (
    <div style={{ animation: 'fadeInUp 0.4s ease' }}>
      {/* Header row */}
      <div className="page-header">
        <div>
          <h2>Kontrol Paneli</h2>
          <p>Son güncelleme: {lastRefresh.toLocaleTimeString('tr-TR')}</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadData} style={{ gap: 6 }}>
          <RefreshCw size={14} />
          Yenile
        </button>
      </div>

      {/* STAT CARDS */}
      <div className="stats-grid">
        {statCards.map((card) => (
          <StatCard key={card.label} {...card} loading={loading && !stats} />
        ))}
      </div>

      {/* CHARTS ROW */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: 16, marginBottom: 16 }}>
        {/* Trend chart */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <TrendingUp size={16} color="var(--primary)" />
              Son 30 Gün Olay Trendi
            </span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={trendFormatted} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="incidentGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(30,45,74,0.6)" vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
                axisLine={false} tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone" dataKey="count"
                stroke="#3b82f6" strokeWidth={2}
                fill="url(#incidentGrad)"
                dot={false} activeDot={{ r: 5, fill: '#3b82f6', strokeWidth: 2, stroke: '#0a0e1a' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Severity Pie */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <ShieldAlert size={16} color="var(--danger)" />
              Önem Dağılımı
            </span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={severity}
                cx="50%" cy="50%"
                innerRadius={55} outerRadius={85}
                paddingAngle={3}
                dataKey="value"
              >
                {severity.map((entry, i) => (
                  <Cell key={i} fill={entry.color} stroke="transparent" />
                ))}
              </Pie>
              <Tooltip content={<PieTooltip />} />
              <Legend
                iconType="circle" iconSize={8}
                formatter={(v) => <span style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>{v}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* BOTTOM ROW */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
        {/* Data types bar */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Database size={16} color="var(--accent)" />
              Tespit Edilen Veri Türleri
            </span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={dataTypes} layout="vertical" margin={{ top: 0, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(30,45,74,0.5)" horizontal={false} />
              <XAxis type="number" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} axisLine={false} tickLine={false} width={90} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-glow)', borderRadius: 10, color: 'var(--text-primary)', fontSize: '0.82rem' }}
                cursor={{ fill: 'rgba(59,130,246,0.05)' }}
              />
              <Bar dataKey="count" fill="#06b6d4" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Recent Incidents */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <AlertCircle size={16} color="var(--warning)" />
              Son Olaylar
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {loading && !incidents.length ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="skeleton" style={{ height: 48, borderRadius: 8 }} />
              ))
            ) : incidents.length === 0 ? (
              <div className="empty-state" style={{ padding: '30px 10px' }}>
                <CheckCircle size={28} color="var(--success)" />
                <p>Olay bulunamadı</p>
              </div>
            ) : (
              incidents.slice(0, 5).map(inc => (
                <div key={inc.id} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 10,
                  padding: '10px 12px',
                  background: 'rgba(10,14,26,0.4)',
                  borderRadius: 8,
                  border: '1px solid var(--border-color)',
                  transition: 'var(--transition)',
                  cursor: 'pointer'
                }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-glow)'}
                  onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border-color)'}
                >
                  <div style={{
                    width: 3, height: '100%', minHeight: 32,
                    background: severityColor[inc.severity] || '#3b82f6',
                    borderRadius: 2, flexShrink: 0
                  }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div className="truncate" style={{ fontSize: '0.82rem', fontWeight: 500, color: 'var(--text-primary)', marginBottom: 3 }}>
                      {inc.title}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: '0.7rem', color: severityColor[inc.severity], fontWeight: 600 }}>
                        {severityLabel[inc.severity]}
                      </span>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        {timeAgo(inc.created_at)}
                      </span>
                    </div>
                  </div>
                  <span style={{
                    fontSize: '0.7rem', fontWeight: 600, color: statusColor[inc.status],
                    background: `${statusColor[inc.status]}15`, padding: '2px 8px',
                    borderRadius: 10, whiteSpace: 'nowrap', flexShrink: 0
                  }}>
                    {statusLabel[inc.status]}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* System Health */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Activity size={16} color="var(--success)" />
              Sistem Durumu
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {[
              {
                label: 'Veritabanı',
                status: health?.database?.status === 'healthy',
                detail: health?.database?.latency_ms ? `${health.database.latency_ms}ms gecikme` : ''
              },
              {
                label: 'Tarama Motoru',
                status: health?.scan_engine?.status === 'healthy',
                detail: 'Aktif ve hazır'
              },
              {
                label: 'Google Workspace',
                status: health?.google_integration?.status === 'connected',
                detail: health?.google_integration?.status === 'connected' ? 'Bağlı' : 'Bağlı değil'
              },
              {
                label: 'Microsoft 365',
                status: health?.office365_integration?.status === 'connected',
                detail: health?.office365_integration?.status === 'connected' ? 'Bağlı' : 'Bağlı değil'
              }
            ].map(({ label, status, detail }) => (
              <div key={label} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '10px 12px',
                background: 'rgba(10,14,26,0.4)',
                borderRadius: 8,
                border: `1px solid ${status ? 'rgba(16,185,129,0.15)' : 'rgba(107,114,128,0.15)'}`
              }}>
                <div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 500, color: 'var(--text-primary)', marginBottom: 2 }}>{label}</div>
                  {detail && <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{detail}</div>}
                </div>
                {status
                  ? <CheckCircle size={16} color="var(--success)" />
                  : <XCircle size={16} color="var(--text-muted)" />
                }
              </div>
            ))}

            {health?.last_scan && (
              <div style={{ padding: '8px 12px', background: 'rgba(59,130,246,0.06)', borderRadius: 8, border: '1px solid rgba(59,130,246,0.15)' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 2 }}>Son Tarama</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--primary-light)', fontWeight: 500 }}>
                  {timeAgo(health.last_scan)}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
