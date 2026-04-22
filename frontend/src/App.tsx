import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ToastProvider } from './contexts/ToastContext'
import Layout from './components/layout/Layout'
import PrivateRoute from './components/common/PrivateRoute'
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
            <Route path="/dashboard" element={
              <PrivateRoute><Layout><DashboardPage /></Layout></PrivateRoute>
            } />
            <Route path="/professions" element={
              <PrivateRoute><Layout><ProfessionsPage /></Layout></PrivateRoute>
            } />
            <Route path="/professions/:professionId/scenarios" element={
              <PrivateRoute><Layout><ScenariosPage /></Layout></PrivateRoute>
            } />
            <Route path="/session/:sessionId" element={
              <PrivateRoute><Layout><SimulationPage /></Layout></PrivateRoute>
            } />
            <Route path="/session/:sessionId/results" element={
              <PrivateRoute><Layout><ResultsPage /></Layout></PrivateRoute>
            } />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
