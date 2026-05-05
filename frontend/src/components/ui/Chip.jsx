import Icon from './Icon'

export default function Chip({ children, selected, onClick, icon, disabled }) {
  return (
    <button
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      title={disabled ? 'Próximamente' : undefined}
      className={`
        inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-[13px] font-medium
        border transition-all duration-200
        ${disabled
          ? 'border-outline/40 bg-transparent text-on-surface/30 cursor-not-allowed'
          : selected
            ? 'border-primary bg-primary-container text-on-primary-container cursor-pointer'
            : 'border-outline bg-transparent text-on-surface-variant hover:bg-surface-variant cursor-pointer'
        }
      `}
    >
      {icon && (
        <Icon
          name={icon}
          size={16}
          className={disabled ? 'text-on-surface/30' : selected ? 'text-on-primary-container' : 'text-on-surface-variant'}
        />
      )}
      {children}
    </button>
  )
}
