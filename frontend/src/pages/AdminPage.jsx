import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../components/ui/Card'
import Icon from '../components/ui/Icon'
import Avatar from '../components/ui/Avatar'
import Button from '../components/ui/Button'
import EmptyState from '../components/ui/EmptyState'
import { obtenerEstadisticas, listarCalificaciones } from '../api/admin'

const CARDS = [
  { key: 'usuarios',               icon: 'group',      label: 'Usuarios',              colorVar: 'var(--color-primary)' },
  { key: 'figuritas_publicadas',   icon: 'style',       label: 'Figuritas publicadas',  colorVar: 'var(--color-tertiary)' },
  { key: 'intercambios_aceptados', icon: 'swap_horiz',  label: 'Intercambios realizados', colorVar: 'var(--color-secondary)' },
  { key: 'subastas_activas',       icon: 'gavel',       label: 'Subastas activas',      colorVar: 'var(--color-gold)' },
]

const ESTADO_CONFIG = {
  pendiente:  { label: 'Pendientes',  color: 'var(--color-primary)' },
  aceptado:   { label: 'Aceptados',   color: '#22c55e' },
  rechazado:  { label: 'Rechazados',  color: 'var(--color-error)' },
}

const PREVIEW_COUNT = 5

export default function AdminPage() {
  const navigate = useNavigate()
  const [stats,           setStats]           = useState(null)
  const [loading,         setLoading]         = useState(true)
  const [calificaciones,  setCalificaciones]  = useState([])
  const [loadingCals,     setLoadingCals]     = useState(true)

  useEffect(() => {
    obtenerEstadisticas()
      .then(data => setStats(data))
      .catch(() => {})
      .finally(() => setLoading(false))

    listarCalificaciones()
      .then(data => setCalificaciones(data))
      .catch(() => {})
      .finally(() => setLoadingCals(false))
  }, [])

  const totalIntercambios = stats
    ? Object.values(stats.intercambios_por_estado).reduce((a, b) => a + b, 0)
    : 0

  return (
    <div className="p-8 max-w-[1000px]">
      <h1 className="text-3xl font-bold text-on-surface mb-6">Panel de Administración</h1>

      {/* Cards globales */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {CARDS.map(c => (
          <Card key={c.key} elevated>
            <div className="flex items-center gap-3.5">
              <div
                className="w-11 h-11 rounded-[14px] flex items-center justify-center shrink-0"
                style={{ background: c.colorVar + '18' }}
              >
                <Icon name={c.icon} size={24} style={{ color: c.colorVar }} />
              </div>
              <div>
                <div className="text-2xl font-bold text-on-surface">
                  {loading ? '…' : (stats?.[c.key] ?? 0)}
                </div>
                <div className="text-[13px] text-on-surface-variant">{c.label}</div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Intercambios por estado */}
        <div>
          <h2 className="text-lg font-semibold mb-3.5">Estado por intercambios</h2>
          {loading ? (
            <div className="flex items-center gap-3 py-8 text-on-surface-variant text-sm">
              <Icon name="progress_activity" size={20} className="animate-spin" /> Cargando...
            </div>
          ) : totalIntercambios === 0 ? (
            <EmptyState icon="swap_horiz" title="Sin intercambios" subtitle="Todavía no hubo intercambios en la plataforma" />
          ) : (
            <Card>
              <div className="flex flex-col gap-3.5">
                {Object.entries(ESTADO_CONFIG).map(([key, cfg]) => {
                  const valor = stats?.intercambios_por_estado[key] ?? 0
                  const pct   = totalIntercambios > 0 ? (valor / totalIntercambios) * 100 : 0
                  return (
                    <div key={key}>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm text-on-surface">{cfg.label}</span>
                        <span className="text-sm font-bold text-on-surface">{valor}</span>
                      </div>
                      <div className="h-2 rounded-full bg-surface-variant overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{ width: `${pct}%`, background: cfg.color }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </Card>
          )}
        </div>

        {/* Top selecciones */}
        <div>
          <h2 className="text-lg font-semibold mb-3.5">Top selecciones más publicadas</h2>
          {loading ? (
            <div className="flex items-center gap-3 py-8 text-on-surface-variant text-sm">
              <Icon name="progress_activity" size={20} className="animate-spin" /> Cargando...
            </div>
          ) : !stats?.top_selecciones?.length ? (
            <EmptyState icon="bar_chart" title="Sin datos" subtitle="Las estadísticas de figuritas por selección aparecerán acá" />
          ) : (
            <Card>
              <div className="flex flex-col gap-2">
                {stats.top_selecciones.map((s, i) => (
                  <div key={s.seleccion} className="flex items-center gap-3 py-1">
                    <span
                      className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                      style={{ background: 'var(--color-primary-container)', color: 'var(--color-on-primary-container)' }}
                    >
                      {i + 1}
                    </span>
                    <span className="flex-1 text-sm text-on-surface">{s.seleccion}</span>
                    <span
                      className="text-xs font-semibold px-2 py-0.5 rounded-full"
                      style={{ background: 'var(--color-secondary-container)', color: 'var(--color-on-secondary-container)' }}
                    >
                      {s.cantidad} figurita{s.cantidad !== 1 ? 's' : ''}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Calificaciones */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-3.5">
          <h2 className="text-lg font-semibold">
            Calificaciones recientes
            {!loadingCals && calificaciones.length > 0 && (
              <span className="ml-2 text-sm font-normal text-on-surface-variant">({calificaciones.length} total)</span>
            )}
          </h2>
          {!loadingCals && calificaciones.length > 0 && (
            <Button variant="text" size="sm" icon="open_in_new" onClick={() => navigate('/admin/calificaciones')}>
              Ver todas
            </Button>
          )}
        </div>
        {loadingCals ? (
          <div className="flex items-center gap-3 py-8 text-on-surface-variant text-sm">
            <Icon name="progress_activity" size={20} className="animate-spin" /> Cargando...
          </div>
        ) : calificaciones.length === 0 ? (
          <EmptyState icon="star" title="Sin calificaciones" subtitle="Las calificaciones aparecerán acá cuando los usuarios califiquen sus intercambios" />
        ) : (
          <Card>
            <div className="flex flex-col divide-y divide-outline/20">
              {calificaciones.slice(-PREVIEW_COUNT).reverse().map(cal => (
                <div key={cal.id} className="flex items-start gap-4 py-3.5 first:pt-0 last:pb-0">
                  <Avatar name={cal.calificador_nombre} size={36} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="font-medium text-sm text-on-surface">{cal.calificador_nombre}</span>
                      <Icon name="arrow_forward" size={14} className="text-on-surface-variant" />
                      <span className="font-medium text-sm text-on-surface">{cal.calificado_nombre}</span>
                    </div>
                    <div className="flex items-center gap-0.5 mt-1">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <Icon
                          key={i}
                          name="star"
                          size={14}
                          style={{ color: i < cal.puntuacion ? 'var(--color-gold, #f59e0b)' : 'var(--color-outline)' }}
                        />
                      ))}
                      <span className="ml-1 text-xs text-on-surface-variant">{cal.puntuacion}/5</span>
                    </div>
                    {cal.comentario && (
                      <p className="text-sm text-on-surface-variant mt-1 italic">"{cal.comentario}"</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
            {calificaciones.length > PREVIEW_COUNT && (
              <button
                onClick={() => navigate('/admin/calificaciones')}
                className="w-full mt-3 pt-3 border-t border-outline/20 text-sm text-primary font-medium hover:text-primary/80 transition-colors text-center"
              >
                Ver las {calificaciones.length - PREVIEW_COUNT} restantes
              </button>
            )}
          </Card>
        )}
      </div>
    </div>
  )
}
