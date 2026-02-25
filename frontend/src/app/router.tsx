import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { useAuthStore } from './providers/AuthProvider'
import { LoadingSpinner } from '../shared/components/LoadingSpinner'

// Lazy-loaded modules
const LoginPage = lazy(() => import('../modules/auth/LoginPage'))
const DashboardPage = lazy(() => import('../modules/dashboard/DashboardPage'))
const MapPage = lazy(() => import('../modules/map/MapPage'))
const OOBPage = lazy(() => import('../modules/oob/OOBPage'))
const SimulationPage = lazy(() => import('../modules/simulation/SimulationPage'))
const IntelPage = lazy(() => import('../modules/intel/IntelPage'))
const AdminPage = lazy(() => import('../modules/admin/AdminPage'))
const CyberPage = lazy(() => import('../modules/cyber/CyberPage'))
const CBRNPage = lazy(() => import('../modules/cbrn/CBRNPage'))
const AsymPage = lazy(() => import('../modules/asym/AsymPage'))
const TerrorPage = lazy(() => import('../modules/terror/TerrorPage'))
const CivilianPage = lazy(() => import('../modules/civilian/CivilianPage'))
const ReportingPage = lazy(() => import('../modules/reporting/ReportingPage'))
const EconPage = lazy(() => import('../modules/econ/EconPage'))
const InfoOpsPage = lazy(() => import('../modules/infoops/InfoOpsPage'))

// ── Guard: redirect unauthenticated users to /login ───────────────────────────
function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  return (
    <Suspense fallback={<LoadingSpinner fullscreen />}>
      <Outlet />
    </Suspense>
  )
}

// ── Guard: redirect authenticated users away from /login ─────────────────────
function PublicOnlyRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }
  return (
    <Suspense fallback={<LoadingSpinner fullscreen />}>
      <Outlet />
    </Suspense>
  )
}

export const router = createBrowserRouter([
  {
    element: <PublicOnlyRoute />,
    children: [{ path: '/login', element: <LoginPage /> }],
  },
  {
    element: <ProtectedRoute />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: '/map', element: <MapPage /> },
      { path: '/oob', element: <OOBPage /> },
      { path: '/simulation', element: <SimulationPage /> },
      { path: '/intel', element: <IntelPage /> },
      { path: '/cyber', element: <CyberPage /> },
      { path: '/cbrn', element: <CBRNPage /> },
      { path: '/asym', element: <AsymPage /> },
      { path: '/terror', element: <TerrorPage /> },
      { path: '/civilian', element: <CivilianPage /> },
      { path: '/reporting', element: <ReportingPage /> },
      { path: '/econ', element: <EconPage /> },
      { path: '/infoops', element: <InfoOpsPage /> },
      { path: '/admin', element: <AdminPage /> },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])
