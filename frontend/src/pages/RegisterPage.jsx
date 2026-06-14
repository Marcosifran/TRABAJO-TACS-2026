import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Icon from '../components/ui/Icon'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()

  const [nombre, setNombre] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)

    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres.')
      return
    }

    setLoading(true)
    try {
      await register(nombre, email, password)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err?.message || 'No se pudo crear la cuenta')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface text-on-surface font-sans p-4">
      <div className="w-full max-w-sm">
        {/* Branding */}
        <div className="flex items-center gap-2.5 justify-center mb-8">
          <div
            className="w-[42px] h-[42px] rounded-xl flex items-center justify-center shrink-0"
            style={{ background: 'linear-gradient(135deg, var(--color-primary), var(--color-tertiary))' }}
          >
            <Icon name="swap_horiz" size={24} className="text-white" />
          </div>
          <div>
            <div className="text-[20px] font-bold tracking-tight">FiguSwap</div>
            <div className="text-[11px] text-on-surface-variant font-medium">Mundial 2026</div>
          </div>
        </div>

        <div className="bg-surface-container rounded-2xl border border-outline-variant p-6">
          <h1 className="text-xl font-bold mb-1">Crear cuenta</h1>
          <p className="text-sm text-on-surface-variant mb-5">Registrate para empezar a intercambiar.</p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input
              label="Nombre"
              icon="person"
              value={nombre}
              onChange={setNombre}
              placeholder="Tu nombre"
            />
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
              placeholder="Mínimo 6 caracteres"
            />

            {error && (
              <div className="flex items-center gap-2 text-sm text-error">
                <Icon name="error" size={18} />
                <span>{error}</span>
              </div>
            )}

            <Button type="submit" size="lg" disabled={loading} className="w-full mt-1">
              {loading ? 'Creando cuenta…' : 'Crear cuenta'}
            </Button>
          </form>

          <p className="text-sm text-on-surface-variant text-center mt-5">
            ¿Ya tenés cuenta?{' '}
            <Link to="/login" className="text-primary font-medium no-underline hover:underline">
              Iniciá sesión
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
