import { apiFetch } from './client'

/** Agrega una figurita al álbum personal. */
export function agregarAlAlbum({ numero, equipo, jugador, cantidad }) {
  return apiFetch('/album/', {
    method: 'POST',
    body: JSON.stringify({ numero: parseInt(numero), equipo, jugador, cantidad: parseInt(cantidad) }),
  })
}

/** Pone una figurita del álbum en oferta pública. */
export function publicarFigurita({ figurita_personal_id, tipo_intercambio, cantidad_disponible }) {
  return apiFetch('/publicaciones/', {
    method: 'POST',
    body: JSON.stringify({ figurita_personal_id, tipo_intercambio, cantidad_disponible: parseInt(cantidad_disponible) }),
  })
}

/** Retorna las publicaciones activas del usuario autenticado. */
export function listarMisPublicaciones() {
  return apiFetch('/publicaciones/mias')
}

/** Retira una publicación propia. */
export function retirarPublicacion(id) {
  return apiFetch(`/publicaciones/${id}`, { method: 'DELETE' })
}
