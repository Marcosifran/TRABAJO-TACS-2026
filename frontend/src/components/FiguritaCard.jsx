import { useState, useEffect } from 'react'
import TiltCard from './TiltCard'
import Icon from './ui/Icon'
import Avatar from './ui/Avatar'
import Button from './ui/Button'
import FiguritaRow from './FiguritaRow'
import { getMaestroJugador } from '../api/maestro'
import { cardGradient } from '../utils/flagColors'

const CAT_ICONS = {
  Escudo: 'shield', Jugador: 'person', Estadio: 'stadium',
  Leyenda: 'star', Especial: 'auto_awesome',
}


export default function FiguritaCard({ figurita, compact = false, showTradeType = true, size = 'md', backActions = null, onAction = null }) {
  const [isFlipped, setIsFlipped] = useState(false)
  const [maestro, setMaestro] = useState(null)
  const isCollection = size === 'collection'
  const isSmall = size === 'sm'
  const sizeClass = isCollection ? 'w-[136px] h-[218px]' : isSmall ? 'w-[11rem] h-[17rem]' : 'w-52 h-80'
  const cardPadding = isCollection ? 'p-3' : isSmall ? 'p-3' : 'p-5'
  const frontNumberClass = isCollection ? 'text-2xl' : isSmall ? 'text-2xl' : 'text-5xl'
  const frontNameClass = isCollection ? 'text-xs' : isSmall ? 'text-sm' : 'text-xl'
  const frontSelectionClass = isCollection ? 'text-[10px]' : isSmall ? 'text-xs' : 'text-base'

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
          className="relative w-full h-full text-white"
          style={{ background: gradient }}
          onClick={() => setIsFlipped(!isFlipped)}
        >
          {/* Front of the card */}
          <div className={`absolute inset-0 ${cardPadding} flex flex-col justify-between transition-opacity duration-300 ${isFlipped ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}
               style={{ textShadow: '0 1px 4px rgba(0,0,0,0.55)' }}>
            <div className={`${frontNumberClass} font-bold`}>#{figurita.numero}</div>
            <div>
              <div className={`${frontNameClass} font-bold`}>{figurita.jugador}</div>
              <div className={frontSelectionClass}>{figurita.seleccion}</div>
            </div>
          </div>

          {/* Back of the card (details) */}
          <div className={`absolute inset-0 ${cardPadding} flex flex-col justify-between transition-opacity duration-300 ${isFlipped ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
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
                  </>
                ) : (
                  <p>Cargando...</p>
                )}
              </div>
            </div>
            <div className="space-y-2" onClick={(event) => event.stopPropagation()}>
              {backActions}
              {showTradeType && figurita.tipo === 'intercambio' && (
                <div
                  className={`text-white text-center text-[10px] font-medium py-1 rounded-lg transition-opacity ${onAction ? 'cursor-pointer hover:opacity-80' : ''}`}
                  style={{ backgroundColor: 'var(--color-trade)' }}
                  onClick={onAction ?? undefined}
                >Intercambio</div>
              )}
              {showTradeType && figurita.tipo === 'subasta' && (
                <div
                  className={`text-white text-center text-[10px] font-medium py-1 rounded-lg transition-opacity ${onAction ? 'cursor-pointer hover:opacity-80' : ''}`}
                  style={{ backgroundColor: 'var(--color-auction)' }}
                  onClick={onAction ?? undefined}
                >Subasta</div>
              )}
            </div>
          </div>
        </div>
      </TiltCard>
    </div>
  );
}
