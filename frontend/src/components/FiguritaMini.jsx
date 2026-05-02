import Icon from './ui/Icon'

export default function FiguritaMini({ figurita, selected, onToggle }) {
  return (
    <div
      onClick={onToggle}
      className={`
        flex items-center gap-2.5 px-3 py-2 rounded-[10px] cursor-pointer transition-all duration-200
        border-[1.5px]
        ${selected
          ? 'bg-primary-container border-primary'
          : 'bg-surface-container border-transparent hover:border-outline-variant'
        }
      `}
    >
      {selected && <Icon name="check_circle" size={18} className="text-primary shrink-0" />}
      <span className="text-[13px] font-semibold text-on-surface">#{figurita.numero}</span>
      <span className="text-[13px] text-on-surface-variant flex-1">{figurita.jugador}</span>
      <span className="text-xs text-on-surface-variant">{figurita.seleccion}</span>
    </div>
  )
}
