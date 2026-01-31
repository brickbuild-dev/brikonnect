import { apiFetch } from './api'

export type AuthState = {
  accessToken: string
  refreshToken: string
  expiresAt: number
  user?: {
    id: string
    email: string
    tenantId: string
  }
}

const AUTH_KEY = 'auth'

export async function getAuth(): Promise<AuthState | null> {
  const result = await chrome.storage.local.get(AUTH_KEY)
  return (result[AUTH_KEY] as AuthState | undefined) ?? null
}

export async function setAuth(auth: AuthState | null) {
  if (!auth) {
    await chrome.storage.local.remove(AUTH_KEY)
    return
  }
  await chrome.storage.local.set({ [AUTH_KEY]: auth })
}

export async function login(email: string, password: string): Promise<AuthState> {
  const data = await apiFetch<{ access_token: string; refresh_token: string; expires_in: number }>(
    '/auth/token',
    {
      method: 'POST',
      body: JSON.stringify({ email, password })
    }
  )
  const auth: AuthState = {
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    expiresAt: Date.now() + data.expires_in * 1000
  }
  await setAuth(auth)
  return auth
}

export async function logout() {
  await setAuth(null)
}
