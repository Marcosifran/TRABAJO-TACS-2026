import { useRef } from 'react'
import Icon from '../components/ui/Icon'

const PARTIDOS = [
  // ── Grupo A ──────────────────────────────────────────────
  { id:  1, fase: 'Grupo A', fecha: '2026-06-11', hora: '20:00', local: 'México',        visitante: 'Bolivia',       estadio: 'Estadio Azteca',              ciudad: 'Ciudad de México' },
  { id:  2, fase: 'Grupo A', fecha: '2026-06-15', hora: '17:00', local: 'México',        visitante: 'Panamá',        estadio: 'Estadio Akron',               ciudad: 'Guadalajara' },
  // ── Grupo B ──────────────────────────────────────────────
  { id:  3, fase: 'Grupo B', fecha: '2026-06-12', hora: '13:00', local: 'USA',           visitante: 'Jamaica',       estadio: 'SoFi Stadium',                ciudad: 'Los Ángeles' },
  { id:  4, fase: 'Grupo B', fecha: '2026-06-16', hora: '16:00', local: 'USA',           visitante: 'Ecuador',       estadio: 'AT&T Stadium',                ciudad: 'Dallas' },
  // ── Grupo C ──────────────────────────────────────────────
  { id:  5, fase: 'Grupo C', fecha: '2026-06-12', hora: '19:00', local: 'Canadá',        visitante: 'Marruecos',     estadio: 'BMO Field',                   ciudad: 'Toronto' },
  { id:  6, fase: 'Grupo C', fecha: '2026-06-17', hora: '13:00', local: 'Canadá',        visitante: 'Venezuela',     estadio: 'BC Place',                    ciudad: 'Vancouver' },
  // ── Grupo D ──────────────────────────────────────────────
  { id:  7, fase: 'Grupo D', fecha: '2026-06-13', hora: '13:00', local: 'España',        visitante: 'Senegal',       estadio: 'MetLife Stadium',             ciudad: 'Nueva York / Nueva Jersey' },
  { id:  8, fase: 'Grupo D', fecha: '2026-06-17', hora: '16:00', local: 'España',        visitante: 'Países Bajos',  estadio: 'Lincoln Financial Field',     ciudad: 'Filadelfia' },
  // ── Grupo E ──────────────────────────────────────────────
  { id:  9, fase: 'Grupo E', fecha: '2026-06-13', hora: '16:00', local: 'Francia',       visitante: 'Australia',     estadio: 'AT&T Stadium',                ciudad: 'Dallas' },
  { id: 10, fase: 'Grupo E', fecha: '2026-06-18', hora: '13:00', local: 'Francia',       visitante: 'Colombia',      estadio: 'Hard Rock Stadium',           ciudad: 'Miami' },
  // ── Grupo F ──────────────────────────────────────────────
  { id: 11, fase: 'Grupo F', fecha: '2026-06-13', hora: '20:00', local: 'Brasil',        visitante: 'Uruguay',       estadio: 'Estadio BBVA',                ciudad: 'Monterrey' },
  { id: 12, fase: 'Grupo F', fecha: '2026-06-18', hora: '19:00', local: 'Brasil',        visitante: 'Nigeria',       estadio: 'Mercedes-Benz Stadium',       ciudad: 'Atlanta' },
  // ── Grupo G ──────────────────────────────────────────────
  { id: 13, fase: 'Grupo G', fecha: '2026-06-14', hora: '13:00', local: 'Argentina',     visitante: 'Chile',         estadio: 'Arrowhead Stadium',           ciudad: 'Kansas City' },
  { id: 14, fase: 'Grupo G', fecha: '2026-06-18', hora: '16:00', local: 'Argentina',     visitante: 'Perú',          estadio: 'Empower Field at Mile High',  ciudad: 'Denver' },
  // ── Grupo H ──────────────────────────────────────────────
  { id: 15, fase: 'Grupo H', fecha: '2026-06-14', hora: '16:00', local: 'Alemania',      visitante: 'Japón',         estadio: 'Empower Field at Mile High',  ciudad: 'Denver' },
  { id: 16, fase: 'Grupo H', fecha: '2026-06-19', hora: '13:00', local: 'Alemania',      visitante: 'Corea del Sur', estadio: 'Lumen Field',                 ciudad: 'Seattle' },
  // ── Grupo I ──────────────────────────────────────────────
  { id: 17, fase: 'Grupo I', fecha: '2026-06-14', hora: '19:00', local: 'Portugal',      visitante: 'Nigeria',       estadio: 'Gillette Stadium',            ciudad: 'Boston' },
  { id: 18, fase: 'Grupo I', fecha: '2026-06-19', hora: '16:00', local: 'Portugal',      visitante: 'Dinamarca',     estadio: 'Commanders Stadium',          ciudad: 'Washington D.C.' },
  // ── Grupo J ──────────────────────────────────────────────
  { id: 19, fase: 'Grupo J', fecha: '2026-06-15', hora: '13:00', local: 'Inglaterra',    visitante: 'Irán',          estadio: 'Gillette Stadium',            ciudad: 'Boston' },
  { id: 20, fase: 'Grupo J', fecha: '2026-06-19', hora: '20:00', local: 'Inglaterra',    visitante: 'Bélgica',       estadio: 'MetLife Stadium',             ciudad: 'Nueva York / Nueva Jersey' },
  // ── Grupo K ──────────────────────────────────────────────
  { id: 21, fase: 'Grupo K', fecha: '2026-06-15', hora: '16:00', local: 'Colombia',      visitante: 'Ghana',         estadio: 'SoFi Stadium',                ciudad: 'Los Ángeles' },
  { id: 22, fase: 'Grupo K', fecha: '2026-06-20', hora: '13:00', local: 'Colombia',      visitante: 'Costa de Marfil',estadio: 'Levi\'s Stadium',            ciudad: 'San Francisco' },
  // ── Grupo L ──────────────────────────────────────────────
  { id: 23, fase: 'Grupo L', fecha: '2026-06-15', hora: '20:00', local: 'Croacia',       visitante: 'Turquía',       estadio: 'Mercedes-Benz Stadium',       ciudad: 'Atlanta' },
  { id: 24, fase: 'Grupo L', fecha: '2026-06-20', hora: '16:00', local: 'Croacia',       visitante: 'Serbia',        estadio: 'Hard Rock Stadium',           ciudad: 'Miami' },
  // ── Grupo M ──────────────────────────────────────────────
  { id: 25, fase: 'Grupo M', fecha: '2026-06-16', hora: '13:00', local: 'Bélgica',       visitante: 'Suiza',         estadio: 'Lumen Field',                 ciudad: 'Seattle' },
  { id: 26, fase: 'Grupo M', fecha: '2026-06-20', hora: '19:00', local: 'Bélgica',       visitante: 'Australia',     estadio: 'BC Place',                    ciudad: 'Vancouver' },
  // ── Grupo N ──────────────────────────────────────────────
  { id: 27, fase: 'Grupo N', fecha: '2026-06-16', hora: '16:00', local: 'Países Bajos',  visitante: 'Arabia Saudita',estadio: 'Arrowhead Stadium',           ciudad: 'Kansas City' },
  { id: 28, fase: 'Grupo N', fecha: '2026-06-21', hora: '13:00', local: 'Países Bajos',  visitante: 'Camerún',       estadio: 'BMO Field',                   ciudad: 'Toronto' },
  // ── Grupo O ──────────────────────────────────────────────
  { id: 29, fase: 'Grupo O', fecha: '2026-06-16', hora: '20:00', local: 'Uruguay',       visitante: 'Corea del Sur', estadio: 'Lincoln Financial Field',     ciudad: 'Filadelfia' },
  { id: 30, fase: 'Grupo O', fecha: '2026-06-21', hora: '16:00', local: 'Uruguay',       visitante: 'Ghana',         estadio: 'Commanders Stadium',          ciudad: 'Washington D.C.' },
  // ── Grupo P ──────────────────────────────────────────────
  { id: 31, fase: 'Grupo P', fecha: '2026-06-17', hora: '20:00', local: 'Polonia',       visitante: 'Arabia Saudita',estadio: 'Estadio Azteca',              ciudad: 'Ciudad de México' },
  { id: 32, fase: 'Grupo P', fecha: '2026-06-21', hora: '20:00', local: 'Polonia',       visitante: 'Irán',          estadio: 'Estadio BBVA',                ciudad: 'Monterrey' },
  // ── Octavos de Final ─────────────────────────────────────
  { id: 33, fase: 'Octavos', fecha: '2026-07-02', hora: '16:00', local: '1.º Grupo A',   visitante: '2.º Grupo B',   estadio: 'MetLife Stadium',             ciudad: 'Nueva York / Nueva Jersey' },
  { id: 34, fase: 'Octavos', fecha: '2026-07-03', hora: '13:00', local: '1.º Grupo C',   visitante: '2.º Grupo D',   estadio: 'AT&T Stadium',                ciudad: 'Dallas' },
  { id: 35, fase: 'Octavos', fecha: '2026-07-03', hora: '20:00', local: '1.º Grupo E',   visitante: '2.º Grupo F',   estadio: 'SoFi Stadium',                ciudad: 'Los Ángeles' },
  { id: 36, fase: 'Octavos', fecha: '2026-07-04', hora: '16:00', local: '1.º Grupo G',   visitante: '2.º Grupo H',   estadio: 'Arrowhead Stadium',           ciudad: 'Kansas City' },
  // ── Cuartos de Final ─────────────────────────────────────
  { id: 37, fase: 'Cuartos', fecha: '2026-07-10', hora: '20:00', local: 'Por definir',   visitante: 'Por definir',   estadio: 'MetLife Stadium',             ciudad: 'Nueva York / Nueva Jersey' },
  { id: 38, fase: 'Cuartos', fecha: '2026-07-11', hora: '20:00', local: 'Por definir',   visitante: 'Por definir',   estadio: 'SoFi Stadium',                ciudad: 'Los Ángeles' },
  // ── Semifinales ──────────────────────────────────────────
  { id: 39, fase: 'Semifinal', fecha: '2026-07-14', hora: '20:00', local: 'Por definir', visitante: 'Por definir',   estadio: 'AT&T Stadium',                ciudad: 'Dallas' },
  { id: 40, fase: 'Semifinal', fecha: '2026-07-15', hora: '20:00', local: 'Por definir', visitante: 'Por definir',   estadio: 'MetLife Stadium',             ciudad: 'Nueva York / Nueva Jersey' },
  // ── Final ────────────────────────────────────────────────
  { id: 41, fase: 'Final',   fecha: '2026-07-19', hora: '12:00', local: 'Por definir',   visitante: 'Por definir',   estadio: 'MetLife Stadium',             ciudad: 'Nueva York / Nueva Jersey' },
]

