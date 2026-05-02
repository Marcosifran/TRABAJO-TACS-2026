export default function Icon({ name, size = 20, className = '', style }) {
  return (
    <span
      className={`material-symbols-rounded select-none leading-none ${className}`}
      style={{ fontSize: size, ...style }}
    >
      {name}
    </span>
  )
}
