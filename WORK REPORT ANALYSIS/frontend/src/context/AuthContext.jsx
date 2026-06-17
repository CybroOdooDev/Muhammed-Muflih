import { createContext, useContext, useEffect, useState } from 'react'

import api, { ACCESS_KEY, REFRESH_KEY } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // On first load, if we have a token, fetch the current user.
  useEffect(() => {
    const token = localStorage.getItem(ACCESS_KEY)
    if (!token) {
      setLoading(false)
      return
    }
    api
      .get('/auth/me/')
      .then((res) => setUser(res.data))
      .catch(() => {
        localStorage.removeItem(ACCESS_KEY)
        localStorage.removeItem(REFRESH_KEY)
      })
      .finally(() => setLoading(false))
  }, [])

  // Exchange a Google authorization code for our JWTs (also stores Gmail tokens).
  async function loginWithGoogle(code) {
    const { data } = await api.post('/auth/google/', { code })
    localStorage.setItem(ACCESS_KEY, data.access)
    localStorage.setItem(REFRESH_KEY, data.refresh)
    setUser(data.user)
    return data.user
  }

  function logout() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, loginWithGoogle, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}
