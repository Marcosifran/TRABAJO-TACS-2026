import { useState, useEffect } from 'react'
import TiltCard from './TiltCard'
import Icon from './ui/Icon'
import Avatar from './ui/Avatar'
import Button from './ui/Button'
import FiguritaRow from './FiguritaRow'
import { getMaestroJugador } from '../api/maestro'

const FLAG_COLORS = {
  Germany:        ['#000000', '#DD0000', '#FFCE00'],
  Colombia:       ['#FCD116', '#003893', '#CE1126'],
  Haiti:          ['#00209F', '#D21034', '#00209F'],
  Paraguay:       ['#D52B1E', '#FFFFFF', '#0038A8'],
  "Saudi Arabia": ['#006C35', '#FFFFFF', '#006C35'],
  "South Korea": ['#FFFFFF', '#CD2E3A', '#0047A0'],
  England:        ['#FFFFFF', '#CE1124', '#FFFFFF'],
  Portugal:       ['#006600', '#FF0000', '#006600'],
  Algeria:        ['#006233', '#FFFFFF', '#D21034'],
  "Ivory Coast": ['#F77F00', '#FFFFFF', '#009E60'],
  Iraq:           ['#CE1126', '#FFFFFF', '#000000'],
  "Czech Republic": ['#FFFFFF', '#11457E', '#D7141A'],
  Argentina:      ['#74ACDF', '#FFFFFF', '#74ACDF'],
  Croatia:        ['#FF0000', '#FFFFFF', '#171796'],
  Iran:           ['#239F40', '#FFFFFF', '#DA0000'],
  "DR Congo":    ['#007FFF', '#CE1021', '#F7D618'],
  Australia:      ['#012169', '#FFFFFF', '#012169'],
  Curacao:        ['#002B7F', '#F9E814', '#002B7F'],
  Japan:          ['#FFFFFF', '#BC002D', '#FFFFFF'],
  Senegal:        ['#00853F', '#FCD116', '#CE1126'],
  Austria:        ['#ED2939', '#FFFFFF', '#ED2939'],
  Ecuador:        ['#FCD116', '#003893', '#CE1126'],
  Jordan:         ['#007A3D', '#FFFFFF', '#000000'],
  "South Africa": ['#007749', '#FFB81C', '#000000'],
  Belgium:        ['#000000', '#FFD100', '#EF3340'],
  Egypt:          ['#CE1126', '#FFFFFF', '#000000'],
  Morocco:        ['#C1272D', '#C1272D', '#006233'],
  Sweden:         ['#006AA7', '#FECC00', '#006AA7'],
  "Bosnia and Herzegovina": ['#002395', '#FECC00', '#002395'],
  Scotland:       ['#0065BD', '#FFFFFF', '#0065BD'],
  Mexico:         ['#006847', '#FFFFFF', '#CE1126'],
  Norway:         ['#BA0C2F', '#FFFFFF', '#00205B'],
  Switzerland:    ['#FF0000', '#FFFFFF', '#FF0000'],
  Brazil:         ['#009C3B', '#FFDF00', '#009C3B'],
  Spain:          ['#AA151B', '#F1BF00', '#AA151B'],
  France:         ['#002395', '#FFFFFF', '#ED2939'],
  Netherlands:    ['#AE1C28', '#FFFFFF', '#21468B'],
  Tunisia:        ['#E70013', '#FFFFFF', '#E70013'],
  "Cape Verde":  ['#003893', '#FFFFFF', '#CF2027'],
  "United States": ['#B22234', '#FFFFFF', '#3C3B6E'],
  "New Zealand": ['#012169', '#FFFFFF', '#C8102E'],
  Turkey:         ['#E30A17', '#FFFFFF', '#E30A17'],
  Canada:         ['#FF0000', '#FFFFFF', '#FF0000'],
  Ghana:          ['#006B3F', '#FCD116', '#CE1126'],
  Panama:         ['#005293', '#FFFFFF', '#D21034'],
  Uzbekistan:     ['#0099B5', '#FFFFFF', '#1EB53A'],
  Uruguay:        ['#FFFFFF', '#0038A8', '#FFFFFF'],
  Qatar:          ['#8D1B3D', '#FFFFFF', '#8D1B3D'],
}
const CAT_ICONS = {
  Escudo: 'shield', Jugador: 'person', Estadio: 'stadium',
  Leyenda: 'star', Especial: 'auto_awesome',
}

