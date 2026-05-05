import { useState } from 'react'

export default function Card({ children, className = '', onClick, elevated = false, style }) {
  const [hovered, setHovered] = useState(false)
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={style}
      className={`
        rounded-2xl p-5 transition-all duration-200
        ${elevated
          ? `bg-surface-container-low border-0 ${hovered ? 'shadow-elev-2 dark:shadow-elev-2-dark' : 'shadow-elev-1 dark:shadow-elev-1-dark'}`
          : 'bg-surface-container border border-outline-variant'
        }
        ${onClick ? 'cursor-pointer' : ''}
        ${onClick && hovered ? '-translate-y-0.5' : ''}
        ${className}
      `}
    >
      {children}
    </div>
  )
}
