import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Mail, Lock, Eye, EyeOff, AlertCircle, ChevronRight } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email.trim()) { setError('E-posta adresi gereklidir.'); return }
    if (!password.trim()) { setError('Şifre gereklidir.'); return }
    setError('')
    setLoading(true)
    try {
      const user = await login(email, password)
      toast.success(`Hoş geldiniz, ${user?.full_name || user?.email}!`)
      navigate('/')
    } catch (err) {
      const msg = err.response?.data?.detail || 'Giriş başarısız. E-posta veya şifre hatalı.'
      setError(msg)
      toast.error('Giriş başarısız!')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0a0e1a',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      overflow: 'hidden',
      padding: '20px'
    }}>
      {/* Animated gradient blobs */}
      <div style={{
        position: 'absolute', top: '-20%', left: '-10%',
        width: '600px', height: '600px',
        background: 'radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%)',
        borderRadius: '50%',
        animation: 'blobMove1 12s ease-in-out infinite',
        pointerEvents: 'none'
      }} />
      <div style={{
        position: 'absolute', top: '30%', right: '-15%',
        width: '700px', height: '700px',
        background: 'radial-gradient(circle, rgba(6,182,212,0.1) 0%, transparent 70%)',
        borderRadius: '50%',
        animation: 'blobMove2 15s ease-in-out infinite',
        pointerEvents: 'none'
      }} />
      <div style={{
        position: 'absolute', bottom: '-20%', left: '25%',
        width: '500px', height: '500px',
        background: 'radial-gradient(circle, rgba(139,92,246,0.12) 0%, transparent 70%)',
        borderRadius: '50%',
        animation: 'blobMove3 10s ease-in-out infinite',
        pointerEvents: 'none'
      }} />

      {/* Floating particles */}
      {[...Array(20)].map((_, i) => (
        <div key={i} style={{
          position: 'absolute',
          width: Math.random() * 3 + 1 + 'px',
          height: Math.random() * 3 + 1 + 'px',
          background: i % 3 === 0 ? 'rgba(59,130,246,0.4)' : i % 3 === 1 ? 'rgba(6,182,212,0.3)' : 'rgba(139,92,246,0.3)',
          borderRadius: '50%',
          top: Math.random() * 100 + '%',
          left: Math.random() * 100 + '%',
          animation: `float ${6 + Math.random() * 8}s ease-in-out infinite`,
          animationDelay: Math.random() * 5 + 's',
          pointerEvents: 'none'
        }} />
      ))}

      {/* Grid overlay */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: 'linear-gradient(rgba(30,45,74,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(30,45,74,0.08) 1px, transparent 1px)',
        backgroundSize: '50px 50px',
        pointerEvents: 'none'
      }} />

      {/* Login card */}
      <div style={{
        width: '100%',
        maxWidth: '420px',
        background: 'rgba(19,29,53,0.85)',
        backdropFilter: 'blur(24px)',
        WebkitBackdropFilter: 'blur(24px)',
        border: '1px solid rgba(45,74,122,0.6)',
        borderRadius: '24px',
        padding: '40px 36px',
        boxShadow: '0 25px 60px rgba(0,0,0,0.6), 0 0 60px rgba(59,130,246,0.08)',
        position: 'relative',
        zIndex: 1,
        animation: 'fadeInUp 0.5s ease'
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            width: '70px', height: '70px',
            background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
            borderRadius: '18px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 20px',
            boxShadow: '0 0 40px rgba(59,130,246,0.4), 0 8px 24px rgba(0,0,0,0.3)',
            animation: 'float 4s ease-in-out infinite'
          }}>
            <Shield size={34} color="white" />
          </div>
          <h1 style={{
            fontSize: '1.6rem', fontWeight: 800,
            background: 'linear-gradient(135deg, #f0f4ff, #60a5fa)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            backgroundClip: 'text', marginBottom: '8px'
          }}>
            DLP Güvenlik Sistemi
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
            Kurumsal Veri Kaybı Önleme Platformu
          </p>
        </div>

        {/* Error message */}
        {error && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '10px',
            background: 'rgba(239,68,68,0.1)',
            border: '1px solid rgba(239,68,68,0.3)',
            borderRadius: '10px', padding: '12px 14px',
            marginBottom: '20px', animation: 'fadeIn 0.2s ease'
          }}>
            <AlertCircle size={16} color="#ef4444" style={{ flexShrink: 0 }} />
            <span style={{ color: '#fca5a5', fontSize: '0.82rem' }}>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Email */}
          <div className="form-group">
            <label className="form-label">E-posta Adresi</label>
            <div className="input-with-icon">
              <Mail size={16} className="input-icon" />
              <input
                type="email"
                className="form-input"
                placeholder="ornek@sirket.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                autoComplete="email"
                autoFocus
                style={{ paddingLeft: '40px' }}
              />
            </div>
          </div>

          {/* Password */}
          <div className="form-group">
            <label className="form-label">Şifre</label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} style={{
                position: 'absolute', left: '12px', top: '50%',
                transform: 'translateY(-50%)', color: 'var(--text-muted)',
                pointerEvents: 'none'
              }} />
              <input
                type={showPassword ? 'text' : 'password'}
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete="current-password"
                style={{ paddingLeft: '40px', paddingRight: '44px' }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute', right: '12px', top: '50%',
                  transform: 'translateY(-50%)', background: 'none', border: 'none',
                  color: 'var(--text-muted)', cursor: 'pointer', padding: '2px',
                  display: 'flex', alignItems: 'center'
                }}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary btn-full"
            style={{
              padding: '13px',
              fontSize: '0.95rem',
              fontWeight: 600,
              marginTop: '8px',
              letterSpacing: '0.3px',
              borderRadius: '12px',
              background: loading ? 'rgba(59,130,246,0.5)' : 'linear-gradient(135deg, #3b82f6, #2563eb)',
              boxShadow: loading ? 'none' : '0 4px 20px rgba(59,130,246,0.4)',
              gap: 10
            }}
          >
            {loading ? (
              <>
                <div className="loading-spinner" style={{ width: 18, height: 18 }} />
                Giriş yapılıyor...
              </>
            ) : (
              <>
                Giriş Yap
                <ChevronRight size={18} />
              </>
            )}
          </button>
        </form>

        {/* Demo credentials */}
        <div style={{
          marginTop: '24px',
          background: 'rgba(59,130,246,0.06)',
          border: '1px solid rgba(59,130,246,0.15)',
          borderRadius: '10px',
          padding: '14px 16px'
        }}>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '8px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Demo Giriş Bilgileri
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {[
              { label: 'Yönetici', email: 'admin@dlp.local', pass: 'admin123' },
              { label: 'Analist', email: 'analyst@dlp.local', pass: 'analyst123' }
            ].map(({ label, email: e, pass }) => (
              <button
                key={e}
                type="button"
                onClick={() => { setEmail(e); setPassword(pass) }}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--text-secondary)', fontSize: '0.78rem',
                  padding: '4px 0', fontFamily: 'inherit',
                  transition: 'var(--transition)', borderRadius: '4px'
                }}
              >
                <span style={{ color: 'var(--primary-light)', fontWeight: 500 }}>{label}</span>
                <span style={{ color: 'var(--text-muted)', fontFamily: 'monospace', fontSize: '0.72rem' }}>{e}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <p style={{ textAlign: 'center', marginTop: '24px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          © 2025 DLP Güvenlik Sistemi — Tüm hakları saklıdır.
        </p>
      </div>
    </div>
  )
}
