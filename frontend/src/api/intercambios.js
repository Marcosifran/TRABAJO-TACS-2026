import { apiFetch } from './client'

/** Propone un intercambio a otro usuario. */
export function proponerIntercambio({ figuritas_ofrecidas_numero, figurita_solicitada_numero, solicitado_a_id }) {
  return apiFetch('/intercambios/', {
    method: 'POST',
    body: JSON.stringify({
      figuritas_ofrecidas_numero,
      figurita_solicitada_numero,
      solicitado_a_id
    }),
  })
}

/** Retorna la lista de intercambios del usuario (enviados y recibidos). */
export function listarIntercambios() {
  return apiFetch('/intercambios/')
}

/** Responde a un intercambio (aceptar/rechazar). */
export function responderIntercambio(id, decision) {
  return apiFetch(`/intercambios/${id}/estado`, {
    method: 'PATCH',
    body: JSON.stringify({ estado: decision }),
  })
}

/** Califica a un usuario tras un intercambio. */
export function calificarIntercambio(id, { puntuacion, comentario }) {
  return apiFetch(`/intercambios/${id}/calificaciones`, {
    method: 'POST',
    body: JSON.stringify({ puntuacion, comentario }),
  })
}
