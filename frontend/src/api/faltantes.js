import { apiFetch } from './client'

export function registrarFaltante({ numero_figurita, equipo, jugador }) {
  return apiFetch('/usuarios/faltantes', {
    method: 'POST',
    body: JSON.stringify({ numero_figurita: parseInt(numero_figurita), equipo: equipo || null, jugador: jugador || null }),
  })
}

export function listarFaltantes() {
  return apiFetch('/usuarios/faltantes')
}
