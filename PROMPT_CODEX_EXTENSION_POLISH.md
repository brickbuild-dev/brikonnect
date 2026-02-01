# Brikonnect Chrome Extension — Full Polish

> **Para o Agente Codex:** Melhora a Chrome Extension para uma experiência de produção completa.

---

## Estado Actual

A extensão tem estrutura básica:
- ✅ Manifest V3
- ✅ Side panel com login
- ✅ Picking sessions list
- ✅ Basic sync status
- ⚠️ Popup mínimo
- ⚠️ Background worker vazio
- ⚠️ UI básica (inline styles)
- ❌ Dark mode
- ❌ Notifications/badge
- ❌ Token refresh
- ❌ Offline indicator
- ❌ Orders lookup
- ❌ Quick actions

---

## TAREFA 1: Setup Styling (Tailwind)

### 1.1 Instalar dependências

```bash
cd apps/extension
pnpm add -D tailwindcss postcss autoprefixer
pnpm add clsx
```

### 1.2 Configurar Tailwind

Criar `tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./popup.html",
    "./sidepanel.html"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        }
      }
    },
  },
  plugins: [],
}
```

Criar `postcss.config.js`:

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

### 1.3 Criar CSS base

Criar `src/styles/globals.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --text-primary: #0f172a;
  --text-secondary: #64748b;
  --border: #e2e8f0;
}

.dark {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --border: #334155;
}

body {
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

@layer components {
  .btn {
    @apply px-3 py-2 rounded-md text-sm font-medium transition-colors;
  }
  .btn-primary {
    @apply bg-primary-600 text-white hover:bg-primary-700;
  }
  .btn-secondary {
    @apply bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700;
  }
  .input {
    @apply w-full px-3 py-2 border rounded-md text-sm bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500;
  }
  .card {
    @apply bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4;
  }
}
```

Importar em `sidepanel.html` e `popup.html`:

```html
<link rel="stylesheet" href="./src/styles/globals.css">
```

---

## TAREFA 2: Background Service Worker

Atualizar `src/background/index.ts`:

```typescript
import { getAuth, refreshToken, logout } from '../shared/auth'

// Constants
const REFRESH_ALARM = 'refresh-token'
const NOTIFICATION_ALARM = 'check-notifications'
const REFRESH_INTERVAL_MINUTES = 10
const NOTIFICATION_INTERVAL_MINUTES = 5

// On install
chrome.runtime.onInstalled.addListener(() => {
  console.log('Brikonnect extension installed')
  
  // Setup alarms
  chrome.alarms.create(REFRESH_ALARM, { periodInMinutes: REFRESH_INTERVAL_MINUTES })
  chrome.alarms.create(NOTIFICATION_ALARM, { periodInMinutes: NOTIFICATION_INTERVAL_MINUTES })
})

// Handle alarms
chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === REFRESH_ALARM) {
    await handleTokenRefresh()
  } else if (alarm.name === NOTIFICATION_ALARM) {
    await checkNotifications()
  }
})

// Token refresh
async function handleTokenRefresh() {
  try {
    const auth = await getAuth()
    if (!auth) return
    
    // Check if token expires in next 5 minutes
    const expiresAt = auth.expiresAt || 0
    const fiveMinutes = 5 * 60 * 1000
    
    if (Date.now() > expiresAt - fiveMinutes) {
      console.log('Refreshing token...')
      await refreshToken()
    }
  } catch (error) {
    console.error('Token refresh failed:', error)
    // If refresh fails, logout
    await logout()
    updateBadge('!')
  }
}

// Check notifications
async function checkNotifications() {
  try {
    const auth = await getAuth()
    if (!auth) {
      updateBadge('')
      return
    }
    
    const response = await fetch(`${getApiUrl()}/api/v1/notifications/?unread=true`, {
      headers: { 'Authorization': `Bearer ${auth.accessToken}` }
    })
    
    if (response.ok) {
      const data = await response.json()
      const count = data.length || 0
      updateBadge(count > 0 ? count.toString() : '')
      
      // Show notification for new items
      if (count > 0 && data[0]) {
        const latest = data[0]
        chrome.notifications.create({
          type: 'basic',
          iconUrl: 'icons/icon128.png',
          title: latest.title,
          message: latest.body || ''
        })
      }
    }
  } catch (error) {
    console.error('Notification check failed:', error)
  }
}

// Update badge
function updateBadge(text: string) {
  chrome.action.setBadgeText({ text })
  chrome.action.setBadgeBackgroundColor({ color: text === '!' ? '#dc2626' : '#3b82f6' })
}

// Get API URL from storage or default
function getApiUrl(): string {
  // In production, this would come from storage
  return 'http://localhost:8000'
}

// Listen for messages from popup/sidepanel
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'CHECK_NOTIFICATIONS') {
    checkNotifications().then(() => sendResponse({ success: true }))
    return true // Keep channel open for async response
  }
  
  if (message.type === 'UPDATE_BADGE') {
    updateBadge(message.text || '')
    sendResponse({ success: true })
  }
  
  if (message.type === 'GET_AUTH_STATUS') {
    getAuth().then((auth) => sendResponse({ authenticated: !!auth }))
    return true
  }
})

// Open side panel when clicking on extension icon (optional behavior)
chrome.action.onClicked.addListener((tab) => {
  if (tab.id) {
    chrome.sidePanel.open({ tabId: tab.id })
  }
})
```

