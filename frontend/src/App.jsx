import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import AppShell from './components/AppShell'
import HomePage from './pages/HomePage'
import CollectionPage from './pages/CollectionPage'
import SearchPage from './pages/SearchPage'
import TradesPage from './pages/TradesPage'
import AuctionsPage from './pages/AuctionsPage'
import NotificationsPage from './pages/NotificationsPage'
import ProfilePage from './pages/ProfilePage'
import AdminPage from './pages/AdminPage'

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/"              element={<HomePage />} />
            <Route path="/coleccion"     element={<CollectionPage />} />
            <Route path="/buscar"        element={<SearchPage />} />
            <Route path="/intercambios"  element={<TradesPage />} />
            <Route path="/subastas"      element={<AuctionsPage />} />
            <Route path="/alertas"       element={<NotificationsPage />} />
            <Route path="/perfil"        element={<ProfilePage />} />
            <Route path="/admin"         element={<AdminPage />} />
            <Route path="*"              element={<Navigate to="/" replace />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </ThemeProvider>
  )
}
