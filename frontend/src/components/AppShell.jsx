import { NavLink, useLocation } from 'react-router-dom'
import Icon from './ui/Icon'
import Badge from './ui/Badge'
import Avatar from './ui/Avatar'
import { useTheme } from '../context/ThemeContext'

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

const PLACEHOLDER_USER = { nombre: 'Tu Usuario', email: 'usuario@test.com' }
const UNREAD_COUNT = 0

export default function AppShell({ children }) {
  const { dark, toggleDark } = useTheme()
  const location = useLocation()

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
                  <Badge count={UNREAD_COUNT}>
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
            <Avatar name={PLACEHOLDER_USER.nombre} size={32} />
            <div>
              <div className="text-[13px] font-semibold text-on-surface">{PLACEHOLDER_USER.nombre}</div>
              <div className="text-[11px] text-on-surface-variant">{PLACEHOLDER_USER.email}</div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}
