import { apiFetch } from './client'

/**
 * Lista todos los usuarios (id, nombre, email).
 * Se usa para resolver nombres a partir de ids en la UI
 * (proponentes de intercambios, ofertantes de subastas, etc.).
 */
export function listarUsuarios() {
  return apiFetch('/usuarios')
}
