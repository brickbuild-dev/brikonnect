import { Navigate, Outlet, createRootRoute, createRoute, createRouter } from '@tanstack/react-router'

import { AppLayout } from './components/Layout'
import { useAuth } from './lib/auth'
import { DashboardPage } from './routes/DashboardPage'
import { LoginPage } from './routes/LoginPage'

function RootLayout() {
  return <Outlet />
}

function ProtectedDashboard() {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="p-6 text-sm text-slate-500">Loading session...</div>
  }

  if (!user) {
    return <Navigate to="/login" />
  }

  return (
    <AppLayout>
      <DashboardPage />
    </AppLayout>
  )
}

const rootRoute = createRootRoute({
  component: RootLayout
})

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: LoginPage
})

const dashboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: ProtectedDashboard
})

const routeTree = rootRoute.addChildren([loginRoute, dashboardRoute])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
