import { ReactNode, useState } from 'react'
import { Link } from '@tanstack/react-router'

import { useAuth } from '../lib/auth'
import { NotificationsDropdown } from './NotificationsDropdown'
import { ThemeToggle } from './ThemeToggle'

export function AppLayout({ children }: { children: ReactNode }) {
  const { logout, user } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="flex items-center justify-between border-b bg-white px-6 py-4 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center gap-3">
          <button
            className="rounded-md border px-2 py-1 text-xs text-slate-600 md:hidden dark:border-slate-700 dark:text-slate-200"
            onClick={() => setSidebarOpen((prev) => !prev)}
          >
            Menu
          </button>
          <div className="text-lg font-semibold">Brikonnect</div>
        </div>
        <div className="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
          <ThemeToggle />
          <NotificationsDropdown />
          <span>{user?.email}</span>
          <button
            className="rounded-md border px-3 py-1 text-xs text-slate-600 dark:border-slate-700 dark:text-slate-200"
            onClick={() => void logout()}
          >
            Logout
          </button>
        </div>
      </header>
      <div className="flex">
        {sidebarOpen ? (
          <div
            className="fixed inset-0 z-10 bg-black/40 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        ) : null}
        <aside
          className={`fixed inset-y-0 left-0 z-20 w-56 border-r bg-white px-4 py-6 transition-transform md:static md:translate-x-0 dark:border-slate-800 dark:bg-slate-900 ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
          }`}
        >
          <nav className="space-y-2 text-sm">
            <Link to="/" className="block font-medium text-slate-700 dark:text-slate-200">
              Dashboard
            </Link>
            <Link to="/billing" className="block text-slate-500 dark:text-slate-400">
              Billing
            </Link>
            <Link to="/stores" className="block text-slate-500 dark:text-slate-400">
              Stores
            </Link>
            <Link to="/inventory" className="block text-slate-500 dark:text-slate-400">
              Inventory
            </Link>
            <Link to="/sync" className="block text-slate-500 dark:text-slate-400">
              Sync
            </Link>
            <Link to="/orders" className="block text-slate-500 dark:text-slate-400">
              Orders
            </Link>
            <Link to="/shipping/carriers" className="block text-slate-500 dark:text-slate-400">
              Shipping
            </Link>
            <Link to="/picker" className="block text-slate-500 dark:text-slate-400">
              Picking
            </Link>
            <Link to="/locations" className="block text-slate-500 dark:text-slate-400">
              Locations
            </Link>
            <Link to="/audit" className="block text-slate-500 dark:text-slate-400">
              Audit
            </Link>
            <Link to="/webhooks" className="block text-slate-500 dark:text-slate-400">
              Webhooks
            </Link>
          </nav>
        </aside>
        <main className="flex-1 px-6 py-8 md:ml-0">{children}</main>
      </div>
    </div>
  )
}
