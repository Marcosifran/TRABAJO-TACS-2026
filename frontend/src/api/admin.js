import { apiFetch } from './client'

export function obtenerEstadisticas() {
  return apiFetch('/admin/estadisticas')
}

export function listarCalificaciones() {
  return apiFetch('/admin/calificaciones')
}
