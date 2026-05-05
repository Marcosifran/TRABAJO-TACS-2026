import { useEffect } from 'react'
import Icon from './Icon'

const TYPE_STYLES = {
  success: 'bg-tertiary-container text-on-tertiary-container',
  error:   'bg-secondary-container text-on-secondary-container',
  info:    'bg-surface-container-high text-on-surface',
}
const TYPE_ICONS = { success: 'check_circle', error: 'error', info: 'info' }

export default function Snackbar({ message, open, onClose, type = 'info' }) {
  useEffect(() => {
    if (open) {
      const t = setTimeout(onClose, 3000)
      return () => clearTimeout(t)
    }
  }, [open, onClose])

  if (!open) return null
  return (
    <div className={`fixed bottom-6 left-1/2 z-[100] flex items-center gap-2.5 px-6 py-3.5 rounded-xl text-sm font-medium shadow-elev-3 animate-snack ${TYPE_STYLES[type]}`}>
      <Icon name={TYPE_ICONS[type]} size={20} />
      {message}
    </div>
  )
}
