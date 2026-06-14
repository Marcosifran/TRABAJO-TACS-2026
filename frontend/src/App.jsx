import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { UserProvider, useUser } from './context/UserContext'
import AppShell from './components/AppShell'
import HomePage from './pages/HomePage'
import CollectionPage from './pages/CollectionPage'
import SearchPage from './pages/SearchPage'
import TradesPage from './pages/TradesPage'
import AuctionsPage from './pages/AuctionsPage'
import NotificationsPage from './pages/NotificationsPage'
import ProfilePage from './pages/ProfilePage'
import AdminPage from './pages/AdminPage'
import AdminCalificacionesPage from './pages/AdminCalificacionesPage'

function RequireAdmin({ children }) {
  const { user } = useUser()
  return user.es_admin ? children : <Navigate to="/" replace />
}

export default function App() {
  return (
    <ThemeProvider>
      <UserProvider>
        <BrowserRouter>
          <AppShell>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/coleccion" element={<CollectionPage />} />
              <Route path="/buscar" element={<SearchPage />} />
              <Route path="/intercambios" element={<TradesPage />} />
              <Route path="/subastas" element={<AuctionsPage />} />
              <Route path="/alertas" element={<NotificationsPage />} />
              <Route path="/perfil" element={<ProfilePage />} />
              <Route
                path="/admin"
                element={
                  <RequireAdmin>
                    <AdminPage />
                  </RequireAdmin>
                }
              />
              <Route
                path="/admin/calificaciones"
                element={
                  <RequireAdmin>
                    <AdminCalificacionesPage />
                  </RequireAdmin>
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AppShell>
        </BrowserRouter>
      </UserProvider>
    </ThemeProvider>
  )
}
