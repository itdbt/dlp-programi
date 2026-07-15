import React, { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('dlp_token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      api.auth.getMe()
        .then(res => setUser(res.data))
        .catch(() => {
          setToken(null)
          localStorage.removeItem('dlp_token')
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [token])

  const login = async (email, password) => {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)
    const res = await api.auth.login(formData)
    const { access_token } = res.data
    localStorage.setItem('dlp_token', access_token)
    setToken(access_token)
    const userRes = await api.auth.getMe()
    setUser(userRes.data)
    return userRes.data
  }

  const logout = () => {
    localStorage.removeItem('dlp_token')
    setToken(null)
    setUser(null)
  }

  const updateUser = (updatedUser) => setUser(updatedUser)

  return (
    <AuthContext.Provider value={{
      user,
      token,
      login,
      logout,
      updateUser,
      isAuthenticated: !!token,
      loading
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
