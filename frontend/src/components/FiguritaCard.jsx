import Icon from './ui/Icon'
import Avatar from './ui/Avatar'
import Button from './ui/Button'

const FLAG_COLORS = {
  Argentina:      ['#74ACDF', '#FFFFFF', '#74ACDF'],
  Brasil:         ['#009C3B', '#FFDF00', '#009C3B'],
  Francia:        ['#002395', '#FFFFFF', '#ED2939'],
  Alemania:       ['#000000', '#DD0000', '#FFCE00'],
  España:         ['#AA151B', '#F1BF00', '#AA151B'],
  Inglaterra:     ['#FFFFFF', '#CE1124', '#FFFFFF'],
  Portugal:       ['#006600', '#FF0000', '#006600'],
  México:         ['#006847', '#FFFFFF', '#CE1126'],
  USA:            ['#002868', '#FFFFFF', '#BF0A30'],
  Canadá:         ['#FF0000', '#FFFFFF', '#FF0000'],
}
const CAT_ICONS = {
  Escudo: 'shield', Jugador: 'person', Estadio: 'stadium',
  Leyenda: 'star', Especial: 'auto_awesome',
}

function flagGradient(seleccion) {
  const c = FLAG_COLORS[seleccion] || ['#666', '#999', '#666']
  return `linear-gradient(135deg, ${c[0]}99, ${c[1]}99, ${c[2]}99)`
}
function cardGradient(seleccion) {
  const c = FLAG_COLORS[seleccion] || ['#666', '#999', '#666']
  return `linear-gradient(135deg, ${c[0]}, ${c[2]})`
}

export default function FiguritaCard({ figurita, onTrade, compact = false }) {
  if (compact) {
    return (
      <div className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl bg-surface-container cursor-pointer hover:bg-surface-variant transition-colors">
        <div
          className="w-10 h-12 rounded-md shrink-0 flex items-center justify-center"
          style={{ background: cardGradient(figurita.seleccion) }}
        >
          <span className="text-base font-bold text-white drop-shadow">#{figurita.numero}</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold text-on-surface truncate">{figurita.jugador}</div>
          <div className="text-xs text-on-surface-variant">{figurita.seleccion}</div>
        </div>
        {figurita.cantidad != null && (
          <span className="text-xs text-on-surface-variant bg-surface-variant px-2 py-0.5 rounded-full">
            x{figurita.cantidad}
          </span>
        )}
      </div>
    )
  }

  return (
    <div className="rounded-2xl overflow-hidden bg-surface-container-low border border-outline-variant transition-all duration-200 hover:-translate-y-0.5 hover:shadow-elev-2 cursor-pointer">
      {/* Header */}
      <div
        className="h-24 flex items-center justify-center relative"
        style={{ background: flagGradient(figurita.seleccion) }}
      >
        <div
          className="w-14 h-[68px] rounded-lg flex flex-col items-center justify-center shadow-md border-2 border-white/50"
          style={{ background: cardGradient(figurita.seleccion) }}
        >
          <span className="text-xl font-extrabold text-white drop-shadow">#{figurita.numero}</span>
          <Icon
            name={CAT_ICONS[figurita.categoria] || 'style'}
            size={14}
            className="text-white/80"
          />
        </div>
        {figurita.tipo === 'subasta' && (
          <div className="absolute top-2 right-2 bg-gold text-black text-[11px] font-bold px-2 py-0.5 rounded-md">
            SUBASTA
          </div>
        )}
      </div>

      {/* Body */}
      <div className="p-3.5">
        <div className="text-[15px] font-semibold text-on-surface truncate mb-0.5">{figurita.jugador}</div>
        <div className="text-[13px] text-on-surface-variant mb-2">{figurita.seleccion} · {figurita.categoria}</div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Avatar name={figurita.owner || '?'} size={22} />
            <span className="text-xs text-on-surface-variant">{figurita.owner}</span>
          </div>
          {figurita.cantidad != null && (
            <span className="text-xs font-semibold text-primary">x{figurita.cantidad}</span>
          )}
        </div>
        {onTrade && (
          <Button
            variant="tonal"
            size="sm"
            icon="swap_horiz"
            onClick={e => { e.stopPropagation(); onTrade(figurita) }}
            className="w-full mt-2.5 justify-center"
          >
            {figurita.tipo === 'subasta' ? 'Ofertar' : 'Proponer intercambio'}
          </Button>
        )}
      </div>
    </div>
  )
}
