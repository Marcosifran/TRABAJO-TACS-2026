import { useState, useEffect, useRef } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import clsx from 'clsx'
import useSWR from 'swr'
import Icon from './ui/Icon'
import Badge from './ui/Badge'
import Avatar from './ui/Avatar'
import { useTheme } from '../context/ThemeContext'
import { useAuth } from '../context/AuthContext'
import { formatTiempoRestante } from '../utils/auctionTime'

const NAV = [
  { to: '/', icon: 'dashboard', label: 'Inicio' },
  { to: '/coleccion', icon: 'collections_bookmark', label: 'Mi Colección' },
  { to: '/buscar', icon: 'search', label: 'Buscar' },
  { to: '/intercambios', icon: 'swap_horiz', label: 'Intercambios' },
  { to: '/subastas', icon: 'gavel', label: 'Subastas' },
  { to: '/alertas', icon: 'notifications', label: 'Alertas' },
  { to: '/perfil', icon: 'person', label: 'Perfil' },
  { to: '/admin', icon: 'admin_panel_settings', label: 'Admin', adminOnly: true },
]

const POLL_INTERVAL = 20000 // 20 segundos

export default function AppShell({ children }) {
  const { dark, toggleDark } = useTheme()
  const { user, users, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const userId = user.id

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  const [notifs, setNotifs] = useState([])
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const seenSugIds = useRef(null)
  const seenAuctIds = useRef(null)
  const seenTradeIds = useRef(null)
  const timerRefs = useRef({})

  function pushNotif(id, icon, title, body) {
    setNotifs((prev) =>
      prev.some((n) => n.id === id) ? prev : [...prev, { id, icon, title, body }],
    )
    clearTimeout(timerRefs.current[id])
    timerRefs.current[id] = setTimeout(
      () => setNotifs((prev) => prev.filter((n) => n.id !== id)),
      6000,
    )
  }

  function dismissNotif(id) {
    clearTimeout(timerRefs.current[id])
    setNotifs((prev) => prev.filter((n) => n.id !== id))
  }

  // Resetea los "vistos" cuando cambia el usuario para evitar falsos positivos
  useEffect(() => {
    seenAuctIds.current = new Set()
  }, [user])

  // SWR con polling: sugerencias — comparte cache con NotificationsPage y TradesPage
  useSWR(['/publicaciones/sugerencias', userId], {
    refreshInterval: POLL_INTERVAL,
    onSuccess: (sugs = []) => {
      const ids = new Set(sugs.map((s) => s.publicacion.id))
      if (seenSugIds.current === null) {
        seenSugIds.current = ids
        return
      }
      const nuevas = sugs.filter((s) => !seenSugIds.current.has(s.publicacion.id))
      if (nuevas.length > 0) {
        const p = nuevas[0].publicacion
        pushNotif(
          `sug-${p.id}`,
          'auto_awesome',
          '¡Nueva sugerencia disponible!',
          `#${p.numero} ${p.jugador} (${p.equipo})${nuevas.length > 1 ? ` y ${nuevas.length - 1} más` : ''}`,
        )
        seenSugIds.current = ids
      }
    },
  })

  // SWR con polling: intercambios — comparte cache con TradesPage y NotificationsPage
  useSWR(['/intercambios/', userId], {
    refreshInterval: POLL_INTERVAL,
    onSuccess: (data) => {
      const pendientes = (data?.recibidos || []).filter((i) => i.estado === 'pendiente')
      const ids = new Set(pendientes.map((i) => i.id))
      if (seenTradeIds.current === null) {
        seenTradeIds.current = ids
        return
      }
      const nuevas = pendientes.filter((i) => !seenTradeIds.current.has(i.id))
      if (nuevas.length > 0) {
        const t = nuevas[0]
        const ofertante = users.find((u) => u.id === t.propuesto_por)?.nombre ?? `Usuario ${t.propuesto_por}`
        pushNotif(
          `trade-${t.id}`,
          'swap_horiz',
          '¡Nueva propuesta de intercambio!',
          `${ofertante} quiere la figurita #${t.figurita_solicitada}`,
        )
        seenTradeIds.current = ids
      }
    },
  })

  // SWR con polling: subastas — comparte cache con AuctionsPage, HomePage, SearchPage
  useSWR('/subastas', {
    refreshInterval: POLL_INTERVAL,
    onSuccess: (data = []) => {
      const ahora = Date.now()
      const porVencer = data.filter((s) => {
        const ms = new Date(s.fin) - ahora
        return s.estado === 'activa' && ms > 0 && ms < 24 * 3600 * 1000
      })
      porVencer.forEach((s) => {
        if (seenAuctIds.current.has(s.id)) return
        seenAuctIds.current.add(s.id)
        pushNotif(
          `auct-${s.id}`,
          'gavel',
          '⏳ Subasta por finalizar',
          `Subasta #${s.id} cierra en ${formatTiempoRestante(s.fin)}`,
        )
      })
    },
  })

  return (
    <div className="flex h-screen bg-surface text-on-surface font-sans overflow-hidden">
      {/* Mobile header */}
      <header className="md:hidden fixed top-0 left-0 right-0 z-30 h-14 bg-surface-container-low border-b border-outline-variant flex items-center px-4 gap-3">
        <button
          onClick={() => setSidebarOpen(true)}
          className="p-2 rounded-full hover:bg-surface-variant transition-colors border-0 bg-transparent cursor-pointer text-on-surface"
        >
          <Icon name="menu" size={22} />
        </button>
        <div className="flex items-center gap-2">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
            style={{
              background: 'linear-gradient(135deg, var(--color-primary), var(--color-tertiary))',
            }}
          >
            <Icon name="swap_horiz" size={16} className="text-white" />
          </div>
          <span className="text-sm font-bold text-on-surface tracking-tight">FiguSwap</span>
        </div>
      </header>

      {/* Backdrop */}
      {sidebarOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <nav
        className={clsx(
          'fixed md:static top-0 left-0 h-full z-50 w-64 shrink-0 bg-surface-container-low border-r border-outline-variant flex flex-col overflow-y-auto scrollbar-none transition-transform duration-300 md:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        {/* Logo + close button (mobile) */}
        <div className="flex items-center gap-2.5 px-5 py-5">
          <button
            onClick={() => setSidebarOpen(false)}
            className="md:hidden p-1.5 rounded-full hover:bg-surface-variant transition-colors border-0 bg-transparent cursor-pointer text-on-surface-variant shrink-0"
          >
            <Icon name="close" size={20} />
          </button>
          <div
            className="w-38 h-38 rounded-xl flex items-center justify-center shrink-0"
            style={{
              background: 'linear-gradient(135deg, var(--color-primary), var(--color-tertiary))',
            }}
          >
            <Icon name="swap_horiz" size={22} className="text-white" />
          </div>
          <div>
            <div className="text-lg-plus font-bold text-on-surface tracking-tight">FiguSwap</div>
            <div className="text-2xs text-on-surface-variant font-medium">Mundial 2026</div>
          </div>
        </div>

        {/* Nav items */}
        <div className="flex-1 px-3">
          {NAV.filter((item) => !item.adminOnly || user.es_admin).map((item) => {
            const isActive =
              item.to === '/' ? location.pathname === '/' : location.pathname.startsWith(item.to)
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setSidebarOpen(false)}
                className={() =>
                  clsx(
                    'flex items-center gap-3 w-full px-3.5 py-2.5 rounded-full text-sm mb-0.5 transition-all duration-200 no-underline',
                    isActive
                      ? 'bg-primary-container text-on-primary-container font-semibold'
                      : 'text-on-surface-variant hover:bg-surface-variant font-normal',
                  )
                }
              >
                {item.icon === 'notifications' ? (
                  <Badge count={0}>
                    <Icon
                      name={item.icon}
                      size={20}
                      className={isActive ? 'text-on-primary-container' : 'text-on-surface-variant'}
                    />
                  </Badge>
                ) : (
                  <Icon
                    name={item.icon}
                    size={20}
                    className={isActive ? 'text-on-primary-container' : 'text-on-surface-variant'}
                  />
                )}
                {item.label}
              </NavLink>
            )
          })}
        </div>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-outline-variant">
          <button
            onClick={toggleDark}
            className="flex items-center gap-2.5 w-full px-3 py-2 rounded-xl bg-surface-container text-on-surface-variant text-xs-plus mb-2.5 cursor-pointer border-0 font-sans hover:bg-surface-variant transition-colors"
          >
            <Icon
              name={dark ? 'light_mode' : 'dark_mode'}
              size={18}
              className="text-on-surface-variant"
            />
            {dark ? 'Modo claro' : 'Modo oscuro'}
          </button>
          <div className="flex items-center gap-2.5 px-1">
            <Avatar name={user.nombre} size={32} />
            <div className="flex-1 min-w-0">
              <div className="text-xs-plus font-semibold text-on-surface truncate">
                {user.nombre}
              </div>
              <div className="text-2xs text-on-surface-variant truncate">{user.email}</div>
            </div>
            {/* Cerrar sesión */}
            <button
              onClick={handleLogout}
              className="p-1 rounded-full hover:bg-surface-variant transition-colors cursor-pointer border-0 bg-transparent shrink-0"
              title="Cerrar sesión"
            >
              <Icon name="logout" size={18} className="text-on-surface-variant" />
            </button>
          </div>
        </div>
      </nav>

      {/* Main */}
      <main className="flex-1 overflow-y-auto pt-14 md:pt-0" key={user.nombre}>
        {children}
      </main>

      {/* Stack de notificaciones pop-up */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2.5 items-end">
        {notifs.map((n) => (
          <div
            key={n.id}
            className="flex items-start gap-3 bg-surface-container-high border border-outline rounded-2xl shadow-xl p-4 w-[320px] animate-slide-in-right"
          >
            <div className="bg-primary-container rounded-full p-2 shrink-0">
              <Icon name={n.icon} size={20} className="text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-sm text-on-surface">{n.title}</div>
              <div className="text-xs text-on-surface-variant mt-0.5">{n.body}</div>
            </div>
            <button
              onClick={() => dismissNotif(n.id)}
              className="p-1 rounded-full hover:bg-surface-variant transition-colors cursor-pointer border-0 bg-transparent shrink-0 text-on-surface-variant"
            >
              <Icon name="close" size={16} />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
