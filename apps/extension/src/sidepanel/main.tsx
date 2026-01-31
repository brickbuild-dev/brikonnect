import React, { useEffect, useState } from 'react'
import ReactDOM from 'react-dom/client'

import { apiFetch } from '../shared/api'
import { AuthState, getAuth, login, logout } from '../shared/auth'

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
}

function SidePanelApp() {
  const [auth, setAuth] = useState<AuthState | null>(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [sessions, setSessions] = useState<PickSession[]>([])
  const [selectedSession, setSelectedSession] = useState<PickSession | null>(null)
  const [routeItems, setRouteItems] = useState<RouteItem[]>([])
  const [stores, setStores] = useState<Store[]>([])
  const [syncRuns, setSyncRuns] = useState<SyncRun[]>([])
  const [syncStatus, setSyncStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    void getAuth().then(setAuth)
  }, [])

  useEffect(() => {
    if (!auth) return
    void loadSessions(auth.accessToken)
    void loadStores(auth.accessToken)
    void loadSyncRuns(auth.accessToken)
  }, [auth])

  const handleLogin = async () => {
    setError(null)
    try {
      const authState = await login(email, password)
      setAuth(authState)
      await loadSessions(authState.accessToken)
      await loadStores(authState.accessToken)
      await loadSyncRuns(authState.accessToken)
    } catch (err) {
      setError((err as Error).message)
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

  const loadRoute = async (session: PickSession, token: string) => {
    const data = await apiFetch<RouteItem[]>(`/picker/sessions/${session.id}/route`, {}, token)
    setSelectedSession(session)
    setRouteItems(data)
  }

  const handlePick = async (item: RouteItem, token: string) => {
    await apiFetch(
      `/picker/sessions/${selectedSession?.id}/pick`,
      {
        method: 'POST',
        body: JSON.stringify({
          order_line_id: item.order_line_id,
          event_type: 'PICKED',
          qty: item.qty_ordered,
          location_code: item.location_code
        })
      },
      token
    )
  }

  const handleQuickSync = async () => {
    if (!auth) return
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
        auth.accessToken
      )
      setSyncStatus(`Preview ${response.run.status.toLowerCase()}`)
      await loadSyncRuns(auth.accessToken)
    } catch (err) {
      setSyncStatus((err as Error).message)
    }
  }

  if (!auth) {
    return (
      <div style={{ padding: 16, fontFamily: 'sans-serif' }}>
        <h1 style={{ fontSize: 16, fontWeight: 600 }}>Brikonnect</h1>
        <p style={{ fontSize: 12, color: '#64748b' }}>Sign in to start picking.</p>
        <div style={{ marginTop: 12 }}>
          <input
            style={{ width: '100%', padding: 8, marginBottom: 8 }}
            placeholder="Email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <input
            type="password"
            style={{ width: '100%', padding: 8, marginBottom: 8 }}
            placeholder="Password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          {error ? <div style={{ color: '#dc2626', fontSize: 12 }}>{error}</div> : null}
          <button style={{ width: '100%', padding: 8 }} onClick={() => void handleLogin()}>
            Sign in
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={{ padding: 16, fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: 16, fontWeight: 600 }}>Picking Sessions</h1>
        <button onClick={() => void handleLogout()}>Logout</button>
      </div>

      <div style={{ marginTop: 12, border: '1px solid #e2e8f0', padding: 8 }}>
        <div style={{ fontSize: 12, fontWeight: 600 }}>Sync status</div>
        <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
          {syncRuns[0]
            ? `Latest: ${syncRuns[0].status} (add ${syncRuns[0].plan_summary?.add ?? 0})`
            : 'No sync runs yet.'}
        </div>
        <button style={{ marginTop: 6 }} onClick={() => void handleQuickSync()}>
          Quick sync preview
        </button>
        {syncStatus ? <div style={{ fontSize: 12, marginTop: 4 }}>{syncStatus}</div> : null}
      </div>

      <button style={{ marginTop: 8 }} onClick={() => void loadSessions(auth.accessToken)}>
        Refresh
      </button>

      <div style={{ marginTop: 12 }}>
        {sessions.map((session) => (
          <div
            key={session.id}
            style={{
              border: '1px solid #e2e8f0',
              padding: 8,
              marginBottom: 8,
              cursor: 'pointer'
            }}
            onClick={() => void loadRoute(session, auth.accessToken)}
          >
            <div style={{ fontSize: 12 }}>{session.status}</div>
            <div style={{ fontSize: 13, fontWeight: 600 }}>{session.total_orders} orders</div>
            <div style={{ fontSize: 12, color: '#64748b' }}>
              {session.picked_items}/{session.total_items} items picked
            </div>
          </div>
        ))}
      </div>

      {selectedSession ? (
        <div style={{ marginTop: 16 }}>
          <h2 style={{ fontSize: 14 }}>Route</h2>
          {routeItems.map((item) => (
            <div
              key={item.order_line_id}
              style={{ borderBottom: '1px solid #e2e8f0', padding: '6px 0' }}
            >
              <div style={{ fontWeight: 600 }}>{item.item_no}</div>
              <div style={{ fontSize: 12, color: '#64748b' }}>
                Qty {item.qty_ordered} · {item.location_code ?? 'No location'}
              </div>
              <button style={{ marginTop: 4 }} onClick={() => void handlePick(item, auth.accessToken)}>
                Pick
              </button>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <SidePanelApp />
  </React.StrictMode>
)
