import { apiFetch } from './client'

export function getMaestroJugador(numero) {
  return apiFetch(`/maestro/${numero}`)
}

/** Lista las selecciones/equipos disponibles en el maestro. */
export function getEquipos() {
  return apiFetch('/maestro/equipos').then((r) => r.equipos ?? [])
}

/** Jugadores de un equipo (ordenados por número de camiseta). */
export function getJugadoresPorEquipo(equipo) {
  return apiFetch(`/maestro/?equipo=${encodeURIComponent(equipo)}`)
}

/** Autocompletado por nombre de jugador, opcionalmente acotado a un equipo. */
export function buscarJugadores(jugador, equipo) {
  const params = new URLSearchParams({ jugador })
  if (equipo) params.set('equipo', equipo)
  return apiFetch(`/maestro/?${params.toString()}`)
}