---

## TAREFA 3: Shared Auth (Melhorado)

Atualizar `src/shared/auth.ts`:

```typescript
const API_URL = 'http://localhost:8000'  // TODO: Make configurable

export interface AuthState {
  accessToken: string
  refreshToken: string
  expiresAt: number
  user: {
    id: string
    email: string
    tenantId: string
    permissions: string[]
  }
}

export async function getAuth(): Promise<AuthState | null> {
  const result = await chrome.storage.local.get('auth')
  return result.auth || null
}

export async function setAuth(auth: AuthState): Promise<void> {
  await chrome.storage.local.set({ auth })
}

export async function clearAuth(): Promise<void> {
  await chrome.storage.local.remove('auth')
}

export async function login(email: string, password: string): Promise<AuthState> {
  const response = await fetch(`${API_URL}/api/v1/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Login failed' }))
    throw new Error(error.detail || 'Login failed')
  }
  
  const data = await response.json()
  
  const auth: AuthState = {
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    expiresAt: Date.now() + (data.expires_in || 900) * 1000,
    user: data.user || { id: '', email, tenantId: '', permissions: [] }
  }
  
  await setAuth(auth)
  return auth
}

export async function refreshToken(): Promise<AuthState> {
  const current = await getAuth()
  if (!current?.refreshToken) {
    throw new Error('No refresh token')
  }
  
  const response = await fetch(`${API_URL}/api/v1/auth/token/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: current.refreshToken })
  })
  
  if (!response.ok) {
    await clearAuth()
    throw new Error('Token refresh failed')
  }
  
  const data = await response.json()
  
  const auth: AuthState = {
    accessToken: data.access_token,
    refreshToken: data.refresh_token || current.refreshToken,
    expiresAt: Date.now() + (data.expires_in || 900) * 1000,
    user: current.user
  }
  
  await setAuth(auth)
  return auth
}

export async function logout(): Promise<void> {
  const auth = await getAuth()
  
  if (auth?.refreshToken) {
    try {
      await fetch(`${API_URL}/api/v1/auth/token/revoke`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${auth.accessToken}`
        },
        body: JSON.stringify({ refresh_token: auth.refreshToken })
      })
    } catch {
      // Ignore revoke errors
    }
  }
  
  await clearAuth()
  chrome.runtime.sendMessage({ type: 'UPDATE_BADGE', text: '' })
}
```

---

## TAREFA 4: Shared API Client (Melhorado)

Atualizar `src/shared/api.ts`:

```typescript
import { getAuth, refreshToken, logout } from './auth'

