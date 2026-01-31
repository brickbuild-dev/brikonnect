import { ReactNode } from 'react'
import { Link } from '@tanstack/react-router'

import { useAuth } from '../lib/auth'

export function AppLayout({ children }: { children: ReactNode }) {
  const { logout, user } = useAuth()
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="flex items-center justify-between border-b bg-white px-6 py-4">
        <div className="text-lg font-semibold">Brikonnect</div>
        <div className="flex items-center gap-4 text-sm text-slate-500">
          <span>{user?.email}</span>
          <button
            className="rounded-md border px-3 py-1 text-xs text-slate-600"
            onClick={() => void logout()}
          >
            Logout
          </button>
        </div>
      </header>
      <div className="flex">
        <aside className="min-h-[calc(100vh-65px)] w-56 border-r bg-white px-4 py-6">
          <nav className="space-y-2 text-sm">
            <Link to="/" className="block font-medium text-slate-700">
              Dashboard
            </Link>
            <Link to="/inventory" className="block text-slate-500">
              Inventory
            </Link>
            <Link to="/orders" className="block text-slate-500">
              Orders
            </Link>
            <Link to="/locations" className="block text-slate-500">
              Locations
            </Link>
          </nav>
        </aside>
        <main className="flex-1 px-6 py-8">{children}</main>
      </div>
    </div>
  )
}
