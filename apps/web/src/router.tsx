import { Navigate, Outlet, createRootRoute, createRoute, createRouter } from '@tanstack/react-router'

import { AppLayout } from './components/Layout'
import { useAuth } from './lib/auth'
import { AuditPage } from './routes/AuditPage'
import { DashboardPage } from './routes/DashboardPage'
import { InventoryDetailPage } from './routes/InventoryDetailPage'
import { InventoryPage } from './routes/InventoryPage'
import { LocationsPage } from './routes/LocationsPage'
import { LoginPage } from './routes/LoginPage'
import { OrderDetailPage } from './routes/OrderDetailPage'
import { OrdersPage } from './routes/OrdersPage'
import { PickSessionDetailPage } from './routes/PickSessionDetailPage'
import { PickSessionsPage } from './routes/PickSessionsPage'
import { WebhooksPage } from './routes/WebhooksPage'

function RootLayout() {
  return <Outlet />
}

function ProtectedLayout() {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="p-6 text-sm text-slate-500">Loading session...</div>
  }

  if (!user) {
    return <Navigate to="/login" />
  }

  return (
    <AppLayout>
      <Outlet />
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

const appRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: ProtectedLayout
})

const dashboardRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/',
  component: DashboardPage
})

const inventoryRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/inventory',
  component: InventoryPage
})

const inventoryDetailRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/inventory/$itemId',
  component: InventoryDetailPage
})

const ordersRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/orders',
  component: OrdersPage
})

const orderDetailRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/orders/$orderId',
  component: OrderDetailPage
})

const pickSessionsRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/picker',
  component: PickSessionsPage
})

const pickSessionDetailRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/picker/$sessionId',
  component: PickSessionDetailPage
})

const locationsRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/locations',
  component: LocationsPage
})

const auditRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/audit',
  component: AuditPage
})

const webhooksRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/webhooks',
  component: WebhooksPage
})

const routeTree = rootRoute.addChildren([
  loginRoute,
  appRoute.addChildren([
    dashboardRoute,
    inventoryRoute,
    inventoryDetailRoute,
    ordersRoute,
    orderDetailRoute,
    pickSessionsRoute,
    pickSessionDetailRoute,
    locationsRoute,
    auditRoute,
    webhooksRoute
  ])
])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