const API_URL = 'http://localhost:8000'

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
  token?: string
): Promise<T> {
  const auth = token ? { accessToken: token } : await getAuth()
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers
  }
  
  if (auth?.accessToken) {
    headers['Authorization'] = `Bearer ${auth.accessToken}`
  }
  
  const url = endpoint.startsWith('http') ? endpoint : `${API_URL}/api/v1${endpoint}`
  
  let response = await fetch(url, { ...options, headers })
  
  // Handle 401 - try refresh
  if (response.status === 401 && !token) {
    try {
      const newAuth = await refreshToken()
      headers['Authorization'] = `Bearer ${newAuth.accessToken}`
      response = await fetch(url, { ...options, headers })
    } catch {
      await logout()
      throw new ApiError(401, 'Session expired. Please login again.')
    }
  }
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new ApiError(response.status, error.detail || `Request failed: ${response.status}`)
  }
  
  // Handle empty response
  const text = await response.text()
  if (!text) return {} as T
  
  return JSON.parse(text)
}

// Typed API methods
export const api = {
  // Auth
  auth: {
    me: () => apiFetch<{ id: string; email: string }>('/auth/me')
  },
  
  // Orders
  orders: {
    list: (params?: { status?: string; limit?: number }) => {
      const query = new URLSearchParams(params as Record<string, string>).toString()
      return apiFetch<any[]>(`/orders${query ? `?${query}` : ''}`)
    },
    get: (id: string) => apiFetch<any>(`/orders/${id}`),
    updateStatus: (id: string, status: string) => 
      apiFetch(`/orders/${id}/status`, {
        method: 'POST',
        body: JSON.stringify({ status })
      })
  },
  
  // Picker
  picker: {
    sessions: () => apiFetch<any[]>('/picker/sessions'),
    getSession: (id: string) => apiFetch<any>(`/picker/sessions/${id}`),
    getRoute: (id: string) => apiFetch<any[]>(`/picker/sessions/${id}/route`),
    pick: (sessionId: string, data: { order_line_id: string; event_type: string; qty: number; location_code?: string }) =>
      apiFetch(`/picker/sessions/${sessionId}/pick`, {
        method: 'POST',
        body: JSON.stringify(data)
      }),
    complete: (id: string) => 
      apiFetch(`/picker/sessions/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status: 'COMPLETED' })
      })
  },
  
  // Sync
  sync: {
    runs: () => apiFetch<any[]>('/sync/runs'),
    preview: (sourceStoreId: string, targetStoreId: string) =>
      apiFetch('/sync/preview', {
        method: 'POST',
        body: JSON.stringify({
          source_store_id: sourceStoreId,
          target_store_id: targetStoreId,
          direction: 'SOURCE_TO_TARGET'
        })
      })
  },
  
  // Stores
  stores: {
    list: () => apiFetch<any[]>('/stores')
  },
  
  // Notifications
  notifications: {
    list: (unread?: boolean) => apiFetch<any[]>(`/notifications${unread ? '?unread=true' : ''}`),
    markRead: (id: string) => apiFetch(`/notifications/${id}/read`, { method: 'POST' }),
    markAllRead: () => apiFetch('/notifications/read-all', { method: 'POST' })
  },
  
  // Inventory (quick lookup)
  inventory: {
    search: (query: string) => apiFetch<any[]>(`/inventory?search=${encodeURIComponent(query)}&limit=10`)
  }
}
```

---

## TAREFA 5: Side Panel (Redesigned)

Criar estrutura de componentes:

```
src/sidepanel/
├── main.tsx
├── App.tsx
├── components/
│   ├── Header.tsx
│   ├── LoginForm.tsx
│   ├── Dashboard.tsx
│   ├── PickingSessions.tsx
│   ├── PickingRoute.tsx
│   ├── OrderLookup.tsx
│   ├── SyncStatus.tsx
│   └── Settings.tsx
└── hooks/
    ├── useAuth.ts
    └── useTheme.ts
```

### 5.1 Main entry

`src/sidepanel/main.tsx`:

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import '../styles/globals.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

### 5.2 App component

`src/sidepanel/App.tsx`:

```tsx
import React, { useEffect, useState } from 'react'
import { getAuth, AuthState } from '../shared/auth'
import Header from './components/Header'
import LoginForm from './components/LoginForm'
import Dashboard from './components/Dashboard'

type View = 'dashboard' | 'picking' | 'orders' | 'sync' | 'settings'

export default function App() {
  const [auth, setAuth] = useState<AuthState | null>(null)
  const [loading, setLoading] = useState(true)
  const [view, setView] = useState<View>('dashboard')
  const [darkMode, setDarkMode] = useState(false)

  useEffect(() => {
    // Load auth state
    getAuth().then((a) => {
      setAuth(a)
      setLoading(false)
    })
    
    // Load theme preference
    chrome.storage.local.get('darkMode').then((result) => {
      const dark = result.darkMode ?? window.matchMedia('(prefers-color-scheme: dark)').matches
      setDarkMode(dark)
      document.documentElement.classList.toggle('dark', dark)
    })
  }, [])

  const toggleDarkMode = () => {
    const newValue = !darkMode
    setDarkMode(newValue)
    document.documentElement.classList.toggle('dark', newValue)
    chrome.storage.local.set({ darkMode: newValue })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!auth) {
    return <LoginForm onLogin={setAuth} />
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header
        user={auth.user}
        view={view}
        onViewChange={setView}
        darkMode={darkMode}
        onToggleDarkMode={toggleDarkMode}
        onLogout={() => setAuth(null)}
      />
      <main className="p-4">
        <Dashboard auth={auth} view={view} onViewChange={setView} />
      </main>
    </div>
  )
}
```

### 5.3 Header component

`src/sidepanel/components/Header.tsx`:

```tsx
import React from 'react'
import { logout } from '../../shared/auth'
import { Moon, Sun, LogOut, Package, ClipboardList, RefreshCw, Settings } from 'lucide-react'

interface Props {
  user: { email: string }
  view: string
  onViewChange: (view: any) => void
  darkMode: boolean
  onToggleDarkMode: () => void
  onLogout: () => void
}

export default function Header({ user, view, onViewChange, darkMode, onToggleDarkMode, onLogout }: Props) {
  const handleLogout = async () => {
    await logout()
    onLogout()
  }

  const navItems = [
    { id: 'dashboard', icon: Package, label: 'Dashboard' },
    { id: 'picking', icon: ClipboardList, label: 'Picking' },
    { id: 'sync', icon: RefreshCw, label: 'Sync' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ]

  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">B</span>
          </div>
          <span className="font-semibold text-gray-900 dark:text-white">Brikonnect</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onToggleDarkMode}
            className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
          <button
            onClick={handleLogout}
            className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Navigation */}
      <nav className="flex px-2 pb-2 gap-1">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onViewChange(item.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              view === item.id
                ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
                : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'
            }`}
          >
            <item.icon className="w-4 h-4" />
            {item.label}
          </button>
        ))}
      </nav>
    </header>
  )
}
```

### 5.4 Login Form

`src/sidepanel/components/LoginForm.tsx`:

```tsx
import React, { useState } from 'react'
import { login, AuthState } from '../../shared/auth'

