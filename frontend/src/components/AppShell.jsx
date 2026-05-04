import { useState, useEffect, useRef } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import Icon from './ui/Icon'
import Badge from './ui/Badge'
import Avatar from './ui/Avatar'
import { useTheme } from '../context/ThemeContext'
import { useUser } from '../context/UserContext'
import { obtenerSugerencias } from '../api/faltantes'
import { listarSubastas } from '../api/subastas'
import { formatTiempoRestante } from '../utils/auctionTime'

const NAV = [
  { to: '/',             icon: 'dashboard',            label: 'Inicio' },
  { to: '/coleccion',    icon: 'collections_bookmark', label: 'Mi Colección' },
  { to: '/buscar',       icon: 'search',               label: 'Buscar' },
  { to: '/intercambios', icon: 'swap_horiz',            label: 'Intercambios' },
  { to: '/subastas',     icon: 'gavel',                label: 'Subastas' },
  { to: '/alertas',      icon: 'notifications',         label: 'Alertas' },
  { to: '/perfil',       icon: 'person',               label: 'Perfil' },
  { to: '/admin',        icon: 'admin_panel_settings',  label: 'Admin' },
]

const POLL_INTERVAL = 20000 // 20 segundos

export default function AppShell({ children }) {
  const { dark, toggleDark } = useTheme()
  const { user, users, switchUser } = useUser()
  const location = useLocation()

  const [notifs, setNotifs] = useState([])
  const seenSugIds   = useRef(null)
  const seenAuctIds  = useRef(null)
  const timerRefs    = useRef({})

  function pushNotif(id, icon, title, body) {
    setNotifs(prev => prev.some(n => n.id === id) ? prev : [...prev, { id, icon, title, body }])
    clearTimeout(timerRefs.current[id])
    timerRefs.current[id] = setTimeout(
      () => setNotifs(prev => prev.filter(n => n.id !== id)),
      6000
    )
  }

  function dismissNotif(id) {
    clearTimeout(timerRefs.current[id])
    setNotifs(prev => prev.filter(n => n.id !== id))
  }

  // Poll sugerencias
  useEffect(() => {
    seenSugIds.current = null
    async function pollSugs() {
      try {
        const data = await obtenerSugerencias()
        const sugs = data.sugerencias || []
        const ids  = new Set(sugs.map(s => s.publicacion.id))
        if (seenSugIds.current === null) { seenSugIds.current = ids; return }
        const nuevas = sugs.filter(s => !seenSugIds.current.has(s.publicacion.id))
        if (nuevas.length > 0) {
          const p = nuevas[0].publicacion
          pushNotif(
            `sug-${p.id}`,
            'auto_awesome',
            '¡Nueva sugerencia disponible!',
            `#${p.numero} ${p.jugador} (${p.equipo})${nuevas.length > 1 ? ` y ${nuevas.length - 1} más` : ''}`
          )
          seenSugIds.current = ids
        }
      } catch { /* ignorar */ }
    }
    pollSugs()
    const t = setInterval(pollSugs, POLL_INTERVAL)
    return () => clearInterval(t)
  }, [user])

  // Poll subastas por vencer (< 24 hs)
  useEffect(() => {
    seenAuctIds.current = new Set()
    async function pollSubastas() {
      try {
        const data = await listarSubastas()
        const ahora = Date.now()
        const porVencer = (data.subastas || []).filter(s => {
          const ms = new Date(s.fin) - ahora
          return s.estado === 'activa' && ms > 0 && ms < 24 * 3600 * 1000
        })
        porVencer.forEach(s => {
          if (seenAuctIds.current.has(s.id)) return
          seenAuctIds.current.add(s.id)
          const tiempo = formatTiempoRestante(s.fin)
          pushNotif(
            `auct-${s.id}`,
            'gavel',
            '⏳ Subasta por finalizar',
            `Subasta #${s.id} cierra en ${tiempo}`
          )
        })
      } catch { /* ignorar */ }
    }
    pollSubastas()
    const t = setInterval(pollSubastas, POLL_INTERVAL)
    return () => clearInterval(t)
  }, [user])

  return (
    <div className="flex h-screen bg-surface text-on-surface font-sans overflow-hidden">
      {/* Sidebar */}
      <nav className="w-64 shrink-0 bg-surface-container-low border-r border-outline-variant flex flex-col overflow-y-auto scrollbar-none">
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-5 py-5">
          <div
            className="w-[38px] h-[38px] rounded-xl flex items-center justify-center shrink-0"
            style={{ background: 'linear-gradient(135deg, var(--color-primary), var(--color-tertiary))' }}
          >
            <Icon name="swap_horiz" size={22} className="text-white" />
          </div>
          <div>
            <div className="text-[18px] font-bold text-on-surface tracking-tight">FiguSwap</div>
            <div className="text-[11px] text-on-surface-variant font-medium">Mundial 2026</div>
          </div>
        </div>

        {/* Nav items */}
        <div className="flex-1 px-3">
          {NAV.map(item => {
            const isActive = item.to === '/'
              ? location.pathname === '/'
              : location.pathname.startsWith(item.to)
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={() => `
                  flex items-center gap-3 w-full px-3.5 py-2.5 rounded-full text-sm mb-0.5
                  transition-all duration-200 no-underline
                  ${isActive
                    ? 'bg-primary-container text-on-primary-container font-semibold'
                    : 'text-on-surface-variant hover:bg-surface-variant font-normal'
                  }
                `}
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
            className="flex items-center gap-2.5 w-full px-3 py-2 rounded-xl bg-surface-container text-on-surface-variant text-[13px] mb-2.5 cursor-pointer border-0 font-sans hover:bg-surface-variant transition-colors"
          >
            <Icon name={dark ? 'light_mode' : 'dark_mode'} size={18} className="text-on-surface-variant" />
            {dark ? 'Modo claro' : 'Modo oscuro'}
          </button>
          <div className="flex items-center gap-2.5 px-1">
            <Avatar name={user.nombre} size={32} />
            <div className="flex-1 min-w-0">
              <div className="text-[13px] font-semibold text-on-surface truncate">{user.nombre}</div>
              <div className="text-[11px] text-on-surface-variant truncate">{user.email}</div>
            </div>
            {/* Selector de usuario para desarrollo */}
            <button
              onClick={() => switchUser(users.indexOf(user) === 0 ? 1 : 0)}
              className="p-1 rounded-full hover:bg-surface-variant transition-colors cursor-pointer border-0 bg-transparent shrink-0"
              title="Cambiar usuario (dev)"
            >
              <Icon name="switch_account" size={18} className="text-on-surface-variant" />
            </button>
          </div>
        </div>
      </nav>

      {/* Main */}
      <main className="flex-1 overflow-y-auto" key={user.nombre}>
        {children}
      </main>

      {/* Stack de notificaciones pop-up */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2.5 items-end">
        {notifs.map(n => (
          <div
            key={n.id}
            className="flex items-start gap-3 bg-surface-container-high border border-outline rounded-2xl shadow-xl p-4 w-[320px]"
            style={{ animation: 'slideInRight 0.3s ease' }}
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

      <style>{`
        @keyframes slideInRight {
          from { transform: translateX(110%); opacity: 0; }
          to   { transform: translateX(0);    opacity: 1; }
        }
      `}</style>
    </div>
  )
}
