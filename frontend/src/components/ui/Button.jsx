import Icon from './Icon'

const VARIANTS = {
  filled:   'bg-primary text-on-primary hover:shadow-elev-1 dark:hover:shadow-elev-1-dark',
  tonal:    'bg-secondary-container text-on-secondary-container hover:shadow-elev-1 dark:hover:shadow-elev-1-dark',
  outlined: 'bg-transparent text-primary border border-outline',
  text:     'bg-transparent text-primary hover:bg-surface-variant',
  error:    'bg-error text-white hover:shadow-elev-1',
}
const SIZES = {
  sm: 'px-3 py-1.5 text-[13px] gap-1.5',
  md: 'px-5 py-2.5 text-sm gap-1.5',
  lg: 'px-7 py-3.5 text-base gap-2',
}

export default function Button({
  children, variant = 'filled', icon, onClick,
  disabled = false, size = 'md', type = 'button', className = '',
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`
        inline-flex items-center justify-center font-medium rounded-full
        transition-all duration-200 cursor-pointer select-none
        disabled:opacity-50 disabled:cursor-not-allowed
        ${VARIANTS[variant]} ${SIZES[size]} ${className}
      `}
    >
      {icon && <Icon name={icon} size={parseInt(SIZES[size].match(/text-\[(\d+)/)?.[1] || 14) + 2} />}
      {children}
    </button>
  )
}
