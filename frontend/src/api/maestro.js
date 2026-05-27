import { apiFetch } from './client'

export function getMaestroJugador(numero) {
  return apiFetch(`/maestro/${numero}`)
}
