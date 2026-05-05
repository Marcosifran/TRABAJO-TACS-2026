import Icon from './Icon'
import Button from './Button'

export default function EmptyState({ icon, title, subtitle, action, onAction }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-18 h-18 rounded-full bg-primary-container flex items-center justify-center mb-4" style={{ width: 72, height: 72 }}>
        <Icon name={icon} size={36} className="text-primary" />
      </div>
      <h3 className="text-lg font-semibold text-on-surface mb-2">{title}</h3>
      {subtitle && <p className="text-sm text-on-surface-variant max-w-sm mb-5">{subtitle}</p>}
      {action && <Button onClick={onAction}>{action}</Button>}
    </div>
  )
}
