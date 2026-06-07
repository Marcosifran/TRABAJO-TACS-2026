import clsx from 'clsx'

export default function FiguritaRow({ children, onClick, className = '' }) {
  return (
    <div
      onClick={onClick}
      className={clsx('flex items-center cursor-pointer transition-colors', className)}
    >
      {children}
    </div>
  )
}
