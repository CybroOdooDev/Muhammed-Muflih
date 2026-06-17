import { Navigate, Route, Routes } from 'react-router-dom'

import ProtectedRoute from './components/ProtectedRoute'
import DashboardLayout from './components/DashboardLayout'
import Login from './pages/Login'
import ReportDashboard from './pages/ReportDashboard'
import Comparison from './pages/Comparison'
import MomDashboard from './pages/MomDashboard'
import WorkDayCount from './pages/WorkDayCount'
import Projects from './pages/Projects'
import Settings from './pages/Settings'
import OdooDailyDashboard from './pages/OdooDailyDashboard'
import { useAuth } from './context/AuthContext'

export default function App() {
  const { user } = useAuth()

  return (
    <Routes>
      <Route
        path="/login"
        element={user ? <Navigate to="/" replace /> : <Login />}
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<ReportDashboard />} />
        <Route path="comparison" element={<Comparison />} />
        <Route path="mom" element={<MomDashboard />} />
        <Route path="work-days" element={<WorkDayCount />} />
        <Route path="projects" element={<Projects />} />
        <Route path="odoo-daily" element={<OdooDailyDashboard />} />
<Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
