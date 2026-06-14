import clsx from 'clsx'
import Icon from './ui/Icon'
import FiguritaRow from './FiguritaRow'

export default function FiguritaMini({ figurita, selected, onToggle }) {
  return (
    <FiguritaRow
      onClick={onToggle}
      className={clsx(
        'gap-2.5 px-3 py-2 rounded-[10px] border-[1.5px]',
        selected
          ? 'bg-primary-container border-primary'
          : 'bg-surface-container border-transparent hover:border-outline-variant',
      )}
    >
      {selected && <Icon name="check_circle" size={18} className="text-primary shrink-0" />}
      <span className="text-xs-plus font-semibold text-on-surface">#{figurita.numero}</span>
      <span className="text-xs-plus text-on-surface-variant flex-1">{figurita.jugador}</span>
      <span className="text-xs text-on-surface-variant">{figurita.seleccion}</span>
    </FiguritaRow>
  )
}
