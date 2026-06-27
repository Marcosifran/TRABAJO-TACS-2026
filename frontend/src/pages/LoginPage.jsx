import { useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Icon from '../components/ui/Icon'

const FEATURES = [
  { icon: 'photo_library', label: 'Colección' },
  { icon: 'swap_horiz', label: 'Intercambios' },
  { icon: 'gavel', label: 'Subastas' },
]

const DEMO_USERS = [
  { email: 'marcos@utn', nombre: 'Marcos', rol: 'Admin', rolColor: 'text-primary' },
  {
    email: 'jeronimo@utn',
    nombre: 'Jerónimo',
    rol: 'Usuario',
    rolColor: 'text-on-surface-variant',
  },
]

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const destino = location.state?.from?.pathname || '/'

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

  async function loginRapido(demoEmail) {
    setError(null)
    setLoading(true)
    try {
      await login(demoEmail, 'figuswap123')
      navigate(destino, { replace: true })
    } catch (err) {
      setError(err?.message || 'No se pudo iniciar sesión')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface text-on-surface font-sans p-4">
      <div className="w-full max-w-sm">
        {/* Branding */}
        <div className="flex flex-col items-center mb-8 gap-3">
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

          {/* Acceso rápido demo */}
          <div className="mt-5 pt-4 border-t border-outline-variant">
            <p className="text-xs text-on-surface-variant text-center mb-2.5">
              Acceso rápido · demo
            </p>
            <div className="flex gap-2">
              {DEMO_USERS.map((u) => (
                <button
                  key={u.email}
                  type="button"
                  onClick={() => loginRapido(u.email)}
                  disabled={loading}
                  className="flex-1 rounded-xl border border-outline-variant bg-surface-container-low hover:bg-surface-variant transition-colors p-2.5 text-left cursor-pointer disabled:opacity-50"
                >
                  <div className="text-xs font-semibold text-on-surface">{u.nombre}</div>
                  <div className={`text-[10px] font-medium ${u.rolColor}`}>{u.rol}</div>
                </button>
              ))}
            </div>
          </div>

          <p className="text-sm text-on-surface-variant text-center mt-5">
            ¿No tenés cuenta?{' '}
            <Link to="/registro" className="text-primary font-medium no-underline hover:underline">
              Registrate
            </Link>
          </p>
        </div>

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
