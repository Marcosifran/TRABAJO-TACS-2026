import { useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import useSWR from 'swr'
import Icon from '../components/ui/Icon'
import EmptyState from '../components/ui/EmptyState'
import Button from '../components/ui/Button'
import { useUser } from '../context/UserContext'
import { formatTiempoRestante, isAuctionActive } from '../utils/auctionTime'

const storageKey = (userId) => `figuswap-alertas-leidas:user-${userId}`
const FADE_MS = 400

function loadLeidas(userId) {
  try {
    return new Set(JSON.parse(localStorage.getItem(storageKey(userId)) || '[]'))
  } catch {
    return new Set()
  }
}
function saveLeidas(set, userId) {
  localStorage.setItem(storageKey(userId), JSON.stringify([...set]))
}

export default function NotificationsPage() {
  const navigate = useNavigate()
  const { user, users } = useUser()
  const fadeTimers = useRef(new Map())
  const userId = users.indexOf(user) + 1

  const [leidas, setLeidas] = useState(() => loadLeidas(userId))
  const [fading, setFading] = useState(new Set())

  const { data: intercambiosData, isLoading: loadingTrades } = useSWR(['/intercambios/', userId])
  const { data: sugerenciasData = [], isLoading: loadingSugs } = useSWR([
    '/publicaciones/sugerencias',
    userId,
  ])
  const { data: subastasData = [], isLoading: loadingSubs } = useSWR('/subastas')
  const { data: todasPubs = [] } = useSWR('/publicaciones?incluir_propias=true')

  const pubsMap = {}
  todasPubs.forEach((p) => { pubsMap[p.id] = p })

  const loading = loadingTrades || loadingSugs || loadingSubs

  const propuestas = intercambiosData?.recibidos?.filter((i) => i.estado === 'pendiente') || []
  const sugerencias = sugerenciasData
  const ahora = Date.now()
  const subastas = subastasData.filter((s) => {
    if (!isAuctionActive(s, ahora)) return false
    const ms = new Date(s.fin).getTime() - ahora
    return ms < 24 * 3600 * 1000
  })

  // Limpia los timers de fade al desmontar
  useRef((() => {
    return () => fadeTimers.current.forEach(clearTimeout)
  })())

  const dismiss = useCallback(
    (id) => {
      setFading((prev) => new Set([...prev, id]))
      const tid = setTimeout(() => {
        setLeidas((prev) => {
          const next = new Set([...prev, id])
          saveLeidas(next, userId)
          return next
        })
        setFading((prev) => {
          const s = new Set(prev)
          s.delete(id)
          return s
        })
        fadeTimers.current.delete(id)
      }, FADE_MS)
      fadeTimers.current.set(id, tid)
    },
    [userId],
  )

  function dismissAll() {
    const ids = [
      ...propuestas.map((p) => `trade-${p.id}`),
      ...sugerencias.map((s) => `sug-${s.publicacion.id}`),
      ...subastas.map((s) => `auct-${s.id}`),
    ]
    setFading(new Set(ids))
    const tid = setTimeout(() => {
      setLeidas((prev) => {
        const next = new Set([...prev, ...ids])
        saveLeidas(next, userId)
        return next
      })
      setFading(new Set())
    }, FADE_MS)
    fadeTimers.current.set('dismissAll', tid)
  }

  const propuestasVis = propuestas.filter((p) => !leidas.has(`trade-${p.id}`))
  const sugerenciasVis = sugerencias.filter((s) => !leidas.has(`sug-${s.publicacion.id}`))
  const subastasVis = subastas.filter((s) => !leidas.has(`auct-${s.id}`))
  const total = propuestasVis.length + sugerenciasVis.length + subastasVis.length

  function alertClass(id) {
    return `transition-all duration-[400ms] ${fading.has(id) ? 'opacity-0 scale-95' : 'opacity-100 scale-100'}`
  }

  return (
    <div className="p-8 max-w-[700px]">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-on-surface m-0">Alertas</h1>
          {!loading && (
            <p className="mt-1 text-on-surface-variant text-sm">
              {total} {total === 1 ? 'alerta activa' : 'alertas activas'}
            </p>
          )}
        </div>
        {!loading && total > 0 && (
          <Button variant="text" size="sm" onClick={dismissAll}>
            Marcar todo leído
          </Button>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center gap-3 py-16 text-on-surface-variant">
          <Icon name="progress_activity" size={24} className="animate-spin" />
          Cargando...
        </div>
      ) : total === 0 ? (
        <EmptyState
          icon="notifications_off"
          title="Sin alertas por ahora"
          subtitle="Te notificaremos cuando aparezca una figurita que buscás, cuando recibas una propuesta o cuando una subasta esté por finalizar"
        />
      ) : (
        <div className="flex flex-col gap-7">
          {propuestasVis.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-on-surface-variant uppercase tracking-wide mb-3 flex items-center gap-2">
                <Icon name="swap_horiz" size={16} className="text-tertiary" />
                Propuestas recibidas ({propuestasVis.length})
              </h2>
              <div className="flex flex-col gap-2">
                {propuestasVis.map((p) => (
                  <div
                    key={p.id}
                    className={`p-4 rounded-2xl border border-outline-variant bg-surface-container flex items-center gap-3 ${alertClass(`trade-${p.id}`)}`}
                  >
                    <div className="bg-tertiary-container rounded-full p-2 shrink-0">
                      <Icon name="swap_horiz" size={18} className="text-tertiary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-semibold text-on-surface">
                        {users[p.propuesto_por - 1]?.nombre ?? `Usuario ${p.propuesto_por}`} quiere
                        intercambiar
                      </div>
                      <div className="text-xs text-on-surface-variant mt-0.5">
                        Ofrece: {p.figuritas_ofrecidas.map((n) => `#${n}`).join(', ')} · Solicita: #
                        {p.figurita_solicitada}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="tonal"
                      onClick={() => navigate('/intercambios', { state: { tab: 'recibidas' } })}
                    >
                      Ver
                    </Button>
                    <button
                      onClick={() => dismiss(`trade-${p.id}`)}
                      className="p-1 rounded-full hover:bg-surface-variant transition-colors border-0 bg-transparent cursor-pointer text-on-surface-variant shrink-0"
                      title="Marcar como leída"
                    >
                      <Icon name="close" size={16} />
                    </button>
                  </div>
                ))}
              </div>
            </section>
          )}

          {sugerenciasVis.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-on-surface-variant uppercase tracking-wide mb-3 flex items-center gap-2">
                <Icon name="auto_awesome" size={16} className="text-primary" />
                Sugerencias de intercambio ({sugerenciasVis.length})
              </h2>
              <div className="flex flex-col gap-2">
                {sugerenciasVis.map((s) => (
                  <div
                    key={s.publicacion.id}
                    className={`p-4 rounded-2xl border border-outline-variant bg-surface-container flex items-center gap-3 ${alertClass(`sug-${s.publicacion.id}`)}`}
                  >
                    <div className="bg-primary-container rounded-full p-2 shrink-0">
                      <Icon name="auto_awesome" size={18} className="text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-semibold text-on-surface">
                        #{s.publicacion.numero} {s.publicacion.jugador} ({s.publicacion.equipo})
                      </div>
                      <div className="text-xs text-on-surface-variant mt-0.5">
                        Ofrecida por {s.ofrecida_por} · Cubre tu faltante #{s.cubre_tu_faltante}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="tonal"
                      onClick={() => navigate('/intercambios', { state: { tab: 'sugerencias' } })}
                    >
                      Ver
                    </Button>
                    <button
                      onClick={() => dismiss(`sug-${s.publicacion.id}`)}
                      className="p-1 rounded-full hover:bg-surface-variant transition-colors border-0 bg-transparent cursor-pointer text-on-surface-variant shrink-0"
                      title="Marcar como leída"
                    >
                      <Icon name="close" size={16} />
                    </button>
                  </div>
                ))}
              </div>
            </section>
          )}

          {subastasVis.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-on-surface-variant uppercase tracking-wide mb-3 flex items-center gap-2">
                <Icon name="gavel" size={16} className="text-secondary" />
                Subastas por finalizar ({subastasVis.length})
              </h2>
              <div className="flex flex-col gap-2">
                {subastasVis.map((s) => (
                  <div
                    key={s.id}
                    className={`p-4 rounded-2xl border border-outline-variant bg-surface-container flex items-center gap-3 ${alertClass(`auct-${s.id}`)}`}
                  >
                    <div className="bg-secondary-container rounded-full p-2 shrink-0">
                      <Icon name="gavel" size={18} className="text-secondary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-semibold text-on-surface">
                        {pubsMap[s.figurita_id]
                          ? `#${pubsMap[s.figurita_id].numero} ${pubsMap[s.figurita_id].jugador} (${pubsMap[s.figurita_id].equipo})`
                          : `Subasta #${s.id}`}
                      </div>
                      <div className="text-xs text-on-surface-variant mt-0.5">
                        De {users[s.usuario_id - 1]?.nombre ?? `Usuario ${s.usuario_id}`} · Cierra en {formatTiempoRestante(s.fin)}
                      </div>
                    </div>
                    <Button size="sm" variant="tonal" onClick={() => navigate('/subastas')}>
                      Ver
                    </Button>
                    <button
                      onClick={() => dismiss(`auct-${s.id}`)}
                      className="p-1 rounded-full hover:bg-surface-variant transition-colors border-0 bg-transparent cursor-pointer text-on-surface-variant shrink-0"
                      title="Marcar como leída"
                    >
                      <Icon name="close" size={16} />
                    </button>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  )
}
