import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#131d35',
            color: '#f0f4ff',
            border: '1px solid #1e2d4a',
            borderRadius: '10px',
            fontSize: '0.875rem',
            fontFamily: 'Inter, sans-serif'
          },
          success: {
            iconTheme: { primary: '#10b981', secondary: '#131d35' },
            style: { border: '1px solid rgba(16,185,129,0.3)' }
          },
          error: {
            iconTheme: { primary: '#ef4444', secondary: '#131d35' },
            style: { border: '1px solid rgba(239,68,68,0.3)' }
          },
          loading: {
            iconTheme: { primary: '#3b82f6', secondary: '#131d35' }
          }
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
)