function cardGradient(seleccion) {
  const c = FLAG_COLORS[seleccion] || ['#666', '#999', '#666']
  return `linear-gradient(135deg, ${c[0]}, ${c[2]})`
}

export default function FiguritaCard({ figurita, compact = false, showTradeType = true, size = 'md', backActions = null }) {
  const [isFlipped, setIsFlipped] = useState(false)
  const [maestro, setMaestro] = useState(null)
  const isCollection = size === 'collection'
  const isSmall = size === 'sm'
  const sizeClass = isCollection ? 'w-[160px] h-[255px]' : isSmall ? 'w-[12.8rem] h-[19.2rem]' : 'w-64 h-96'
  const cardPadding = isCollection ? 'p-3' : isSmall ? 'p-3' : 'p-6'
  const frontNumberClass = isCollection ? 'text-3xl' : isSmall ? 'text-3xl' : 'text-7xl'
  const frontNameClass = isCollection ? 'text-sm' : isSmall ? 'text-base' : 'text-2xl'
  const frontSelectionClass = isCollection ? 'text-xs' : isSmall ? 'text-xs' : 'text-lg'

  useEffect(() => {
    if (isFlipped && !maestro) {
      getMaestroJugador(figurita.numero)
        .then(setMaestro)
        .catch(console.error);
    }
  }, [isFlipped, maestro, figurita.numero]);

  if (compact) {
    return (
      <FiguritaRow className="gap-3 px-3.5 py-2.5 rounded-xl bg-surface-container hover:bg-surface-variant">
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
      </FiguritaRow>
    )
  }

  const gradient = cardGradient(figurita.seleccion);

  return (
    <div className={sizeClass}>
      <TiltCard>
        <div
          className={`w-full h-full text-white flex flex-col justify-between ${cardPadding}`}
          style={{ background: gradient }}
          onClick={() => setIsFlipped(!isFlipped)}
        >
          {/* Front of the card */}
          <div className={`transition-opacity duration-300 ${isFlipped ? 'opacity-0' : 'opacity-100'}`}>
            <div className={`${frontNumberClass} font-bold`}>#{figurita.numero}</div>
            <div>
              <div className={`${frontNameClass} font-bold`}>{figurita.jugador}</div>
              <div className={frontSelectionClass}>{figurita.seleccion}</div>
            </div>
          </div>

          {/* Back of the card (details) */}
          <div className={`absolute inset-0 ${cardPadding} flex flex-col justify-between transition-opacity duration-300 ${isFlipped ? 'opacity-100' : 'opacity-0'}`}>
            <div>
              <div className="flex items-center gap-1.5">
                <Avatar name={figurita.owner || '?'} size={22} />
                <span className="text-xs">{figurita.owner}</span>
              </div>
              <div className="mt-3 text-xs leading-snug">
                {maestro ? (
                  <>
                    <p>País: {maestro.equipo}</p>
                    <p>Posición: {maestro.posicion}</p>
                    <p>Nro Camiseta: {maestro.numero_camiseta}</p>
                  </>
                ) : (
                  <p>Cargando...</p>
                )}
              </div>
            </div>
            <div className="space-y-2" onClick={(event) => event.stopPropagation()}>
              {backActions}
              {showTradeType && figurita.tipo === 'intercambio' && (
                <div className="bg-blue-500 text-white text-center py-1 rounded-lg">Intercambio</div>
              )}
              {showTradeType && figurita.tipo === 'subasta' && (
                <div className="bg-yellow-500 text-white text-center py-1 rounded-lg">Subasta</div>
              )}
            </div>
          </div>
        </div>
      </TiltCard>
    </div>
  );
}
