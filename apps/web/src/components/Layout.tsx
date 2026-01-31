import { ReactNode } from 'react'

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="flex items-center justify-between border-b bg-white px-6 py-4">
        <div className="text-lg font-semibold">Brikonnect</div>
        <div className="text-sm text-slate-500">Inventory & Fulfillment</div>
      </header>
      <div className="flex">
        <aside className="min-h-[calc(100vh-65px)] w-56 border-r bg-white px-4 py-6">
          <nav className="space-y-2 text-sm">
            <div className="font-medium text-slate-700">Dashboard</div>
            <div className="text-slate-500">Inventory</div>
            <div className="text-slate-500">Orders</div>
            <div className="text-slate-500">Picking</div>
          </nav>
        </aside>
        <main className="flex-1 px-6 py-8">{children}</main>
      </div>
    </div>
  )
}
