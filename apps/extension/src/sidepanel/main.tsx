import React, { useEffect, useMemo, useState } from 'react'
import ReactDOM from 'react-dom/client'
import clsx from 'clsx'
import {
  Bell,
  CheckCircle2,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Moon,
  PackageCheck,
  RefreshCcw,
  Search,
  Settings,
  Sun
} from 'lucide-react'

import { apiFetch, getApiBaseUrl, setApiBaseUrl } from '../shared/api'
import { AuthState, getAuth, login, logout, refreshAuth } from '../shared/auth'
import { applyTheme, getStoredTheme, setStoredTheme, Theme } from '../shared/theme'
import '../styles/index.css'

type PickSession = {
  id: string
  status: string
  total_orders: number
  total_items: number
  picked_items: number
}

type RouteItem = {
  order_line_id: string
  order_id: string
  item_no: string
  qty_ordered: number
  location_code?: string | null
}

type Store = {
  id: string
  name: string
  channel: string
  is_primary: boolean
}

type SyncRun = {
  id: string
  status: string
  plan_summary?: { add: number; update: number; remove: number }
  created_at?: string
}

type Order = {
  id: string
  external_order_id: string
  status: string
  buyer_name?: string | null
  grand_total?: string | null
}

type NotificationItem = {
  id: string
  title: string
  body?: string | null
  read_at?: string | null
  dismissed_at?: string | null
  created_at?: string | null
}

type TabKey = 'dashboard' | 'orders' | 'picking' | 'sync' | 'settings'

const statusOptions = ['PENDING', 'PICKING', 'PACKING', 'READY', 'SHIPPED', 'DELIVERED', 'COMPLETED']