PARTIDOS.sort((a, b) => (a.fecha + a.hora).localeCompare(b.fecha + b.hora))

const FASE_COLOR = {
  'Final':     { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-300', dot: '#f59e0b' },
  'Semifinal': { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-600 dark:text-orange-300', dot: '#f97316' },
  'Cuartos':   { bg: 'bg-red-100 dark:bg-red-900/30',       text: 'text-red-600 dark:text-red-300',       dot: '#ef4444' },
  'Octavos':   { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-600 dark:text-purple-300', dot: '#8b5cf6' },
}

function faseBadge(fase) {
  const c = FASE_COLOR[fase]
  if (!c) return { bg: 'bg-primary-container', text: 'text-on-primary-container', dot: 'var(--color-primary)' }
  return c
}

function formatFecha(fechaStr) {
  const [y, m, d] = fechaStr.split('-')
  const meses = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
  return `${parseInt(d)} ${meses[parseInt(m)]}`
}

function esPasado(fechaStr) {
  return new Date(fechaStr) < new Date()
}

export default function WorldCupSchedule() {
  const scrollRef = useRef(null)

  function scroll(dir) {
    scrollRef.current?.scrollBy({ left: dir * 680, behavior: 'smooth' })
  }

  return (
    <div className="mt-8">
      <div className="flex justify-between items-center mb-3.5">
        <div>
          <h2 className="text-lg font-semibold m-0">Partidos del Mundial 2026</h2>
          <p className="text-xs text-on-surface-variant mt-0.5">🇺🇸 USA · 🇨🇦 Canadá · 🇲🇽 México — 11 Jun – 19 Jul</p>
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
        {PARTIDOS.map(p => {
          const { bg, text, dot } = faseBadge(p.fase)
          const pasado = esPasado(p.fecha)
          return (
            <div
              key={p.id}
              className={`shrink-0 w-52 rounded-2xl border border-outline-variant p-3.5 flex flex-col gap-2 transition-opacity ${pasado ? 'opacity-50' : 'bg-surface-container-low'}`}
              style={{ scrollSnapAlign: 'start' }}
            >
              {/* Fase badge */}
              <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full self-start ${bg} ${text}`}>
                {p.fase}
              </span>

              {/* Fecha y hora */}
              <div className="flex items-center gap-1.5 text-xs text-on-surface-variant">
                <span className="font-semibold text-on-surface">{formatFecha(p.fecha)}</span>
                <span>·</span>
                <span>{p.hora} hs</span>
              </div>

              {/* Equipos */}
              <div className="flex flex-col gap-1">
                <div className="font-semibold text-sm text-on-surface truncate">{p.local}</div>
                <div className="text-[10px] text-on-surface-variant font-medium uppercase tracking-wide">vs</div>
                <div className="font-semibold text-sm text-on-surface truncate">{p.visitante}</div>
              </div>

              {/* Estadio */}
              <div className="flex items-start gap-1 mt-auto pt-1 border-t border-outline-variant/50">
                <Icon name="stadium" size={13} className="text-on-surface-variant shrink-0 mt-0.5" />
                <div>
                  <div className="text-[11px] text-on-surface-variant leading-tight">{p.estadio}</div>
                  <div className="text-[10px] text-on-surface-variant/70 leading-tight">{p.ciudad}</div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
