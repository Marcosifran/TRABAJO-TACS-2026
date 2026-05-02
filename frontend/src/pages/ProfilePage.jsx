import Card from '../components/ui/Card'
import Avatar from '../components/ui/Avatar'
import Button from '../components/ui/Button'
import Icon from '../components/ui/Icon'
import StarRating from '../components/ui/StarRating'
import EmptyState from '../components/ui/EmptyState'

const STATS = [
  { icon: 'collections_bookmark', label: 'Figuritas',   value: '0', colorVar: 'var(--color-primary)' },
  { icon: 'playlist_add',         label: 'Faltan',       value: '0', colorVar: 'var(--color-secondary)' },
  { icon: 'swap_horiz',           label: 'Intercambios', value: '0', colorVar: 'var(--color-tertiary)' },
]

export default function ProfilePage() {
  return (
    <div className="p-8 max-w-[800px]">
      <Card elevated className="mb-6 p-7">
        <div className="flex items-center gap-5">
          <Avatar name="Tu Usuario" size={72} />
          <div className="flex-1">
            <h1 className="text-2xl font-bold m-0 text-on-surface">Tu Usuario</h1>
            <p className="text-on-surface-variant text-sm mt-1 mb-2">usuario@test.com</p>
            <div className="flex items-center gap-1.5">
              <StarRating value={0} size={20} />
              <span className="text-sm font-semibold text-on-surface">—</span>
              <span className="text-[13px] text-on-surface-variant">(0 intercambios)</span>
            </div>
          </div>
          <Button variant="outlined" icon="edit">Editar perfil</Button>
        </div>
      </Card>

      <div className="grid grid-cols-3 gap-4 mb-6">
        {STATS.map((s, i) => (
          <Card key={i} className="text-center p-5">
            <Icon name={s.icon} size={28} style={{ color: s.colorVar }} />
            <div className="text-3xl font-bold text-on-surface my-2">{s.value}</div>
            <div className="text-[13px] text-on-surface-variant">{s.label}</div>
          </Card>
        ))}
      </div>

      <h2 className="text-lg font-semibold mb-3.5">Actividad reciente</h2>
      <EmptyState
        icon="history"
        title="Sin actividad reciente"
        subtitle="Tus intercambios, publicaciones y subastas aparecerán acá"
      />
    </div>
  )
}
