import { createContext, useCallback, useEffect, useMemo, useState } from 'react'
import api, { clearTokens, endpoints, setTokens } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [hospital, setHospital] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadSession = useCallback(async () => {
    try {
      const { data } = await api.get(endpoints.me)
      setUser(data)
      const hospitalResponse = await api.get(endpoints.hospital)
      setHospital(hospitalResponse.data)
    } catch {
      clearTokens()
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSession()
  }, [loadSession])

  const login = useCallback(async (identifier, password) => {
    const { data } = await api.post(endpoints.login, { identifier, password })
    setTokens(data.tokens)
    setUser(data.user)
    const hospitalResponse = await api.get(endpoints.hospital)
    setHospital(hospitalResponse.data)
    return data
  }, [])

  const logout = useCallback(async () => {
    const refresh = localStorage.getItem('asternova.refresh')
    try {
      await api.post(endpoints.logout, { refresh })
    } catch {
      /* the token may already be invalid - signing out locally is enough */
    }
    clearTokens()
    setUser(null)
  }, [])

  const can = useCallback(
    (module, action = 'view') => {
      if (!user) return false
      if (user.role === 'super_admin') return true
      const permissions = user.permissions || {}
      const actions = permissions[module] || []
      return actions.includes(action) || actions.includes('*')
    },
    [user],
  )

  const value = useMemo(
    () => ({ user, hospital, loading, login, logout, can, refresh: loadSession, setUser }),
    [user, hospital, loading, login, logout, can, loadSession],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export { useAuth } from './useAuth.js'
export default AuthContext
