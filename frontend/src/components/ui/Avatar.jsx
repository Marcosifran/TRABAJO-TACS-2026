export default function Avatar({ name = '?', size = 40 }) {
  const initials = name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
  return (
    <div
      className="rounded-full bg-primary-container text-on-primary-container flex items-center justify-center font-semibold shrink-0 overflow-hidden"
      style={{ width: size, height: size, fontSize: size * 0.38 }}
    >
      {initials}
    </div>
  )
}
