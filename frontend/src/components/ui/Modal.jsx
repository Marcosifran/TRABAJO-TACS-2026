import Icon from './Icon'

export default function Modal({ open, onClose, title, children, width = 520 }) {
  if (!open) return null
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
      <div
        onClick={e => e.stopPropagation()}
        className="relative bg-surface-container-high rounded-3xl p-7 shadow-elev-3 dark:shadow-elev-3-dark animate-modal overflow-y-auto max-h-[85vh] scrollbar-none"
        style={{ width, maxWidth: '90vw' }}
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-xl font-semibold text-on-surface m-0">{title}</h2>
          <button
            onClick={onClose}
            className="p-1 rounded-full hover:bg-surface-variant transition-colors cursor-pointer bg-transparent border-0"
          >
            <Icon name="close" size={22} className="text-on-surface-variant" />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}