interface Props {
  onLogin: (auth: AuthState) => void
}

export default function LoginForm({ onLogin }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    
    try {
      const auth = await login(email, password)
      onLogin(auth)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50 dark:bg-gray-900">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-white font-bold text-2xl">B</span>
          </div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">Brikonnect</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Sign in to start picking</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              placeholder="you@example.com"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              placeholder="••••••••"
              required
            />
          </div>

          {error && (
            <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-3 rounded-md">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary w-full"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
```

### 5.5 Dashboard

`src/sidepanel/components/Dashboard.tsx`:

```tsx
import React from 'react'
import { AuthState } from '../../shared/auth'
import PickingSessions from './PickingSessions'
import SyncStatus from './SyncStatus'
import OrderLookup from './OrderLookup'

interface Props {
  auth: AuthState
  view: string
  onViewChange: (view: string) => void
}

export default function Dashboard({ auth, view, onViewChange }: Props) {
  if (view === 'picking') {
    return <PickingSessions auth={auth} />
  }
  
  if (view === 'sync') {
    return <SyncStatus auth={auth} />
  }
  
  if (view === 'settings') {
    return <SettingsView />
  }
  
  // Dashboard view
  return (
    <div className="space-y-4">
      {/* Quick Order Lookup */}
      <OrderLookup auth={auth} />
      
      {/* Active Picking */}
      <div className="card">
        <h3 className="font-medium text-gray-900 dark:text-white mb-3">Active Picking</h3>
        <PickingSessionsCompact auth={auth} onViewAll={() => onViewChange('picking')} />
      </div>
      
      {/* Sync Status */}
      <div className="card">
        <h3 className="font-medium text-gray-900 dark:text-white mb-3">Sync Status</h3>
        <SyncStatusCompact auth={auth} onViewAll={() => onViewChange('sync')} />
      </div>
    </div>
  )
}

function SettingsView() {
  const [apiUrl, setApiUrl] = React.useState('http://localhost:8000')
  
  React.useEffect(() => {
    chrome.storage.local.get('apiUrl').then((result) => {
      if (result.apiUrl) setApiUrl(result.apiUrl)
    })
  }, [])
  
  const saveApiUrl = () => {
    chrome.storage.local.set({ apiUrl })
  }
  
  return (
    <div className="card">
      <h3 className="font-medium text-gray-900 dark:text-white mb-4">Settings</h3>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            API URL
          </label>
          <input
            type="url"
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            className="input"
          />
        </div>
        
        <button onClick={saveApiUrl} className="btn btn-primary">
          Save
        </button>
      </div>
    </div>
  )
}

function PickingSessionsCompact({ auth, onViewAll }: { auth: AuthState; onViewAll: () => void }) {
  const [sessions, setSessions] = React.useState<any[]>([])
  
  React.useEffect(() => {
    import('../../shared/api').then(({ api }) => {
      api.picker.sessions().then(setSessions).catch(console.error)
    })
  }, [])
  
  const active = sessions.filter((s) => s.status === 'ACTIVE' || s.status === 'DRAFT')
  
  if (active.length === 0) {
    return <p className="text-sm text-gray-500">No active sessions</p>
  }
  
  return (
    <div>
      {active.slice(0, 2).map((session) => (
        <div key={session.id} className="py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
          <div className="flex justify-between">
            <span className="text-sm font-medium">{session.total_orders} orders</span>
            <span className="text-xs text-gray-500">{session.picked_items}/{session.total_items} picked</span>
          </div>
        </div>
      ))}
      {active.length > 2 && (
        <button onClick={onViewAll} className="text-sm text-primary-600 mt-2">
          View all ({active.length})
        </button>
      )}
    </div>
  )
}

function SyncStatusCompact({ auth, onViewAll }: { auth: AuthState; onViewAll: () => void }) {
  const [runs, setRuns] = React.useState<any[]>([])
  
  React.useEffect(() => {
    import('../../shared/api').then(({ api }) => {
      api.sync.runs().then(setRuns).catch(console.error)
    })
  }, [])
  
  const latest = runs[0]
  
  if (!latest) {
    return <p className="text-sm text-gray-500">No sync runs yet</p>
  }
  
  return (
    <div>
      <div className="flex justify-between items-center">
        <span className="text-sm">{latest.status}</span>
        {latest.plan_summary && (
          <span className="text-xs text-gray-500">
            +{latest.plan_summary.add} / ~{latest.plan_summary.update} / -{latest.plan_summary.remove}
          </span>
        )}
      </div>
      <button onClick={onViewAll} className="text-sm text-primary-600 mt-2">
        View history
      </button>
    </div>
  )
}
```

### 5.6 Order Lookup

`src/sidepanel/components/OrderLookup.tsx`:

```tsx
import React, { useState } from 'react'
import { AuthState } from '../../shared/auth'
import { api } from '../../shared/api'
import { Search } from 'lucide-react'

interface Props {
  auth: AuthState
}

export default function OrderLookup({ auth }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const orders = await api.orders.list({ limit: 5 })
      // Filter by query (order number or buyer)
      const filtered = orders.filter(
        (o: any) =>
          o.external_order_id?.toLowerCase().includes(query.toLowerCase()) ||
          o.buyer_name?.toLowerCase().includes(query.toLowerCase())
      )
      setResults(filtered)
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h3 className="font-medium text-gray-900 dark:text-white mb-3">Quick Order Lookup</h3>
      
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="input flex-1"
          placeholder="Order # or buyer name"
        />
        <button onClick={handleSearch} disabled={loading} className="btn btn-primary">
          <Search className="w-4 h-4" />
        </button>
      </div>

      {results.length > 0 && (
        <div className="mt-3 space-y-2">
          {results.map((order) => (
            <div
              key={order.id}
              className="p-2 bg-gray-50 dark:bg-gray-700 rounded-md text-sm"
            >
              <div className="flex justify-between">
                <span className="font-medium">#{order.external_order_id}</span>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  order.status === 'SHIPPED' ? 'bg-green-100 text-green-800' :
                  order.status === 'PICKING' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {order.status}
                </span>
              </div>
              <div className="text-gray-500 text-xs mt-1">{order.buyer_name}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

---

## TAREFA 6: Popup (Quick Actions)

Atualizar `src/popup/main.tsx`:

```tsx
import React, { useEffect, useState } from 'react'
import ReactDOM from 'react-dom/client'
import { getAuth, logout, AuthState } from '../shared/auth'
import { api } from '../shared/api'
import '../styles/globals.css'

function PopupApp() {
  const [auth, setAuth] = useState<AuthState | null>(null)
  const [loading, setLoading] = useState(true)
  const [notifications, setNotifications] = useState<any[]>([])

  useEffect(() => {
    getAuth().then((a) => {
      setAuth(a)
      setLoading(false)
      if (a) {
        api.notifications.list(true).then(setNotifications).catch(console.error)
      }
    })
  }, [])

  const handleLogout = async () => {
    await logout()
    setAuth(null)
    window.close()
  }

  const openSidePanel = () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]?.id) {
        chrome.sidePanel.open({ tabId: tabs[0].id })
        window.close()
      }
    })
  }

  if (loading) {
    return (
      <div className="w-64 p-4 flex justify-center">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!auth) {
    return (
      <div className="w-64 p-4">
        <h1 className="text-lg font-semibold text-gray-900">Brikonnect</h1>
        <p className="text-sm text-gray-500 mt-1">Sign in from the side panel</p>
        <button onClick={openSidePanel} className="btn btn-primary w-full mt-4">
          Open Side Panel
        </button>
      </div>
    )
  }

  return (
    <div className="w-72 p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">Brikonnect</h1>
          <p className="text-xs text-gray-500">{auth.user.email}</p>
        </div>
        <button onClick={handleLogout} className="text-xs text-gray-500 hover:text-gray-700">
          Logout
        </button>
      </div>

      {/* Notifications */}
      {notifications.length > 0 && (
        <div className="mb-4">
          <h2 className="text-sm font-medium text-gray-700 mb-2">
            Notifications ({notifications.length})
          </h2>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {notifications.slice(0, 3).map((n) => (
              <div key={n.id} className="text-xs p-2 bg-gray-50 rounded">
                <div className="font-medium">{n.title}</div>
                {n.body && <div className="text-gray-500">{n.body}</div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="space-y-2">
        <button onClick={openSidePanel} className="btn btn-primary w-full">
          Open Picking
        </button>
        <QuickStatusButtons auth={auth} />
      </div>
    </div>
  )
}

function QuickStatusButtons({ auth }: { auth: AuthState }) {
  const [recentOrder, setRecentOrder] = useState<any>(null)

  useEffect(() => {
    api.orders.list({ status: 'NEW', limit: 1 }).then((orders) => {
      if (orders.length > 0) setRecentOrder(orders[0])
    }).catch(console.error)
  }, [])

  if (!recentOrder) return null

  const updateStatus = async (status: string) => {
    try {
      await api.orders.updateStatus(recentOrder.id, status)
      setRecentOrder(null)
    } catch (error) {
      console.error('Failed to update status:', error)
    }
  }

  return (
    <div className="border-t pt-3 mt-3">
      <div className="text-xs text-gray-500 mb-2">
        Quick: #{recentOrder.external_order_id}
      </div>
      <div className="flex gap-2">
        <button onClick={() => updateStatus('PICKING')} className="btn btn-secondary flex-1 text-xs">
          Start Pick
        </button>
        <button onClick={() => updateStatus('PACKING')} className="btn btn-secondary flex-1 text-xs">
          Packing
        </button>
      </div>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <PopupApp />
  </React.StrictMode>
)
```

---

## TAREFA 7: Adicionar Icons

### 7.1 Instalar lucide-react

```bash
cd apps/extension
pnpm add lucide-react
```

### 7.2 Criar icons para extension

Criar pasta `public/icons/` com:
- icon16.png
- icon48.png
- icon128.png

Atualizar `manifest.json`:

```json
{
  "manifest_version": 3,
  "name": "Brikonnect",
  "version": "1.0.0",
  "description": "Brikonnect picking and inventory management companion",
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "permissions": ["storage", "sidePanel", "notifications", "alarms"],
  "host_permissions": ["https://api.brikonnect.com/*", "http://localhost:8000/*"],
  "action": {
    "default_title": "Brikonnect",
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png"
    }
  },
  "side_panel": {
    "default_path": "sidepanel.html"
  },
  "background": {
    "service_worker": "src/background/index.ts",
    "type": "module"
  }
}
```

---

## TAREFA 8: Atualizar HTML files

### sidepanel.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Brikonnect</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="./src/sidepanel/main.tsx"></script>
</body>
</html>
```

### popup.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Brikonnect</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="./src/popup/main.tsx"></script>
</body>
</html>
```

---

## TAREFA 9: Testes Manuais

Após implementar, testar:

1. **Build**: `pnpm build`
2. **Load em Chrome**: chrome://extensions → Load unpacked → dist/
3. **Login**: Verificar que funciona
4. **Dark mode**: Toggle funciona
5. **Picking**: Sessions aparecem, pick funciona
6. **Notifications**: Badge atualiza
7. **Popup**: Quick actions funcionam

---

## Checklist Final

- [ ] Tailwind configurado e a funcionar
- [ ] Background worker com token refresh
- [ ] Notifications com badge
- [ ] Side panel com UI polida
- [ ] Dark mode toggle
- [ ] Order lookup funciona
- [ ] Picking flow completo
- [ ] Popup com quick actions
- [ ] Icons criados
- [ ] Build sem erros

---

## Commits

1. `feat(extension): setup Tailwind CSS`
2. `feat(extension): improve background service worker`
3. `feat(extension): redesign side panel UI`
4. `feat(extension): add popup quick actions`
5. `feat(extension): add notifications and badge`
6. `chore(extension): update manifest and icons`

Push quando completo.
