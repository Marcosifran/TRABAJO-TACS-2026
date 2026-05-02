import Icon from './Icon'

export default function Chip({ children, selected, onClick, icon }) {
  return (
    <button
      onClick={onClick}
      className={`
        inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-[13px] font-medium
        border transition-all duration-200 cursor-pointer
        ${selected
          ? 'border-primary bg-primary-container text-on-primary-container'
          : 'border-outline bg-transparent text-on-surface-variant hover:bg-surface-variant'
        }
      `}
    >
      {icon && (
        <Icon
          name={icon}
          size={16}
          className={selected ? 'text-on-primary-container' : 'text-on-surface-variant'}
        />
      )}
      {children}
    </button>
  )
}
