import { useState, useEffect, useRef } from 'react'
import { parseISO, format, isPast } from 'date-fns'
import { es } from 'date-fns/locale'
import Icon from '../components/ui/Icon'
import { getPartidos } from '../api/partidos'

const FASE_COLOR = {
  Final: {
    bg: 'bg-yellow-100 dark:bg-yellow-900/30',
    text: 'text-yellow-700 dark:text-yellow-300',
    dot: '#f59e0b',
  },
  Semifinal: {
    bg: 'bg-orange-100 dark:bg-orange-900/30',
    text: 'text-orange-600 dark:text-orange-300',
    dot: '#f97316',
  },
  Cuartos: {
    bg: 'bg-red-100 dark:bg-red-900/30',
    text: 'text-red-600 dark:text-red-300',
    dot: '#ef4444',
  },
  Dieciseisavos: {
    bg: 'bg-indigo-100 dark:bg-indigo-900/30',
    text: 'text-indigo-600 dark:text-indigo-300',
    dot: '#6366f1',
  },
  Octavos: {
    bg: 'bg-purple-100 dark:bg-purple-900/30',
    text: 'text-purple-600 dark:text-purple-300',
    dot: '#8b5cf6',
  },
  'Tercer puesto': {
    bg: 'bg-amber-100 dark:bg-amber-900/30',
    text: 'text-amber-600 dark:text-amber-300',
    dot: '#d97706',
  },
}

function faseBadge(fase) {
  const c = FASE_COLOR[fase]
  if (!c)
    return {
      bg: 'bg-primary-container',
      text: 'text-on-primary-container',
      dot: 'var(--color-primary)',
    }
  return c
}

function formatFecha(fechaStr) {
  return format(parseISO(fechaStr), "d 'de' MMM", { locale: es })
}

function esPasado(fechaStr) {
  return isPast(parseISO(fechaStr))
}

function SkeletonCard() {
  return (
    <div className="shrink-0 w-52 rounded-2xl border border-outline-variant p-3.5 flex flex-col gap-2 animate-pulse bg-surface-container-low">
      <div className="h-4 w-16 rounded-full bg-outline-variant" />
      <div className="h-3 w-24 rounded bg-outline-variant" />
      <div className="flex flex-col gap-1">
        <div className="h-4 w-28 rounded bg-outline-variant" />
        <div className="h-3 w-4 rounded bg-outline-variant" />
        <div className="h-4 w-28 rounded bg-outline-variant" />
      </div>
      <div className="h-3 w-32 rounded bg-outline-variant mt-auto pt-1" />
    </div>
  )
}

export default function WorldCupSchedule() {
  const scrollRef = useRef(null)
  const [partidos, setPartidos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Auto-scroll al primer partido de hoy (o al próximo si no hay hoy)
  useEffect(() => {
    if (!partidos.length || !scrollRef.current) return
    const hoy = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Argentina/Buenos_Aires' })
    const idx = partidos.findIndex((p) => p.fecha >= hoy)
    if (idx > 0) {
      // w-52 = 208px + gap-3 = 12px
      scrollRef.current.scrollTo({ left: idx * 220, behavior: 'smooth' })
    }
  }, [partidos])

  useEffect(() => {
    let cancelled = false
    getPartidos()
      .then((data) => {
        if (!cancelled) setPartidos(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err?.message || 'No se pudieron cargar los partidos')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  function scroll(dir) {
    scrollRef.current?.scrollBy({ left: dir * 680, behavior: 'smooth' })
  }

  return (
    <div className="mt-8">
      <div className="flex justify-between items-center mb-3.5">
        <div>
          <h2 className="text-lg font-semibold m-0">Partidos del Mundial 2026</h2>
          <p className="text-xs text-on-surface-variant mt-0.5">
            🇺🇸 USA · 🇨🇦 Canadá · 🇲🇽 México — 11 Jun – 19 Jul
          </p>
        </div>
        <div className="flex gap-1.5">
          <button
            onClick={() => scroll(-1)}
            className="w-8 h-8 rounded-full flex items-center justify-center bg-surface-container hover:bg-surface-variant transition-colors border-0 cursor-pointer text-on-surface-variant"
          >
            <Icon name="chevron_left" size={20} />
          </button>
          <button
            onClick={() => scroll(1)}
            className="w-8 h-8 rounded-full flex items-center justify-center bg-surface-container hover:bg-surface-variant transition-colors border-0 cursor-pointer text-on-surface-variant"
          >
            <Icon name="chevron_right" size={20} />
          </button>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex gap-3 overflow-x-auto pb-2 scrollbar-none"
        style={{ scrollSnapType: 'x mandatory' }}
      >
        {loading && Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}

        {error && (
          <div className="flex items-center gap-2 text-sm text-error py-4 px-1">
            <Icon name="error" size={18} />
            <span>{error}</span>
          </div>
        )}

        {!loading &&
          !error &&
          partidos.map((p) => {
            const { bg, text } = faseBadge(p.fase)
            const pasado = esPasado(p.fecha)
            const tieneResultado =
              p.goles_local !== null &&
              p.goles_local !== undefined &&
              p.goles_visitante !== null &&
              p.goles_visitante !== undefined

            return (
              <div
                key={p.id}
                className={`shrink-0 w-52 rounded-2xl border border-outline-variant p-3.5 flex flex-col gap-2 transition-opacity ${pasado ? 'opacity-50' : 'bg-surface-container-low'}`}
                style={{ scrollSnapAlign: 'start' }}
              >
                {/* Fase badge */}
                <span
                  className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full self-start ${bg} ${text}`}
                >
                  {p.fase}
                </span>

                {/* Fecha y hora */}
                <div className="flex items-center gap-1.5 text-xs text-on-surface-variant">
                  <span className="font-semibold text-on-surface">{formatFecha(p.fecha)}</span>
                  <span>·</span>
                  <span>{p.hora} hs</span>
                </div>

                {/* Equipos y resultado */}
                <div className="flex flex-col gap-1">
                  <div className="font-semibold text-sm text-on-surface truncate">{p.local}</div>
                  <div className="flex items-center gap-2">
                    <div className="text-[10px] text-on-surface-variant font-medium uppercase tracking-wide">
                      vs
                    </div>
                    {tieneResultado && (
                      <div className="text-xs font-bold text-on-surface tabular-nums">
                        {p.goles_local} – {p.goles_visitante}
                      </div>
                    )}
                  </div>
                  <div className="font-semibold text-sm text-on-surface truncate">{p.visitante}</div>
                </div>

                {/* Estadio */}
                {p.estadio && (
                  <div className="flex items-start gap-1 mt-auto pt-1 border-t border-outline-variant/50">
                    <Icon
                      name="stadium"
                      size={13}
                      className="text-on-surface-variant shrink-0 mt-0.5"
                    />
                    <div className="text-2xs text-on-surface-variant leading-tight truncate">
                      {p.estadio}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
      </div>
    </div>
  )
}
