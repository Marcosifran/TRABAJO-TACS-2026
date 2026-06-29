import { useState, useEffect } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { apiFetch } from '../api/client'
import { getPartidos } from '../api/partidos'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Icon from '../components/ui/Icon'

const FEATURES = [
  { icon: 'photo_library', label: 'Colección' },
  { icon: 'swap_horiz', label: 'Intercambios' },
  { icon: 'gavel', label: 'Subastas' },
]

function fraseUsuarios(n) {
  if (n <= 1) return 'Sé el primer coleccionista'
  if (n < 10) return `${n} coleccionistas pioneros`
  return `${n} coleccionistas en la comunidad`
}

function fraseIntercambios(n) {
  if (n === 0) return 'El primer intercambio te espera'
  if (n === 1) return '1 intercambio concretado'
  return `${n} intercambios concretados`
}

function frasePublicaciones(n) {
  if (n === 0) return 'Sé el primero en publicar'
  if (n === 1) return '1 figurita buscando dueño'
  return `${n} figuritas buscando dueño`
}

const STATS_CONFIG = [
  { key: 'usuarios', icon: 'group', frase: fraseUsuarios },
  { key: 'intercambios_completados', icon: 'handshake', frase: fraseIntercambios },
  { key: 'publicaciones_activas', icon: 'style', frase: frasePublicaciones },
]

function hoyBA() {
  return new Date().toLocaleDateString('en-CA', { timeZone: 'America/Argentina/Buenos_Aires' })
}

export default function LoginPage() {
  const { login } = useAuth()
  const { dark, toggleDark } = useTheme()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const [stats, setStats] = useState(null)
  const [partidosHoy, setPartidosHoy] = useState([])

  const destino = location.state?.from?.pathname || '/'

  useEffect(() => {
    apiFetch('/estadisticas/publicas')
      .then(setStats)
      .catch(() => {})
    getPartidos()
      .then((ps) => setPartidosHoy(ps.filter((p) => p.fecha === hoyBA())))
      .catch(() => {})
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email, password)
      navigate(destino, { replace: true })
    } catch (err) {
      setError(err?.message || 'No se pudo iniciar sesión')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface text-on-surface font-sans p-4 relative">
      {/* Theme toggle */}
      <button
        onClick={toggleDark}
        className="fixed top-4 right-4 w-9 h-9 rounded-full flex items-center justify-center bg-surface-container border border-outline-variant hover:bg-surface-variant transition-colors cursor-pointer"
        title={dark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
      >
        <Icon
          name={dark ? 'light_mode' : 'dark_mode'}
          size={18}
          className="text-on-surface-variant"
        />
      </button>

      <div className="w-full max-w-sm">
        {/* Branding */}
        <div className="flex flex-col items-center mb-6 gap-3">
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center shadow-md"
            style={{
              background: 'linear-gradient(135deg, var(--color-primary), var(--color-tertiary))',
            }}
          >
            <Icon name="swap_horiz" size={28} className="text-white" />
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold tracking-tight">FiguSwap</div>
            <div className="text-sm text-on-surface-variant mt-0.5">
              Intercambiá figuritas del Mundial 2026
            </div>
          </div>
        </div>

        {/* Partidos de hoy */}
        {partidosHoy.length > 0 && (
          <div className="mb-4 bg-surface-container rounded-2xl border border-outline-variant px-4 py-3">
            <p className="text-xs font-semibold text-on-surface-variant uppercase tracking-wide mb-2">
              ⚽ Partidos de hoy
            </p>
            <div className="flex flex-col gap-1.5">
              {partidosHoy.slice(0, 5).map((p) => (
                <div key={p.id} className="flex items-center justify-between text-sm">
                  <span className="text-on-surface truncate">
                    {p.local} <span className="text-on-surface-variant text-xs">vs</span>{' '}
                    {p.visitante}
                  </span>
                  <span className="text-on-surface-variant text-xs ml-3 shrink-0">{p.hora} hs</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Card principal */}
        <div className="bg-surface-container rounded-2xl border border-outline-variant p-6">
          <h1 className="text-xl font-bold mb-1">Iniciar sesión</h1>
          <p className="text-sm text-on-surface-variant mb-5">Ingresá con tu email y contraseña.</p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input
              label="Email"
              type="email"
              icon="mail"
              value={email}
              onChange={setEmail}
              placeholder="tu@email.com"
            />
            <Input
              label="Contraseña"
              type="password"
              icon="lock"
              value={password}
              onChange={setPassword}
              placeholder="••••••••"
            />

            {error && (
              <div className="flex items-center gap-2 text-sm text-error">
                <Icon name="error" size={18} />
                <span>{error}</span>
              </div>
            )}

            <Button type="submit" size="lg" disabled={loading} className="w-full mt-1">
              {loading ? 'Ingresando…' : 'Ingresar'}
            </Button>
          </form>

          <p className="text-sm text-on-surface-variant text-center mt-5">
            ¿No tenés cuenta?{' '}
            <Link to="/registro" className="text-primary font-medium no-underline hover:underline">
              Registrate
            </Link>
          </p>
        </div>

        {/* Stats */}
        {stats && (
          <div className="mt-4 flex flex-col gap-2">
            {STATS_CONFIG.map(({ key, icon, frase }) => (
              <div
                key={key}
                className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-surface-container"
              >
                <Icon name={icon} size={15} className="text-primary shrink-0" />
                <span className="text-xs text-on-surface-variant">{frase(stats[key])}</span>
              </div>
            ))}
          </div>
        )}

        {/* Feature strip */}
        <div className="flex justify-center gap-6 mt-6">
          {FEATURES.map((f) => (
            <div key={f.label} className="flex flex-col items-center gap-1">
              <div className="w-9 h-9 rounded-xl bg-surface-container flex items-center justify-center">
                <Icon name={f.icon} size={18} className="text-on-surface-variant" />
              </div>
              <span className="text-[10px] text-on-surface-variant">{f.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
