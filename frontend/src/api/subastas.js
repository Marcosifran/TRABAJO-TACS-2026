import { apiFetch } from './client'

/*
    Lista las subastas
*/
export function listarSubastas() {
  return apiFetch('/subastas')
}

/*
    se crea una subasta
*/

export function crearSubasta(data) {
  return apiFetch('/subastas', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/*
    ofertar en una subasta
*/

export function ofertarSubasta(subastaId, figuritasIds) {
  return apiFetch(`/subastas/${subastaId}/ofertas`, {
    method: 'POST',
    body: JSON.stringify({ figuritas_ofrecidas: figuritasIds }),
  })
}

export function listarMisSubastas() {
  return apiFetch('/usuarios/subastas')
}

export function listarOfertas(subastaId) {
  return apiFetch(`/subastas/${subastaId}/ofertas`)
}

export function listarMisOfertas() {
  return apiFetch('/usuarios/ofertas')
}

export function cancelarSubasta(subastaId) {
  return apiFetch(`/subastas/${subastaId}`, { method: 'DELETE' })
}

export function cancelarOferta(subastaId, ofertaId) {
  return apiFetch(`/subastas/${subastaId}/ofertas/${ofertaId}`, { method: 'DELETE' })
}

export function aceptarOferta(subastaId, ofertaId) {
  return apiFetch(`/subastas/${subastaId}/ofertas/${ofertaId}`, {
    method: 'PATCH',
    body: JSON.stringify({ estado: 'aceptada' }),
  })
}
