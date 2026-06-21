import { useState, useEffect, useRef, useCallback } from 'react'
import Icon from './Icon'

/**
 * Input de texto con un desplegable de sugerencias asíncronas.
 *
 * Props:
 * - value / onChange: texto controlado del input.
 * - fetchSuggestions(query) => Promise<item[]>: se llama (con debounce) al tipear.
 * - getOptionLabel(item) => string: texto principal de cada sugerencia.
 * - getOptionKey(item) => string|number: key de React por opción.
 * - renderOption(item) => node (opcional): render personalizado de la opción.
 * - onSelect(item): se invoca al elegir una sugerencia.
 * - loadAll() => Promise<item[]> (opcional): lista completa a mostrar al enfocar
 *   el campo vacío (ej: todos los jugadores de un país ya elegido).
 * - autoOpenKey (opcional): cuando cambia a un valor truthy, abre automáticamente
 *   el desplegable con `loadAll()` (ej: el país recién seleccionado).
 * - placeholder, icon, disabled, minChars (default 1), debounceMs (default 300).
 */
export default function Autocomplete({
  value,
  onChange,
  fetchSuggestions,
  getOptionLabel = (o) => String(o),
  getOptionKey = (o, i) => i,
  renderOption,
  onSelect,
  loadAll,
  autoOpenKey,
  placeholder,
  icon = 'search',
  disabled = false,
  minChars = 1,
  debounceMs = 300,
}) {
  const [focused, setFocused] = useState(false)
  const [open, setOpen] = useState(false)
  const [options, setOptions] = useState([])
  const [loading, setLoading] = useState(false)
  const debounceRef = useRef(null)
  const containerRef = useRef(null)
  const skipNextFetch = useRef(false)

  const run = useCallback(async (fn) => {
    setLoading(true)
    try {
      const data = await fn()
      setOptions(Array.isArray(data) ? data : [])
      setOpen(true)
    } catch {
      setOptions([])
    } finally {
      setLoading(false)
    }
  }, [])

  // Refs para que el efecto de búsqueda no se re-ejecute en cada render
  // (fetchSuggestions/loadAll suelen recrearse como arrow inline en el padre).
  const loadAllRef = useRef(loadAll)
  loadAllRef.current = loadAll
  const fetchRef = useRef(fetchSuggestions)
  fetchRef.current = fetchSuggestions

  const showAll = useCallback(() => {
    if (loadAllRef.current) run(() => loadAllRef.current())
  }, [run])

  useEffect(() => {
    if (skipNextFetch.current) {
      skipNextFetch.current = false
      return
    }
    if (debounceRef.current) clearTimeout(debounceRef.current)
    const q = value.trim()
    if (q.length < minChars) {
      // Campo vacío/corto: mostrar el plantel completo si hay loadAll, si no cerrar.
      if (q.length === 0 && loadAllRef.current) showAll()
      else {
        setOptions([])
        setOpen(false)
      }
      return
    }
    debounceRef.current = setTimeout(() => run(() => fetchRef.current(q)), debounceMs)
    return () => clearTimeout(debounceRef.current)
  }, [value, minChars, debounceMs, run, showAll])

  // Al elegir un país (autoOpenKey cambia), mostrar todo su plantel.
  const prevKey = useRef(autoOpenKey)
  useEffect(() => {
    if (autoOpenKey && autoOpenKey !== prevKey.current) showAll()
    prevKey.current = autoOpenKey
  }, [autoOpenKey, showAll])

  // Cerrar al hacer click fuera del componente.
  useEffect(() => {
    function onClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  function handleSelect(item) {
    skipNextFetch.current = true
    onSelect?.(item)
    setOpen(false)
    setOptions([])
  }

  const baseClass = `
    w-full px-3.5 py-3 text-sm rounded-xl border-[1.5px] transition-colors duration-200
    font-sans outline-none pl-10
    ${
      disabled
        ? 'bg-surface-variant text-on-surface-variant border-outline-variant cursor-not-allowed opacity-60'
        : `bg-surface-container-low text-on-surface ${focused ? 'border-primary' : 'border-outline'}`
    }
  `

  return (
    <div ref={containerRef} className="relative">
      <div className="absolute left-3 top-3 pointer-events-none">
        <Icon
          name={loading ? 'progress_activity' : icon}
          size={18}
          className={`text-on-surface-variant ${loading ? 'animate-spin' : ''}`}
        />
      </div>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        onFocus={() => {
          setFocused(true)
          if (options.length > 0) setOpen(true)
          else if (!value.trim()) showAll()
        }}
        onBlur={() => setFocused(false)}
        className={baseClass}
      />
      {open && options.length > 0 && (
        <ul className="absolute z-20 mt-1 w-full max-h-64 overflow-auto rounded-xl border-[1.5px] border-outline bg-surface-container shadow-lg">
          {options.map((item, i) => (
            <li key={getOptionKey(item, i)}>
              <button
                type="button"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => handleSelect(item)}
                className="w-full text-left px-3.5 py-2.5 text-sm text-on-surface hover:bg-surface-variant transition-colors"
              >
                {renderOption ? renderOption(item) : getOptionLabel(item)}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
