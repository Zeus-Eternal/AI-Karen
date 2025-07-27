"use client";
import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { getAuthService } from '@/services/authService'
import type { CurrentUser } from '@/services'
import { getAuthToken } from '@/lib/auth-token'

interface AuthContextValue {
  user: CurrentUser | null
  loading: boolean
  login: (u: string, p: string) => Promise<boolean>
  logout: () => void
  updateCredentials: (u?: string, p?: string) => Promise<boolean>
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  loading: true,
  login: async () => false,
  logout: () => {},
  updateCredentials: async () => false,
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const authService = getAuthService()
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = getAuthToken()
    if (!token) {
      setLoading(false)
      return
    }
    authService.getCurrentUser().then(u => {
      setUser(u)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const login = async (u: string, p: string) => {
    const res = await authService.login(u, p)
    if (res) {
      setUser({ user_id: res.user_id, roles: res.roles })
      return true
    }
    return false
  }

  const logout = () => {
    authService.logout()
    setUser(null)
  }

  const updateCredentials = async (u?: string, p?: string) => {
    const res = await authService.updateCredentials(u, p)
    if (res) {
      setUser({ user_id: res.user_id, roles: res.roles })
      return true
    }
    return false
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, updateCredentials }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
