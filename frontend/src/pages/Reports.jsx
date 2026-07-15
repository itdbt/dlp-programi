import React, { useState, useEffect, useCallback } from 'react'
import { Download, RefreshCw, TrendingUp, BarChart3, Shield, AlertTriangle } from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, BarChart, Bar
} from 'recharts'
import { api } from '../api/client'
import { format, subDays } from 'date-fns'
import { tr } from 'date-fns/locale'
import toast from 'react-hot-toast'

// ── MOCK DATA ──────────────────────────────────────────────────────────────
const generateTrend = () => Array.from({ length: 30 }, (_, i) => ({
  date: format(subDays(new Date(), 29 - i), 'd MMM', { locale: tr }),
  olaylar: Math.floor(Math.random() * 15) + 1,
  tarama: Math.floor(Math.random() * 5) + 1
}))

const mockTrend = generateTrend()

const mockSeverityData = [
  { name: 'Kritik', value: 18, color: '#dc2626' },
  { name: 'Yüksek', value: 56, color: '#f97316' },
  { name: 'Orta', value: 98, color: '#f59e0b' },
  { name: 'Düşük', value: 75, color: '#10b981' }
]

const mockTopPolicies = [
  { name: 'Finansal Veri Koruma', count: 45 },
  { name: 'Kişisel Veri Koruma', count: 67 },
  { name: 'Kod Güvenliği', count: 34 },
  { name: 'Sağlık Bilgisi', count: 8 },
  { name: 'İletişim Verisi', count: 12 }
]

const mockDataTypes = [
  { name: 'TC Kimlik No', count: 89, risk: 'Yüksek' },
  { name: 'Kredi Kartı', count: 67, risk: 'Kritik' },
  { name: 'IBAN', count: 54, risk: 'Yüksek' },
  { name: 'E-posta', count: 43, risk: 'Orta' },
  { name: 'Telefon', count: 38, risk: 'Orta' },
  { name: 'API Anahtarı', count: 29, risk: 'Kritik' },
  { name: 'Şifre/Hash', count: 21, risk: 'Kritik' },
  { name: 'Pasaport', count: 15, risk: 'Yüksek' },
  { name: 'Vergi No', count: 34, risk: 'Orta' },
  { name: 'Sağlık Bilgisi', count: 12, risk: 'Kritik' }
]

const mockIncidentTable = [
  { id: 1, title: 'Kredi kartı verisi tespit edildi', severity: 'critical', status: 'open', policy: 'Finansal Veri Koruma', date: '25.06.2025' },
  { id: 2, title: 'TC kimlik numarası paylaşıldı', severity: 'high', status: 'resolved', policy: 'Kişisel Veri Koruma', date: '24.06.2025' },
  { id: 3, title: 'API anahtarı açık bırakıldı', severity: 'critical', status: 'investigating', policy: 'Kod Güvenliği', date: '23.06.2025' }
]

const mockCompliance = [
  { name: 'KVKK', score: 87, color: '#3b82f6', requirements: ['Veri envanteri oluşturuldu', 'Aydınlatma metni hazır', 'Veri ihlal prosedürü mevcut', 'DPO atandı'] },
  { name: 'GDPR', score: 82, color: '#06b6d4', requirements: ['Data mapping tamamlandı', 'Privacy by design uygulandı', 'Veri silme prosedürü mevcut', 'Şikayet mekanizması aktif'] },
  { name: 'PCI DSS', score: 68, color: '#f59e0b', requirements: ['Kart verisi şifreleme aktif', 'Erişim logları tutuluyor', 'Güvenlik açığı taraması yapıldı', 'Penetrasyon testi yapılmadı'] },
  { name: 'HIPAA', score: 54, color: '#ef4444', requirements: ['PHI tespiti aktif', 'Erişim kontrolü mevcut', 'BAA anlaşmaları gerekli', 'Risk analizi tamamlanmadı'] }
]

