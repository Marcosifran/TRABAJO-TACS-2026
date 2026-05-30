/**
 * Tiempo hasta el cierre de una subasta (referencia: ahora).
 * @param {string|Date} finIso
 * @returns {string} "2h 15m", "5m", o "Finalizada"
 */
export function formatTiempoRestante(finIso) {
  if (!finIso) return ''
  const ms = new Date(finIso).getTime() - Date.now()
  if (ms <= 0) return 'Finalizada'
  const horas = Math.floor(ms / 3600000)
  const mins = Math.floor((ms % 3600000) / 60000)
  return horas > 0 ? `${horas}h ${mins}m` : `${mins}m`
}

/**
 * Devuelve true si la subasta está activa y su fecha de fin aún no llegó.
 * @param {object} sub - Objeto subasta con campos `estado` y `fin`
 * @param {number} [now] - Timestamp de referencia (default: Date.now())
 */
export function isAuctionActive(sub, now = Date.now()) {
  if (!sub || sub.estado !== 'activa') return false
  const fin = sub.fin ? new Date(sub.fin).getTime() : 0
  return fin > now
}

/**
 * Texto para mostrar en tarjetas: "Cierra en …" o "Finalizada".
 */
export function lineaCierraEn(finIso) {
  const t = formatTiempoRestante(finIso)
  if (t === '') return ''
  if (t === 'Finalizada') return 'Finalizada'
  return `Cierra en ${t}`
}
