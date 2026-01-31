import { useAuth } from '../lib/auth'

export function DashboardPage() {
  const { user, tenant } = useAuth()

  return (
    <div>
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <p className="mt-2 text-sm text-slate-600">
        Welcome back{user?.display_name ? `, ${user.display_name}` : ''}!
      </p>
      <div className="mt-6 rounded-lg border bg-white p-4">
        <div className="text-sm text-slate-500">Tenant</div>
        <div className="text-lg font-medium">{tenant?.name ?? 'Unknown'}</div>
        <div className="text-xs text-slate-400">{tenant?.slug}</div>
      </div>
    </div>
  )
}
