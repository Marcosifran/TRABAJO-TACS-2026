import clsx from 'clsx'

export default function Card({ children, className = '', onClick, elevated = false, style }) {
  return (
    <div
      onClick={onClick}
      style={style}
      className={clsx(
        'rounded-2xl p-5 transition-all duration-200',
        elevated
          ? 'bg-surface-container-low border-0 shadow-elev-1 dark:shadow-elev-1-dark hover:shadow-elev-2 dark:hover:shadow-elev-2-dark'
          : 'bg-surface-container border border-outline-variant',
        onClick && 'cursor-pointer hover:-translate-y-0.5',
        className,
      )}
    >
      {children}
    </div>
  )
}
