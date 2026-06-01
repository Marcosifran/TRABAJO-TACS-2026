import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../components/ui/Card'
import Icon from '../components/ui/Icon'
import Avatar from '../components/ui/Avatar'
import Button from '../components/ui/Button'
import EmptyState from '../components/ui/EmptyState'
import { listarCalificaciones } from '../api/admin'

function StarFilter({ value, onChange }) {
  return (
    <div className="flex gap-1">
      {[0, 1, 2, 3, 4, 5].map(n => (
        <button
          key={n}
          onClick={() => onChange(n === value ? 0 : n)}
          className={`px-2.5 py-1 rounded-full text-xs font-semibold border transition-colors ${
            value === n
              ? 'bg-primary text-on-primary border-primary'
              : 'bg-surface border-outline text-on-surface-variant hover:bg-surface-container'
          }`}
        >
          {n === 0 ? 'Todas' : `${n}★`}
        </button>
      ))}
    </div>
  )
}

export default function AdminCalificacionesPage() {
  const navigate = useNavigate()
  const [calificaciones, setCalificaciones] = useState([])
  const [loading, setLoading] = useState(true)

  const [filtroCalificador, setFiltroCalificador] = useState('')
  const [filtroCalificado,  setFiltroCalificado]  = useState('')
  const [filtroPuntuacion,  setFiltroPuntuacion]  = useState(0)
  const [filtroComentario,  setFiltroComentario]  = useState(false)

  useEffect(() => {
    listarCalificaciones()
      .then(data => setCalificaciones(data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const calificadores = useMemo(
    () => [...new Set(calificaciones.map(c => c.calificador_nombre))].sort(),
    [calificaciones]
  )
  const calificados = useMemo(
    () => [...new Set(calificaciones.map(c => c.calificado_nombre))].sort(),
    [calificaciones]
  )

  const filtradas = useMemo(() => {
    return calificaciones
      .filter(c => !filtroCalificador || c.calificador_nombre === filtroCalificador)
      .filter(c => !filtroCalificado  || c.calificado_nombre  === filtroCalificado)
      .filter(c => filtroPuntuacion === 0 || c.puntuacion === filtroPuntuacion)
      .filter(c => !filtroComentario || !!c.comentario)
      .slice()
      .reverse()
  }, [calificaciones, filtroCalificador, filtroCalificado, filtroPuntuacion, filtroComentario])

  const hayFiltros = filtroCalificador || filtroCalificado || filtroPuntuacion > 0 || filtroComentario

  function limpiarFiltros() {
    setFiltroCalificador('')
    setFiltroCalificado('')
    setFiltroPuntuacion(0)
    setFiltroComentario(false)
  }

  const selectClass = "bg-surface border border-outline rounded-lg px-3 py-1.5 text-sm text-on-surface focus:outline-primary"

  return (
    <div className="p-8 max-w-[900px]">
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => navigate('/admin')}
          className="flex items-center justify-center w-9 h-9 rounded-full hover:bg-surface-container transition-colors"
        >
          <Icon name="arrow_back" size={20} className="text-on-surface-variant" />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-on-surface">Calificaciones</h1>
          {!loading && (
            <p className="text-sm text-on-surface-variant mt-0.5">
              {filtradas.length} de {calificaciones.length} calificaciones
            </p>
          )}
        </div>
      </div>

      {/* Filtros */}
      <Card className="mb-5">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2 flex-1 min-w-[180px]">
              <Icon name="person" size={16} className="text-on-surface-variant shrink-0" />
              <select
                className={selectClass + ' flex-1'}
                value={filtroCalificador}
                onChange={e => setFiltroCalificador(e.target.value)}
              >
                <option value="">Calificador — todos</option>
                {calificadores.map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
            <div className="flex items-center gap-2 flex-1 min-w-[180px]">
              <Icon name="person_check" size={16} className="text-on-surface-variant shrink-0" />
              <select
                className={selectClass + ' flex-1'}
                value={filtroCalificado}
                onChange={e => setFiltroCalificado(e.target.value)}
              >
                <option value="">Calificado — todos</option>
                {calificados.map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={filtroComentario}
                onChange={e => setFiltroComentario(e.target.checked)}
                className="w-4 h-4 accent-primary"
              />
              <span className="text-sm text-on-surface-variant">Con comentario</span>
            </label>
            {hayFiltros && (
              <Button variant="text" size="sm" icon="filter_list_off" onClick={limpiarFiltros}>
                Limpiar
              </Button>
            )}
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-on-surface-variant font-medium uppercase tracking-wide shrink-0">Puntuación</span>
            <StarFilter value={filtroPuntuacion} onChange={setFiltroPuntuacion} />
          </div>
        </div>
      </Card>

      {/* Lista */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Icon name="progress_activity" size={32} className="animate-spin text-on-surface-variant" />
        </div>
      ) : filtradas.length === 0 ? (
        <EmptyState
          icon="star"
          title={hayFiltros ? 'Sin resultados para este filtro' : 'Sin calificaciones'}
          subtitle={hayFiltros ? 'Probá con otros criterios de búsqueda' : 'Todavía no se registraron calificaciones'}
        />
      ) : (
        <Card>
          <div className="flex flex-col divide-y divide-outline/20">
            {filtradas.map(cal => (
              <div key={cal.id} className="flex items-start gap-4 py-4 first:pt-0 last:pb-0">
                <Avatar name={cal.calificador_nombre} size={40} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="font-semibold text-sm text-on-surface">{cal.calificador_nombre}</span>
                    <Icon name="arrow_forward" size={14} className="text-on-surface-variant" />
                    <span className="font-semibold text-sm text-on-surface">{cal.calificado_nombre}</span>
                  </div>
                  <div className="flex items-center gap-0.5 mt-1.5">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Icon
                        key={i}
                        name="star"
                        size={16}
                        style={{ color: i < cal.puntuacion ? 'var(--color-gold, #f59e0b)' : 'var(--color-outline)' }}
                      />
                    ))}
                    <span className="ml-1.5 text-xs font-semibold text-on-surface-variant">{cal.puntuacion}/5</span>
                  </div>
                  {cal.comentario ? (
                    <p className="text-sm text-on-surface mt-1.5 italic">"{cal.comentario}"</p>
                  ) : (
                    <p className="text-xs text-on-surface-variant mt-1.5">Sin comentario</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