const mockRiskMatrix = [
  { likelihood: 5, impact: 5, label: 'Kredi Kartı Sızıntısı', count: 3 },
  { likelihood: 4, impact: 5, label: 'TC Kimlik İhlali', count: 12 },
  { likelihood: 3, impact: 4, label: 'API Sızıntısı', count: 5 },
  { likelihood: 2, impact: 3, label: 'E-posta Sızıntısı', count: 28 },
  { likelihood: 1, impact: 2, label: 'Düşük Risk İhlali', count: 45 }
]

// ── HELPERS ────────────────────────────────────────────────────────────────
const sevColor = { critical: '#dc2626', high: '#f97316', medium: '#f59e0b', low: '#10b981' }
const sevLabel = { critical: 'Kritik', high: 'Yüksek', medium: 'Orta', low: 'Düşük' }
const stColor = { open: '#3b82f6', investigating: '#f59e0b', resolved: '#10b981', false_positive: '#6b7280' }
const stLabel = { open: 'Açık', investigating: 'İnceleniyor', resolved: 'Çözüldü', false_positive: 'Yanlış Pozitif' }

function getHeatmapColor(l, impact) {
  const score = l * impact
  if (score >= 20) return 'heatmap-critical'
  if (score >= 12) return 'heatmap-high'
  if (score >= 6) return 'heatmap-medium'
  return 'heatmap-low'
}

