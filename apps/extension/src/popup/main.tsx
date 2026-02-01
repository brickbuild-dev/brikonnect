import React, { useEffect, useState } from 'react'
import ReactDOM from 'react-dom/client'
import { ArrowUpRight, CheckCircle2, PanelRightOpen } from 'lucide-react'

import { apiFetch } from '../shared/api'
import { getAuth, logout, refreshAuth } from '../shared/auth'
import { applyTheme, getStoredTheme } from '../shared/theme'
import '../styles/index.css'

const statusOptions = ['READY', 'SHIPPED', 'DELIVERED', 'COMPLETED']

function PopupApp() {
  const [authenticated, setAuthenticated] = useState(false)
  const [orderId, setOrderId] = useState('')
  const [status, setStatus] = useState('READY')
  const [message, setMessage] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    applyTheme(getStoredTheme())
    void getAuth().then((auth) => setAuthenticated(Boolean(auth)))
    chrome.storage.local.get('unreadCount').then((result) => {
      if (typeof result.unreadCount === 'number') {
        setUnreadCount(result.unreadCount)
      }
    })
  }, [])

  const openSidePanel = async () => {
    const currentWindow = await chrome.windows.getCurrent()
    await chrome.sidePanel.open({ windowId: currentWindow.id })
  }

  const handleStatusUpdate = async () => {
    if (!orderId.trim()) return
    setLoading(true)
    setMessage(null)
    try {
      const auth = await refreshAuth()
      if (!auth) {
        setMessage('Sign in via the side panel.')
        setAuthenticated(false)
        return
      }
      await apiFetch(
        `/orders/${orderId.trim()}/status`,
        {
          method: 'POST',
          body: JSON.stringify({ status, notes: 'Updated from Brikonnect popup.' })
        },
        auth.accessToken
      )
      setMessage('Status updated.')
      setOrderId('')
    } catch (error) {
      setMessage((error as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-72 space-y-4 p-4">
      <div>
        <div className="text-sm font-semibold">Brikonnect</div>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          {authenticated ? 'Quick actions ready.' : 'Sign in from the side panel.'}
        </p>
        <div className="mt-2 inline-flex items-center gap-2 rounded-full bg-amber-100 px-2 py-1 text-[10px] font-semibold text-amber-700 dark:bg-amber-500/20 dark:text-amber-200">
          {unreadCount} unread alerts
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 space-y-3">
        <div className="text-xs font-semibold uppercase text-slate-400">Quick status update</div>
        <input
          className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          placeholder="Order ID"
          value={orderId}
          onChange={(event) => setOrderId(event.target.value)}
        />
        <select className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100" value={status} onChange={(event) => setStatus(event.target.value)}>
          {statusOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
        <button className="inline-flex items-center justify-center gap-2 rounded-md bg-slate-900 px-3 py-2 text-xs font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200 w-full" onClick={() => void handleStatusUpdate()} disabled={loading}>
          <CheckCircle2 className="h-4 w-4" />
          {loading ? 'Updating...' : 'Update status'}
        </button>
        {message ? <p className="text-xs text-emerald-600">{message}</p> : null}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 space-y-2">
        <div className="text-xs font-semibold uppercase text-slate-400">Navigation</div>
        <button className="inline-flex items-center justify-center gap-2 rounded-md bg-slate-900 px-3 py-2 text-xs font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200 w-full" onClick={() => void openSidePanel()}>
          <PanelRightOpen className="h-4 w-4" /> Open side panel
        </button>
        {authenticated ? (
          <button
            className="inline-flex w-full items-center justify-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300"
            onClick={() => void logout()}
          >
            <ArrowUpRight className="h-4 w-4" /> Sign out
          </button>
        ) : null}
      </div>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <PopupApp />
  </React.StrictMode>
)
