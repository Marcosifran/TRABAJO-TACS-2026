import { useState } from 'react'
import Icon from './Icon'

export default function Input({
  label, value, onChange, type = 'text',
  icon, placeholder, multiline = false, options,
}) {
  const [focused, setFocused] = useState(false)

  const baseClass = `
    w-full px-3.5 py-3 text-sm rounded-xl border-[1.5px] transition-colors duration-200
    bg-surface-container-low text-on-surface font-sans outline-none
    ${focused ? 'border-primary' : 'border-outline'}
    ${icon ? 'pl-10' : ''}
  `

  return (
    <div className="relative">
      {label && (
        <label className={`block text-xs font-medium mb-1 transition-colors duration-200 ${focused ? 'text-primary' : 'text-on-surface-variant'}`}>
          {label}
        </label>
      )}
      {icon && (
        <div className={`absolute left-3 ${label ? 'top-[30px]' : 'top-3'} pointer-events-none`}>
          <Icon name={icon} size={18} className="text-on-surface-variant" />
        </div>
      )}
      {options ? (
        <select
          value={value}
          onChange={e => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className={`${baseClass} cursor-pointer appearance-none`}
        >
          {options.map(o => (
            <option key={o.value ?? o} value={o.value ?? o}>{o.label ?? o}</option>
          ))}
        </select>
      ) : multiline ? (
        <textarea
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          rows={3}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className={`${baseClass} resize-y`}
        />
      ) : (
        <input
          type={type}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className={baseClass}
        />
      )}
    </div>
  )
}
