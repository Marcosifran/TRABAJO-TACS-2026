import Icon from './Icon'

export default function Tabs({ tabs, active, onChange }) {
  return (
    <div className="flex border-b border-outline-variant">
      {tabs.map(t => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={`
            flex items-center gap-1.5 px-6 py-3 text-sm font-medium transition-all duration-200
            border-b-[3px] -mb-px cursor-pointer bg-transparent border-t-0 border-l-0 border-r-0 font-sans
            ${active === t.id
              ? 'text-primary border-primary font-semibold'
              : 'text-on-surface-variant border-transparent hover:text-on-surface'
            }
          `}
        >
          {t.icon && <Icon name={t.icon} size={16} className={active === t.id ? 'text-primary' : 'text-on-surface-variant'} />}
          {t.label}
        </button>
      ))}
    </div>
  )
}
