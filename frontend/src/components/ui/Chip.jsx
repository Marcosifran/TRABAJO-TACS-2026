import clsx from 'clsx'
import Icon from './Icon'

const STATES = {
  disabled: 'border-outline/40 bg-transparent text-on-surface/30 cursor-not-allowed',
  selected: 'border-primary bg-primary-container text-on-primary-container cursor-pointer',
  default:  'border-outline bg-transparent text-on-surface-variant hover:bg-surface-variant cursor-pointer',
}
const ICON_COLOR = {
  disabled: 'text-on-surface/30',
  selected: 'text-on-primary-container',
  default:  'text-on-surface-variant',
}

export default function Chip({ children, selected, onClick, icon, disabled }) {
  const state = disabled ? 'disabled' : selected ? 'selected' : 'default'
  return (
    <button
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      title={disabled ? 'Próximamente' : undefined}
      className={clsx(
        'inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs-plus font-medium border transition-all duration-200',
        STATES[state],
      )}
    >
      {icon && <Icon name={icon} size={16} className={ICON_COLOR[state]} />}
      {children}
    </button>
  )
}