function SidePanelApp() {
  const [auth, setAuth] = useState<AuthState | null>(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [activeTab, setActiveTab] = useState<TabKey>('dashboard')
  const [theme, setTheme] = useState<Theme>(() => getStoredTheme())
  const [sessions, setSessions] = useState<PickSession[]>([])
  const [selectedSession, setSelectedSession] = useState<PickSession | null>(null)
  const [routeItems, setRouteItems] = useState<RouteItem[]>([])
  const [pickedLines, setPickedLines] = useState<string[]>([])
  const [stores, setStores] = useState<Store[]>([])
  const [syncRuns, setSyncRuns] = useState<SyncRun[]>([])
  const [syncStatus, setSyncStatus] = useState<string | null>(null)
  const [orders, setOrders] = useState<Order[]>([])
  const [orderQuery, setOrderQuery] = useState('')
  const [orderStatus, setOrderStatus] = useState('READY')
  const [orderError, setOrderError] = useState<string | null>(null)
  const [orderLoading, setOrderLoading] = useState(false)
  const [notifications, setNotifications] = useState<NotificationItem[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [apiBaseUrl, setApiBaseUrlState] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    void getAuth().then(setAuth)
    void getApiBaseUrl().then(setApiBaseUrlState)
  }, [])

  useEffect(() => {
    setStoredTheme(theme)
  }, [theme])

  useEffect(() => {
    applyTheme(theme)
    if (theme !== 'system') return
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = () => applyTheme(theme)
    media.addEventListener('change', handleChange)
    return () => media.removeEventListener('change', handleChange)
  }, [theme])

  useEffect(() => {
    chrome.storage.local.get('unreadCount').then((result) => {
      if (typeof result.unreadCount === 'number') {
        setUnreadCount(result.unreadCount)
      }
    })
    const listener: typeof chrome.storage.onChanged.addListener = (changes, areaName) => {
      if (areaName === 'local' && changes.unreadCount) {
        setUnreadCount(changes.unreadCount.newValue ?? 0)
      }
    }
    chrome.storage.onChanged.addListener(listener)
    return () => chrome.storage.onChanged.removeListener(listener)
  }, [])

  useEffect(() => {
    if (!auth) return
    void loadAll()
  }, [auth])

  const navItems = [
    { id: 'dashboard' as const, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'orders' as const, label: 'Orders', icon: Search },
    { id: 'picking' as const, label: 'Picking', icon: PackageCheck },
    { id: 'sync' as const, label: 'Sync', icon: RefreshCcw },
    { id: 'settings' as const, label: 'Settings', icon: Settings }
  ]

  const unreadNotifications = useMemo(
    () => notifications.filter((item) => !item.read_at && !item.dismissed_at),
    [notifications]
  )

  const stats = useMemo(() => {
    const activeSessions = sessions.filter(
      (session) => session.status !== 'COMPLETED' && session.status !== 'CANCELLED'
    )
    const totalPicked = sessions.reduce((sum, session) => sum + session.picked_items, 0)
    const totalItems = sessions.reduce((sum, session) => sum + session.total_items, 0)
    return {
      activeSessions: activeSessions.length,
      pickedProgress: totalItems ? Math.round((totalPicked / totalItems) * 100) : 0,
      unreadNotifications: unreadCount,
      lastSync: syncRuns[0]?.status ?? 'None'
    }
  }, [sessions, syncRuns, unreadCount])

  const handleLogin = async () => {
    setError(null)
    setLoading(true)
    try {
      const authState = await login(email, password)
      setAuth(authState)
      setActiveTab('dashboard')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    await logout()
    setAuth(null)
    setSessions([])
    setSelectedSession(null)
    setRouteItems([])
    setStores([])
    setSyncRuns([])
    setSyncStatus(null)
    setOrders([])
    setNotifications([])
    setUnreadCount(0)
  }

  const getToken = async () => {
    const refreshed = await refreshAuth()
    if (!refreshed) {
      setAuth(null)
      return null
    }
    setAuth(refreshed)
    return refreshed.accessToken
  }

  const loadAll = async () => {
    const token = await getToken()
    if (!token) return
    await Promise.all([loadSessions(token), loadStores(token), loadSyncRuns(token), loadNotifications(token)])
  }

  const loadSessions = async (token: string) => {
    const data = await apiFetch<PickSession[]>('/picker/sessions', {}, token)
    setSessions(data)
  }

  const loadStores = async (token: string) => {
    const data = await apiFetch<Store[]>('/stores', {}, token)
    setStores(data)
  }

  const loadSyncRuns = async (token: string) => {
    const data = await apiFetch<SyncRun[]>('/sync/runs', {}, token)
    setSyncRuns(data)
  }

  const loadNotifications = async (token: string) => {
    const data = await apiFetch<NotificationItem[]>('/notifications', {}, token)
    setNotifications(data)
    setUnreadCount(data.filter((item) => !item.read_at && !item.dismissed_at).length)
  }

  const refreshSessions = async () => {
    const token = await getToken()
    if (!token) return
    await loadSessions(token)
  }

  const refreshNotifications = async () => {
    const token = await getToken()
    if (!token) return
    await loadNotifications(token)
  }

  const loadRoute = async (session: PickSession, token: string) => {
    const data = await apiFetch<RouteItem[]>(`/picker/sessions/${session.id}/route`, {}, token)
    setSelectedSession(session)
    setRouteItems(data)
    setPickedLines([])
  }

  const handleSelectSession = async (session: PickSession) => {
    const token = await getToken()
    if (!token) return
    await loadRoute(session, token)
  }

  const handlePick = async (item: RouteItem, token: string, eventType: 'PICKED' | 'MISSING') => {
    await apiFetch(
      `/picker/sessions/${selectedSession?.id}/pick`,
      {
        method: 'POST',
        body: JSON.stringify({
          order_line_id: item.order_line_id,
          event_type: eventType,
          qty: item.qty_ordered,
          location_code: item.location_code
        })
      },
      token
    )
    setPickedLines((prev) => (prev.includes(item.order_line_id) ? prev : [...prev, item.order_line_id]))
    await loadSessions(token)
  }

  const handlePickAction = async (item: RouteItem, eventType: 'PICKED' | 'MISSING') => {
    const token = await getToken()
    if (!token) return
    await handlePick(item, token, eventType)
  }

  const handleUpdateSession = async (status: string) => {
    if (!selectedSession) return
    const token = await getToken()
    if (!token) return
    await apiFetch(
      `/picker/sessions/${selectedSession.id}`,
      {
        method: 'PATCH',
        body: JSON.stringify({ status })
      },
      token
    )
    await loadSessions(token)
    const updated = await apiFetch<PickSession>(`/picker/sessions/${selectedSession.id}`, {}, token)
    setSelectedSession(updated)
  }

  const handleQuickSync = async () => {
    const token = await getToken()
    if (!token) return
    setSyncStatus(null)
    const source = stores.find((store) => store.is_primary) ?? stores[0]
    const target = stores.find((store) => store.id !== source?.id)
    if (!source || !target) {
      setSyncStatus('Add at least two stores to sync.')
      return
    }
    try {
      const response = await apiFetch<{ run: SyncRun }>(
        '/sync/preview',
        {
          method: 'POST',
          body: JSON.stringify({
            source_store_id: source.id,
            target_store_id: target.id,
            direction: 'SOURCE_TO_TARGET'
          })
        },
        token
      )
      setSyncStatus(`Preview ${response.run.status.toLowerCase()}`)
      await loadSyncRuns(token)
    } catch (err) {
      setSyncStatus((err as Error).message)
    }
  }

  const handleOrderSearch = async () => {
    const token = await getToken()
    if (!token) return
    setOrderError(null)
    setOrderLoading(true)
    try {
      const data = await apiFetch<Order[]>(
        `/orders?q=${encodeURIComponent(orderQuery.trim())}`,
        {},
        token
      )
      setOrders(data)
    } catch (err) {
      setOrderError((err as Error).message)
    } finally {
      setOrderLoading(false)
    }
  }

  const handleOrderStatusUpdate = async (orderId: string) => {
    const token = await getToken()
    if (!token) return
    setOrderError(null)
    try {
      await apiFetch(
        `/orders/${orderId}/status`,
        {
          method: 'POST',
          body: JSON.stringify({ status: orderStatus, notes: 'Updated from Brikonnect extension.' })
        },
        token
      )
      await handleOrderSearch()
    } catch (err) {
      setOrderError((err as Error).message)
    }
  }

  const handleSaveSettings = async () => {
    if (!apiBaseUrl.trim()) return
    await setApiBaseUrl(apiBaseUrl.trim())
  }

  if (!auth) {
    return (
      <div className="flex h-full flex-col gap-6 p-6">
        <div>
          <div className="text-xl font-semibold">Brikonnect</div>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Sign in to manage picking and sync.
          </p>
        </div>
        <div className="panel-card space-y-3">
          <div>
            <label className="panel-label">Email</label>
            <input
              className="panel-input mt-2"
              placeholder="you@store.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>
          <div>
            <label className="panel-label">Password</label>
            <input
              className="panel-input mt-2"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>
          {error ? <p className="text-xs text-rose-500">{error}</p> : null}
          <button className="panel-button w-full" onClick={() => void handleLogin()} disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-slate-200 bg-white px-4 py-4 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-lg font-semibold">Brikonnect</div>
            <div className="text-xs text-slate-500 dark:text-slate-400">{auth.user?.email ?? 'Signed in'}</div>
          </div>
          <button
            className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
            onClick={() => void handleLogout()}
          >
            <LogOut className="h-4 w-4" /> Logout
          </button>
        </div>
        <nav className="mt-4 flex gap-2 overflow-x-auto">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <button
                key={item.id}
                className={clsx(
                  'inline-flex items-center gap-2 rounded-full px-3 py-2 text-xs font-semibold transition',
                  activeTab === item.id
                    ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900'
                    : 'bg-slate-100 text-slate-500 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300'
                )}
                onClick={() => setActiveTab(item.id)}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </button>
            )
          })}
        </nav>
      </header>

      <main className="flex-1 space-y-6 overflow-y-auto p-4">
        {activeTab === 'dashboard' ? (
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="panel-card">
                <div className="panel-label">Active sessions</div>
                <div className="mt-2 text-2xl font-semibold">{stats.activeSessions}</div>
                <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  {stats.pickedProgress}% items picked
                </div>
              </div>
              <div className="panel-card">
                <div className="panel-label">Unread alerts</div>
                <div className="mt-2 flex items-center gap-2 text-2xl font-semibold">
                  <Bell className="h-5 w-5 text-amber-500" />
                  {stats.unreadNotifications}
                </div>
                <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  Latest sync: {stats.lastSync}
                </div>
              </div>
            </div>

            <div className="panel-card">
              <div className="flex items-center justify-between">
                <div className="text-sm font-semibold">Notifications</div>
                <button
                  className="text-xs font-semibold text-slate-500 hover:text-slate-900 dark:text-slate-400"
                  onClick={() => void refreshNotifications()}
                >
                  Refresh
                </button>
              </div>
              <div className="mt-3 space-y-3">
                {unreadNotifications.slice(0, 4).map((notification) => (
                  <div key={notification.id} className="rounded-lg border border-slate-200 p-3 text-sm dark:border-slate-800">
                    <div className="font-semibold text-slate-900 dark:text-slate-100">
                      {notification.title}
                    </div>
                    <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      {notification.body ?? 'New update'}
                    </div>
                  </div>
                ))}
                {unreadNotifications.length === 0 ? (
                  <p className="text-xs text-slate-500 dark:text-slate-400">No unread notifications.</p>
                ) : null}
              </div>
            </div>
          </div>
        ) : null}

        {activeTab === 'orders' ? (
          <div className="space-y-4">
            <div className="panel-card space-y-3">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Search className="h-4 w-4" /> Order lookup
              </div>
              <input
                className="panel-input"
                placeholder="Search by order ID, buyer, or email"
                value={orderQuery}
                onChange={(event) => setOrderQuery(event.target.value)}
              />
              <button className="panel-button" onClick={() => void handleOrderSearch()} disabled={orderLoading}>
                {orderLoading ? 'Searching...' : 'Search orders'}
              </button>
              {orderError ? <p className="text-xs text-rose-500">{orderError}</p> : null}
            </div>

            <div className="panel-card space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <select className="panel-input max-w-[180px]" value={orderStatus} onChange={(e) => setOrderStatus(e.target.value)}>
                  {statusOptions.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  Select status to apply
                </span>
              </div>
              <div className="space-y-3">
                {orders.map((order) => (
                  <div key={order.id} className="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
                    <div className="flex items-center justify-between text-sm">
                      <div className="font-semibold text-slate-900 dark:text-slate-100">
                        {order.external_order_id}
                      </div>
                      <span className="text-xs text-slate-500 dark:text-slate-400">{order.status}</span>
                    </div>
                    <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      {order.buyer_name ?? 'Unknown buyer'}
                    </div>
                    <button className="panel-button mt-3" onClick={() => void handleOrderStatusUpdate(order.id)}>
                      <CheckCircle2 className="h-4 w-4" /> Update status
                    </button>
                  </div>
                ))}
                {orders.length === 0 ? (
                  <p className="text-xs text-slate-500 dark:text-slate-400">Search for an order to begin.</p>
                ) : null}
              </div>
            </div>
          </div>
        ) : null}

        {activeTab === 'picking' ? (
          <div className="space-y-4">
            <div className="panel-card">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <ClipboardList className="h-4 w-4" /> Picking sessions
                </div>
                <button className="text-xs font-semibold text-slate-500 hover:text-slate-900 dark:text-slate-400" onClick={() => void refreshSessions()}>
                  Refresh
                </button>
              </div>
              <div className="mt-3 space-y-3">
                {sessions.map((session) => (
                  <button
                    key={session.id}
                    className={clsx(
                      'w-full rounded-lg border p-3 text-left transition',
                      selectedSession?.id === session.id
                        ? 'border-slate-900 bg-slate-900/5 dark:border-slate-100 dark:bg-slate-100/10'
                        : 'border-slate-200 hover:border-slate-300 dark:border-slate-800'
                    )}
                    onClick={() => void handleSelectSession(session)}
                  >
                    <div className="flex items-center justify-between text-sm font-semibold">
                      <span>{session.status}</span>
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        {session.picked_items}/{session.total_items}
                      </span>
                    </div>
                    <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      {session.total_orders} orders · {session.total_items} items
                    </div>
                  </button>
                ))}
                {sessions.length === 0 ? (
                  <p className="text-xs text-slate-500 dark:text-slate-400">No sessions yet.</p>
                ) : null}
              </div>
            </div>

            {selectedSession ? (
              <div className="panel-card space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-semibold">Session progress</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      {selectedSession.picked_items}/{selectedSession.total_items} items picked
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <button className="panel-button" onClick={() => void handleUpdateSession('ACTIVE')}>
                      Start
                    </button>
                    <button className="panel-button" onClick={() => void handleUpdateSession('COMPLETED')}>
                      Complete
                    </button>
                  </div>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-200 dark:bg-slate-800">
                  <div
                    className="h-2 rounded-full bg-emerald-500"
                    style={{
                      width: `${Math.min(
                        100,
                        selectedSession.total_items
                          ? (selectedSession.picked_items / selectedSession.total_items) * 100
                          : 0
                      )}%`
                    }}
                  />
                </div>
                <div className="space-y-3">
                  {routeItems.map((item) => {
                    const picked = pickedLines.includes(item.order_line_id)
                    return (
                      <div
                        key={item.order_line_id}
                        className={clsx(
                          'rounded-lg border p-3 text-sm',
                          picked ? 'border-emerald-400 bg-emerald-50/60 dark:border-emerald-500/40' : 'border-slate-200 dark:border-slate-800'
                        )}
                      >
                        <div className="flex items-center justify-between font-semibold">
                          <span>{item.item_no}</span>
                          <span className="text-xs text-slate-500 dark:text-slate-400">
                            Qty {item.qty_ordered}
                          </span>
                        </div>
                        <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                          Location: {item.location_code ?? 'Unassigned'}
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2">
                          <button
                            className="panel-button"
                            onClick={() => void handlePickAction(item, 'PICKED')}
                          >
                            Picked
                          </button>
                          <button
                            className="inline-flex items-center justify-center rounded-md border border-rose-200 px-3 py-2 text-xs font-semibold text-rose-600 transition hover:bg-rose-50 dark:border-rose-500/40 dark:text-rose-300"
                            onClick={() => void handlePickAction(item, 'MISSING')}
                          >
                            Missing
                          </button>
                        </div>
                      </div>
                    )
                  })}
                  {routeItems.length === 0 ? (
                    <p className="text-xs text-slate-500 dark:text-slate-400">Select a session to see route items.</p>
                  ) : null}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}

        {activeTab === 'sync' ? (
          <div className="space-y-4">
            <div className="panel-card space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <RefreshCcw className="h-4 w-4" /> Sync status
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                {syncRuns[0]
                  ? `Latest: ${syncRuns[0].status} (add ${syncRuns[0].plan_summary?.add ?? 0})`
                  : 'No sync runs yet.'}
              </div>
              <button className="panel-button" onClick={() => void handleQuickSync()}>
                Run quick preview
              </button>
              {syncStatus ? <p className="text-xs text-emerald-600">{syncStatus}</p> : null}
            </div>

            <div className="panel-card space-y-3">
              <div className="text-sm font-semibold">Stores</div>
              <div className="space-y-2 text-xs text-slate-500 dark:text-slate-400">
                {stores.map((store) => (
                  <div key={store.id} className="flex items-center justify-between">
                    <span>
                      {store.name} · {store.channel}
                    </span>
                    {store.is_primary ? (
                      <span className="rounded-full bg-emerald-100 px-2 py-1 text-[10px] font-semibold text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200">
                        Primary
                      </span>
                    ) : null}
                  </div>
                ))}
                {stores.length === 0 ? <p>No stores configured.</p> : null}
              </div>
            </div>

            <div className="panel-card space-y-3">
              <div className="text-sm font-semibold">Recent runs</div>
              <div className="space-y-2">
                {syncRuns.slice(0, 3).map((run) => (
                  <div key={run.id} className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                    <span>{run.status}</span>
                    <span>{run.plan_summary?.add ?? 0} adds</span>
                  </div>
                ))}
                {syncRuns.length === 0 ? (
                  <p className="text-xs text-slate-500 dark:text-slate-400">No runs yet.</p>
                ) : null}
              </div>
            </div>
          </div>
        ) : null}

        {activeTab === 'settings' ? (
          <div className="space-y-4">
            <div className="panel-card space-y-3">
              <div className="text-sm font-semibold">Theme</div>
              <div className="flex items-center gap-2">
                <button
                  className={clsx(
                    'inline-flex items-center gap-2 rounded-md border px-3 py-2 text-xs font-semibold',
                    theme === 'light'
                      ? 'border-slate-900 bg-slate-900 text-white dark:border-slate-100 dark:bg-slate-100 dark:text-slate-900'
                      : 'border-slate-200 text-slate-500 dark:border-slate-700 dark:text-slate-300'
                  )}
                  onClick={() => setTheme('light')}
                >
                  <Sun className="h-4 w-4" /> Light
                </button>
                <button
                  className={clsx(
                    'inline-flex items-center gap-2 rounded-md border px-3 py-2 text-xs font-semibold',
                    theme === 'dark'
                      ? 'border-slate-900 bg-slate-900 text-white dark:border-slate-100 dark:bg-slate-100 dark:text-slate-900'
                      : 'border-slate-200 text-slate-500 dark:border-slate-700 dark:text-slate-300'
                  )}
                  onClick={() => setTheme('dark')}
                >
                  <Moon className="h-4 w-4" /> Dark
                </button>
                <button
                  className={clsx(
                    'inline-flex items-center gap-2 rounded-md border px-3 py-2 text-xs font-semibold',
                    theme === 'system'
                      ? 'border-slate-900 bg-slate-900 text-white dark:border-slate-100 dark:bg-slate-100 dark:text-slate-900'
                      : 'border-slate-200 text-slate-500 dark:border-slate-700 dark:text-slate-300'
                  )}
                  onClick={() => setTheme('system')}
                >
                  <Settings className="h-4 w-4" /> System
                </button>
              </div>
            </div>

            <div className="panel-card space-y-3">
              <div className="text-sm font-semibold">API base URL</div>
              <input
                className="panel-input"
                value={apiBaseUrl}
                onChange={(event) => setApiBaseUrlState(event.target.value)}
              />
              <button className="panel-button" onClick={() => void handleSaveSettings()}>
                Save settings
              </button>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Current: {apiBaseUrl}
              </p>
            </div>

            <div className="panel-card space-y-2">
              <div className="text-sm font-semibold">Notifications</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                Unread: {unreadCount}
              </div>
              <button
                className="panel-button"
                  onClick={() => void refreshNotifications()}
              >
                Refresh notifications
              </button>
            </div>
          </div>
        ) : null}
      </main>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <SidePanelApp />
  </React.StrictMode>
)
