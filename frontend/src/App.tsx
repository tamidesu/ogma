import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ToastProvider } from './contexts/ToastContext'
import Layout from './components/layout/Layout'
import LandingPage from './pages/LandingPage'
import AuthPage from './pages/AuthPage'
import DashboardPage from './pages/DashboardPage'
import ProfessionsPage from './pages/ProfessionsPage'
import ScenariosPage from './pages/ScenariosPage'
import SimulationPage from './pages/SimulationPage'
import ResultsPage from './pages/ResultsPage'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/"         element={<Layout><LandingPage /></Layout>} />
            <Route path="/login"    element={<AuthPage />} />
            <Route path="/register" element={<AuthPage />} />

            {/* Protected routes */}
            <Route path="/dashboard"   element={<Layout><DashboardPage /></Layout>} />
            <Route path="/professions" element={<Layout><ProfessionsPage /></Layout>} />
            <Route
              path="/professions/:professionId/scenarios"
              element={<Layout><ScenariosPage /></Layout>}
            />
            {/* Legacy guided mode */}
            <Route
              path="/session/:sessionId"
              element={<Layout><SimulationPage /></Layout>}
            />
            <Route
              path="/session/:sessionId/results"
              element={<Layout><ResultsPage /></Layout>}
            />
            {/* ── Open-world simulation ── */}
            {/* Start new session from brief */}
            <Route path="/play/:briefId" element={<OpenWorldPage />} />
            {/* Resume existing open-world session */}
            <Route path="/play/session/:sessionId" element={<OpenWorldPage />} />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
