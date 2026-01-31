import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { apiFetch } from './api'

type User = {
  id: string
  email: string
  tenant_id: string
  display_name?: string | null
}

type Tenant = {
  id: string
  slug: string
  name: string
  plan: string
  currency: string
}

type AuthState = {
  user: User | null
  tenant: Tenant | null
  permissions: string[]
  loading: boolean
}

type AuthContextValue = AuthState & {
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    tenant: null,
    permissions: [],
    loading: true
  })

  const loadSession = useCallback(async () => {
    try {
      const data = await apiFetch<{ user: User; tenant: Tenant; permissions: string[] }>('/auth/me')
      setState({ user: data.user, tenant: data.tenant, permissions: data.permissions, loading: false })
    } catch {
      setState({ user: null, tenant: null, permissions: [], loading: false })
    }
  }, [])

  useEffect(() => {
    void loadSession()
  }, [loadSession])

  const login = useCallback(async (email: string, password: string) => {
    const data = await apiFetch<{ user: User; tenant: Tenant; permissions: string[] }>(
      '/auth/login',
      {
        method: 'POST',
        body: JSON.stringify({ email, password })
      }
    )
    setState({ user: data.user, tenant: data.tenant, permissions: data.permissions, loading: false })
  }, [])

  const logout = useCallback(async () => {
    await apiFetch('/auth/logout', { method: 'POST' })
    setState({ user: null, tenant: null, permissions: [], loading: false })
  }, [])

  const value = useMemo(() => ({ ...state, login, logout }), [state, login, logout])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
