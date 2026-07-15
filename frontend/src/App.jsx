import React, { Suspense, lazy } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout/Layout'

const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Policies = lazy(() => import('./pages/Policies'))
const Incidents = lazy(() => import('./pages/Incidents'))
const Scanner = lazy(() => import('./pages/Scanner'))
const Reports = lazy(() => import('./pages/Reports'))
const Integrations = lazy(() => import('./pages/Integrations'))
const Settings = lazy(() => import('./pages/Settings'))

function LoadingScreen({ message = 'Yükleniyor...' }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      background: '#0a0e1a',
      gap: '20px'
    }}>
      <div style={{
        width: '56px', height: '56px',
        background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
        borderRadius: '14px',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: '0 0 30px rgba(59,130,246,0.4)',
        fontSize: '1.8rem'
      }}>
        🛡️
      </div>
      <div style={{ textAlign: 'center' }}>
        <p style={{ color: '#f0f4ff', fontWeight: 600, fontSize: '1rem', marginBottom: '6px' }}>
          DLP Güvenlik Sistemi
        </p>
        <p style={{ color: '#4a5a7a', fontSize: '0.82rem' }}>{message}</p>
      </div>
      <div className="loading-spinner" />
    </div>
  )
}

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  if (loading) return <LoadingScreen message="Kimlik doğrulanıyor..." />
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}

function AppRoutes() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) return <LoadingScreen message="DLP Sistemi Yükleniyor..." />

  return (
    <Suspense fallback={<LoadingScreen />}>
      <Routes>
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/" replace /> : <Login />}
        />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="politikalar" element={<Policies />} />
          <Route path="olaylar" element={<Incidents />} />
          <Route path="tarama" element={<Scanner />} />
          <Route path="raporlar" element={<Reports />} />
          <Route path="entegrasyonlar" element={<Integrations />} />
          <Route path="ayarlar" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
