import Icon from './Icon'

export default function StarRating({ value = 0, onChange, size = 24 }) {
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map(i => (
        <button
          key={i}
          onClick={() => onChange?.(i)}
          className={`p-0.5 bg-transparent border-0 ${onChange ? 'cursor-pointer' : 'cursor-default'}`}
        >
          <Icon
            name={i <= value ? 'star' : 'star_border'}
            size={size}
            className={i <= value ? 'text-gold' : 'text-outline-variant'}
          />
        </button>
      ))}
    </div>
  )
}
