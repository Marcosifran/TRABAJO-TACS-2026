import { BrowserRouter, Routes, Route, Navigate, Outlet, useLocation } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { AuthProvider, useAuth } from './context/AuthContext'
import AppShell from './components/AppShell'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import HomePage from './pages/HomePage'
import CollectionPage from './pages/CollectionPage'
import SearchPage from './pages/SearchPage'
import TradesPage from './pages/TradesPage'
import AuctionsPage from './pages/AuctionsPage'
import NotificationsPage from './pages/NotificationsPage'
import ProfilePage from './pages/ProfilePage'
import AdminPage from './pages/AdminPage'
import AdminCalificacionesPage from './pages/AdminCalificacionesPage'

// Layout protegido: si no hay sesión redirige a /login recordando el destino.
// Mantiene una única instancia de AppShell mientras se navega entre rutas internas.
function ProtectedLayout() {
  const { token } = useAuth()
  const location = useLocation()
  if (!token) return <Navigate to="/login" replace state={{ from: location }} />
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  )
}

function RequireAdmin({ children }) {
  const { user } = useAuth()
  return user?.es_admin ? children : <Navigate to="/" replace />
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login"    element={<LoginPage />} />
            <Route path="/registro" element={<RegisterPage />} />

            <Route element={<ProtectedLayout />}>
              <Route path="/"              element={<HomePage />} />
              <Route path="/coleccion"     element={<CollectionPage />} />
              <Route path="/buscar"        element={<SearchPage />} />
              <Route path="/intercambios"  element={<TradesPage />} />
              <Route path="/subastas"      element={<AuctionsPage />} />
              <Route path="/alertas"       element={<NotificationsPage />} />
              <Route path="/perfil"        element={<ProfilePage />} />
              <Route path="/admin"                element={<RequireAdmin><AdminPage /></RequireAdmin>} />
              <Route path="/admin/calificaciones" element={<RequireAdmin><AdminCalificacionesPage /></RequireAdmin>} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  )
}
