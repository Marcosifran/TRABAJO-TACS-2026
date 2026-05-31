export default function FiguritaRow({ children, onClick, className = '' }) {
  return (
    <div
      onClick={onClick}
      className={`flex items-center cursor-pointer transition-colors ${className}`}
    >
      {children}
    </div>
  )
}
