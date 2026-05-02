import Card from '../components/ui/Card'
import Icon from '../components/ui/Icon'
import EmptyState from '../components/ui/EmptyState'

const STATS = [
  { icon: 'group',       label: 'Usuarios',          value: '0',  colorVar: 'var(--color-primary)' },
  { icon: 'style',       label: 'Figuritas',          value: '0',  colorVar: 'var(--color-tertiary)' },
  { icon: 'swap_horiz',  label: 'Intercambios hoy',   value: '0',  colorVar: 'var(--color-secondary)' },
  { icon: 'gavel',       label: 'Subastas activas',   value: '0',  colorVar: 'var(--color-gold)' },
]

export default function AdminPage() {
  return (
    <div className="p-8 max-w-[1000px]">
      <h1 className="text-3xl font-bold text-on-surface mb-6">Panel de Administración</h1>

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

      <h2 className="text-lg font-semibold mb-3.5">Top selecciones más intercambiadas</h2>
      <EmptyState
        icon="bar_chart"
        title="Sin datos de actividad"
        subtitle="Las estadísticas de intercambios por selección aparecerán acá"
      />
    </div>
  )
}