// ── COMPLIANCE TAB ─────────────────────────────────────────────────────────
function ComplianceTab() {
  return (
    <div className="grid-2" style={{ gap: 20 }}>
      {mockCompliance.map(comp => (
        <div key={comp.name} className="compliance-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div>
              <div style={{
                fontSize: '1.3rem', fontWeight: 800, color: comp.color,
                background: `${comp.color}12`, border: `2px solid ${comp.color}30`,
                padding: '4px 14px', borderRadius: 8, display: 'inline-block', marginBottom: 6
              }}>
                {comp.name}
              </div>
            </div>
            <div>
              <div className="compliance-score" style={{ color: comp.color }}>{comp.score}%</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'right' }}>Uyumluluk</div>
            </div>
          </div>
          <div className="progress" style={{ height: 8, marginBottom: 16 }}>
            <div className="progress-bar" style={{ width: `${comp.score}%`, background: `linear-gradient(to right, ${comp.color}99, ${comp.color})` }} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {comp.requirements.map((req, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{
                  width: 18, height: 18, borderRadius: '50%', flexShrink: 0,
                  background: i < 3 ? `${comp.color}18` : 'rgba(107,114,128,0.15)',
                  border: `1px solid ${i < 3 ? comp.color + '40' : 'rgba(107,114,128,0.3)'}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.65rem', color: i < 3 ? comp.color : 'var(--text-muted)'
                }}>
                  {i < 3 ? '✓' : '!'}
                </div>
                <span style={{ fontSize: '0.8rem', color: i < 3 ? 'var(--text-secondary)' : 'var(--text-muted)' }}>{req}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// ── RISK MATRIX TAB ────────────────────────────────────────────────────────
function RiskMatrixTab() {
  const likelihoods = ['Çok Düşük', 'Düşük', 'Orta', 'Yüksek', 'Çok Yüksek']
  const impacts = ['Çok Düşük', 'Düşük', 'Orta', 'Yüksek', 'Kritik']

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: 12, alignItems: 'center' }}>
        <div style={{ writingMode: 'vertical-rl', textOrientation: 'mixed', transform: 'rotate(180deg)', color: 'var(--text-muted)', fontSize: '0.78rem', fontWeight: 600, textAlign: 'center' }}>
          ← Olasılık
        </div>
        <div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {[5, 4, 3, 2, 1].map(l => (
              <div key={l} style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                <div style={{ width: 70, fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'right', flexShrink: 0 }}>
                  {likelihoods[l - 1]}
                </div>
                {[1, 2, 3, 4, 5].map(impact => {
                  const risk = mockRiskMatrix.find(r => r.likelihood === l && r.impact === impact)
                  return (
                    <div key={impact}
                      className={`heatmap-cell ${getHeatmapColor(l, impact)}`}
                      style={{ flex: 1, minHeight: 50, fontSize: '0.75rem', fontWeight: 700 }}
                      title={risk ? `${risk.label}: ${risk.count} olay` : ''}
                    >
                      {risk ? risk.count : l * impact}
                    </div>
                  )
                })}
              </div>
            ))}
            <div style={{ display: 'flex', gap: 4, paddingLeft: 74 }}>
              {impacts.map((imp, i) => (
                <div key={i} style={{ flex: 1, textAlign: 'center', fontSize: '0.68rem', color: 'var(--text-muted)', paddingTop: 6 }}>
                  {imp}
                </div>
              ))}
            </div>
            <div style={{ textAlign: 'center', fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600, paddingLeft: 74 }}>
              Etki →
            </div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: 16, marginTop: 20, flexWrap: 'wrap' }}>
        {[
          { label: 'Düşük Risk (1-5)', cls: 'heatmap-low' },
          { label: 'Orta Risk (6-11)', cls: 'heatmap-medium' },
          { label: 'Yüksek Risk (12-19)', cls: 'heatmap-high' },
          { label: 'Kritik Risk (20-25)', cls: 'heatmap-critical' }
        ].map(({ label, cls }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div className={`heatmap-cell ${cls}`} style={{ width: 20, height: 20, minHeight: 20, borderRadius: 4 }} />
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{label}</span>
          </div>
        ))}
      </div>

      {/* Risk items */}
      <div style={{ marginTop: 24 }}>
        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Tespit Edilen Risk Kalemleri
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {mockRiskMatrix.map((risk, i) => {
            const score = risk.likelihood * risk.impact
            const cls = getHeatmapColor(risk.likelihood, risk.impact)
            const color = cls.includes('critical') ? '#dc2626' : cls.includes('high') ? '#f97316' : cls.includes('medium') ? '#f59e0b' : '#10b981'
            return (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                background: 'rgba(10,14,26,0.4)', borderRadius: 8, padding: '10px 14px',
                border: '1px solid var(--border-color)'
              }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 8, background: `${color}15`,
                  border: `1px solid ${color}30`, display: 'flex', alignItems: 'center',
                  justifyContent: 'center', fontWeight: 800, color, fontSize: '0.9rem', flexShrink: 0
                }}>{score}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-primary)' }}>{risk.label}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    Olasılık: {risk.likelihood}/5 • Etki: {risk.impact}/5
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color }}>{risk.count}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>olay</div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ── MAIN COMPONENT ─────────────────────────────────────────────────────────
export default function Reports() {
  const [activeTab, setActiveTab] = useState('incidents')
  const [dateFrom, setDateFrom] = useState(format(subDays(new Date(), 30), 'yyyy-MM-dd'))
  const [dateTo, setDateTo] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [trendData] = useState(mockTrend)

  const tabs = [
    { id: 'incidents', label: '📈 Olay Raporu' },
    { id: 'scans', label: '🔍 Tarama Raporu' },
    { id: 'compliance', label: '✅ Uyumluluk' },
    { id: 'risk', label: '⚠️ Risk Matrisi' },
    { id: 'datatypes', label: '🔔 Veri Türleri' }
  ]

  const handleExport = (type) => {
    toast.success(`${type} raporu dışa aktarılıyor...`)
    setTimeout(() => toast.success('Rapor hazır! İndirme başladı.'), 1500)
  }

  return (
    <div style={{ animation: 'fadeInUp 0.4s ease' }}>
      <div className="page-header">
        <div>
          <h2>Raporlar & Analitik</h2>
          <p>Kapsamlı güvenlik raporları ve analizler</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <input type="date" className="form-input" value={dateFrom} onChange={e => setDateFrom(e.target.value)} style={{ width: 150 }} />
          <input type="date" className="form-input" value={dateTo} onChange={e => setDateTo(e.target.value)} style={{ width: 150 }} />
          <button className="btn btn-primary" style={{ gap: 6 }} onClick={() => toast.loading('Rapor oluşturuluyor...')}>
            <RefreshCw size={14} />Rapor Oluştur
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs" style={{ marginBottom: 24 }}>
        {tabs.map(t => (
          <button key={t.id} className={`tab ${activeTab === t.id ? 'active' : ''}`} onClick={() => setActiveTab(t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      {/* OLAY RAPORU */}
      {activeTab === 'incidents' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button className="btn btn-secondary btn-sm" onClick={() => handleExport('CSV')} style={{ gap: 6 }}>
              <Download size={14} />CSV Dışa Aktar
            </button>
          </div>

          {/* Summary stats */}
          <div className="grid-4" style={{ gap: 12 }}>
            {[
              { label: 'Toplam Olay', value: 247, color: '#3b82f6' },
              { label: 'Çözülen', value: 134, color: '#10b981' },
              { label: 'Açık', value: 43, color: '#f97316' },
              { label: 'Kritik', value: 18, color: '#dc2626' }
            ].map(({ label, value, color }) => (
              <div key={label} style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-color)',
                borderRadius: 12, padding: '16px', textAlign: 'center'
              }}>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color, lineHeight: 1 }}>{value}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 6 }}>{label}</div>
              </div>
            ))}
          </div>

          {/* Charts */}
          <div className="card">
            <div className="card-header">
              <span className="card-title"><TrendingUp size={16} color="var(--primary)" />Olaylar Zaman İçinde</span>
            </div>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={trendData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="incGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(30,45,74,0.5)" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-glow)', borderRadius: 10, color: 'var(--text-primary)', fontSize: '0.82rem' }} />
                <Area type="monotone" dataKey="olaylar" stroke="#3b82f6" strokeWidth={2} fill="url(#incGrad)" dot={false} name="Olay Sayısı" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="card">
              <div className="card-header"><span className="card-title">Önem Dağılımı</span></div>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={mockSeverityData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3} dataKey="value">
                    {mockSeverityData.map((e, i) => <Cell key={i} fill={e.color} stroke="transparent" />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-glow)', borderRadius: 10, color: 'var(--text-primary)', fontSize: '0.82rem' }} />
                  <Legend iconType="circle" iconSize={8} formatter={v => <span style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>{v}</span>} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="card">
              <div className="card-header"><span className="card-title">En Aktif Politikalar</span></div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={mockTopPolicies} layout="vertical" margin={{ left: 10, right: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(30,45,74,0.5)" horizontal={false} />
                  <XAxis type="number" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 9 }} axisLine={false} tickLine={false} width={130} />
                  <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-glow)', borderRadius: 10, color: 'var(--text-primary)', fontSize: '0.82rem' }} cursor={{ fill: 'rgba(59,130,246,0.05)' }} />
                  <Bar dataKey="count" fill="#06b6d4" radius={[0, 4, 4, 0]} name="Olay Sayısı" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Incident table */}
          <div className="card">
            <div className="card-header"><span className="card-title">Olay Listesi</span></div>
            <div className="table-container">
              <table className="dlp-table">
                <thead>
                  <tr><th>#</th><th>Başlık</th><th>Önem</th><th>Durum</th><th>Politika</th><th>Tarih</th></tr>
                </thead>
                <tbody>
                  {mockIncidentTable.map(inc => (
                    <tr key={inc.id}>
                      <td style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>#{inc.id}</td>
                      <td style={{ fontWeight: 500 }}>{inc.title}</td>
                      <td><span style={{ padding: '3px 8px', borderRadius: 20, fontSize: '0.7rem', fontWeight: 600, background: `${sevColor[inc.severity]}12`, color: sevColor[inc.severity], border: `1px solid ${sevColor[inc.severity]}30` }}>{sevLabel[inc.severity]}</span></td>
                      <td><span style={{ padding: '3px 8px', borderRadius: 20, fontSize: '0.7rem', fontWeight: 600, background: `${stColor[inc.status]}12`, color: stColor[inc.status] }}>{stLabel[inc.status]}</span></td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>{inc.policy}</td>
                      <td style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>{inc.date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TARAMA RAPORU */}
      {activeTab === 'scans' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="grid-4" style={{ gap: 12 }}>
            {[
              { label: 'Toplam Tarama', value: 42, color: '#3b82f6' },
              { label: 'Taranan Dosya', value: '3.049', color: '#06b6d4' },
              { label: 'Tespit Edilen Olay', value: 53, color: '#f97316' },
              { label: 'Başarısız Tarama', value: 2, color: '#ef4444' }
            ].map(({ label, value, color }) => (
              <div key={label} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 12, padding: 16, textAlign: 'center' }}>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color, lineHeight: 1 }}>{value}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 6 }}>{label}</div>
              </div>
            ))}
          </div>

          <div className="card">
            <div className="card-header"><span className="card-title">Tarama Aktivitesi</span></div>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={trendData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(30,45,74,0.5)" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-glow)', borderRadius: 10, color: 'var(--text-primary)', fontSize: '0.82rem' }} />
                <Area type="monotone" dataKey="tarama" stroke="#06b6d4" strokeWidth={2} fill="url(#scanGrad)" dot={false} name="Tarama" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* UYUMLULUK */}
      {activeTab === 'compliance' && <ComplianceTab />}

      {/* RİSK MATRİSİ */}
      {activeTab === 'risk' && (
        <div className="card">
          <div className="card-header"><span className="card-title"><AlertTriangle size={16} color="var(--warning)" />Risk Matrisi</span></div>
          <RiskMatrixTab />
        </div>
      )}

      {/* VERİ TÜRLERİ */}
      {activeTab === 'datatypes' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="card">
            <div className="card-header"><span className="card-title"><BarChart3 size={16} color="var(--accent)" />Veri Türü Frekansı</span></div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={mockDataTypes} layout="vertical" margin={{ left: 10, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(30,45,74,0.5)" horizontal={false} />
                <XAxis type="number" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} axisLine={false} tickLine={false} width={110} />
                <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-glow)', borderRadius: 10, color: 'var(--text-primary)', fontSize: '0.82rem' }} cursor={{ fill: 'rgba(59,130,246,0.05)' }} />
                <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} name="Tespit Sayısı" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="card">
            <div className="card-header"><span className="card-title">Veri Türü Detayları</span></div>
            <div className="table-container">
              <table className="dlp-table">
                <thead>
                  <tr><th>Veri Türü</th><th>Tespit Sayısı</th><th>Risk Seviyesi</th><th>Oran</th></tr>
                </thead>
                <tbody>
                  {mockDataTypes.sort((a, b) => b.count - a.count).map((dt, i) => {
                    const max = mockDataTypes[0].count
                    const rcolor = dt.risk === 'Kritik' ? '#dc2626' : dt.risk === 'Yüksek' ? '#f97316' : dt.risk === 'Orta' ? '#f59e0b' : '#10b981'
                    return (
                      <tr key={i}>
                        <td style={{ fontWeight: 500 }}>{dt.name}</td>
                        <td style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{dt.count}</td>
                        <td><span style={{ padding: '3px 8px', borderRadius: 20, fontSize: '0.7rem', fontWeight: 600, background: `${rcolor}12`, color: rcolor }}>{dt.risk}</span></td>
                        <td style={{ width: 150 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <div className="progress" style={{ flex: 1 }}>
                              <div className="progress-bar" style={{ width: `${(dt.count / max) * 100}%`, background: rcolor }} />
                            </div>
                            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', minWidth: 36 }}>
                              {Math.round((dt.count / mockDataTypes.reduce((s, d) => s + d.count, 0)) * 100)}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
