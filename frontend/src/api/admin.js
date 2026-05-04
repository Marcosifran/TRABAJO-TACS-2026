import { apiFetch } from './client'

export function obtenerEstadisticas() {
  return apiFetch('/admin/estadisticas')
}
