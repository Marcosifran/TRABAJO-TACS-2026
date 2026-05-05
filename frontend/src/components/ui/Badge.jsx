export default function Badge({ count, children }) {
  return (
    <div className="relative inline-flex">
      {children}
      {count > 0 && (
        <div className="absolute -top-1 -right-1 min-w-[18px] h-[18px] rounded-full bg-secondary text-on-secondary text-[11px] font-semibold flex items-center justify-center px-1">
          {count > 99 ? '99+' : count}
        </div>
      )}
    </div>
  )
}
