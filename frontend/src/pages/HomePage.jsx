import { useNavigate } from 'react-router-dom'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Icon from '../components/ui/Icon'
import EmptyState from '../components/ui/EmptyState'

const STATS = [
  { icon: 'collections_bookmark', label: 'Figuritas',    value: '—',    colorVar: 'var(--color-primary)' },
  { icon: 'playlist_add',         label: 'Faltan',        value: '—',    colorVar: 'var(--color-secondary)' },
  { icon: 'swap_horiz',           label: 'Intercambios',  value: '—',    colorVar: 'var(--color-tertiary)' },
  { icon: 'star',                 label: 'Reputación',    value: '—',    colorVar: 'var(--color-gold)' },
]

export default function HomePage() {
  const navigate = useNavigate()
  return (
    <div className="p-8 max-w-[1100px]">
      <div className="mb-7">
        <h1 className="text-3xl font-bold text-on-surface m-0">Bienvenido de vuelta 👋</h1>
        <p className="mt-1 text-on-surface-variant text-[15px]">Tu resumen de actividad en FiguSwap</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {STATS.map((s, i) => (
          <Card key={i} elevated>
            <div className="flex items-center gap-3.5">
              <div
                className="w-11 h-11 rounded-[14px] flex items-center justify-center shrink-0"
                style={{ background: s.colorVar + '18' }}
              >
                <Icon name={s.icon} size={24} style={{ color: s.colorVar }} />
              </div>
              <div>
                <div className="text-2xl font-bold text-on-surface">{s.value}</div>
                <div className="text-[13px] text-on-surface-variant">{s.label}</div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Quick actions */}
      <div className="flex gap-2.5 mb-8">
        <Button icon="add" onClick={() => navigate('/coleccion')}>Publicar figurita</Button>
        <Button variant="tonal" icon="search" onClick={() => navigate('/buscar')}>Buscar figuritas</Button>
        <Button variant="outlined" icon="gavel" onClick={() => navigate('/subastas')}>Ver subastas</Button>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Últimas publicadas */}
        <div>
          <div className="flex justify-between items-center mb-3.5">
            <h2 className="text-lg font-semibold m-0">Últimas publicadas</h2>
            <Button variant="text" size="sm" onClick={() => navigate('/buscar')}>Ver todas</Button>
          </div>
          <EmptyState
            icon="style"
            title="Sin figuritas publicadas"
            subtitle="Todavía no hay figuritas disponibles para intercambio"
          />
        </div>

        {/* Subastas y Sugerencias */}
        <div>
          <div className="flex justify-between items-center mb-3.5">
            <h2 className="text-lg font-semibold m-0">Subastas por finalizar</h2>
            <Button variant="text" size="sm" onClick={() => navigate('/subastas')}>Ver todas</Button>
          </div>
          <EmptyState
            icon="gavel"
            title="Sin subastas activas"
            subtitle="No hay subastas próximas a finalizar"
          />

          {/* Sugerencias */}
          <h2 className="text-lg font-semibold mt-6 mb-3.5">Sugerencias para vos</h2>
          <Card
            style={{
              background: 'linear-gradient(135deg, var(--color-primary-container), var(--color-tertiary-container))',
              border: 'none',
            }}
          >
            <div className="flex items-center gap-3">
              <Icon name="auto_awesome" size={28} className="text-primary" />
              <div className="flex-1">
                <div className="font-semibold text-[14px] text-on-primary-container">Sin sugerencias aún</div>
                <div className="text-[13px] text-on-primary-container/80">Registrá tus faltantes para recibir sugerencias automáticas</div>
              </div>
              <Button size="sm" onClick={() => navigate('/intercambios')}>Ver</Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
