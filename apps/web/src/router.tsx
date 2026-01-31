import { Navigate, Outlet, createRootRoute, createRoute, createRouter } from '@tanstack/react-router'

import { AppLayout } from './components/Layout'
import { useAuth } from './lib/auth'
import { DashboardPage } from './routes/DashboardPage'
import { InventoryDetailPage } from './routes/InventoryDetailPage'
import { InventoryPage } from './routes/InventoryPage'
import { LocationsPage } from './routes/LocationsPage'
import { LoginPage } from './routes/LoginPage'
import { OrderDetailPage } from './routes/OrderDetailPage'
import { OrdersPage } from './routes/OrdersPage'

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

const locationsRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/locations',
  component: LocationsPage
})

const routeTree = rootRoute.addChildren([
  loginRoute,
  appRoute.addChildren([
    dashboardRoute,
    inventoryRoute,
    inventoryDetailRoute,
    ordersRoute,
    orderDetailRoute,
    locationsRoute
  ])
])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
