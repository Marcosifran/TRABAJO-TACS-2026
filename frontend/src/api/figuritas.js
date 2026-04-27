const API_BASE = "http://localhost:8000/api/v1";
const TOKEN = import.meta.env.VITE_USER_TOKEN;

const headersAuth = {
  "Content-Type": "application/json",
  "X-User-Token": TOKEN,
};

/**
 * Obtiene todas las publicaciones disponibles para intercambio.
 * Excluye automáticamente las del usuario autenticado (lo hace el backend).
 * Corresponde a: GET /api/v1/publicaciones/
 */
export async function getPublicaciones(filtros = {}) {
  const params = new URLSearchParams();
  if (filtros.numero)           params.append("numero", filtros.numero);
  if (filtros.equipo)           params.append("equipo", filtros.equipo);
  if (filtros.jugador)          params.append("jugador", filtros.jugador);
  if (filtros.tipo_intercambio) params.append("tipo_intercambio", filtros.tipo_intercambio);

  const url = `${API_BASE}/publicaciones/${params.toString() ? "?" + params : ""}`;
  const respuesta = await fetch(url, { headers: headersAuth });

  if (!respuesta.ok) throw new Error("Error al cargar publicaciones");
  return await respuesta.json();
}

/**
 * Obtiene todas las figuritas del álbum personal del usuario autenticado.
 * Incluye el campo en_intercambio para saber cuáles están publicadas.
 * Corresponde a: GET /api/v1/album/
 */
export async function getMiAlbum() {
  const respuesta = await fetch(`${API_BASE}/album/`, { headers: headersAuth });

  if (!respuesta.ok) throw new Error("Error al cargar el álbum");
  return await respuesta.json();
}

/**
 * Agrega una figurita al álbum personal.
 * Corresponde a: POST /api/v1/album/
 */
export async function agregarAlAlbum(figurita) {
  const respuesta = await fetch(`${API_BASE}/album/`, {
    method: "POST",
    headers: headersAuth,
    body: JSON.stringify(figurita),
  });

  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(error.detail || "Error al agregar figurita al álbum");
  }
  return await respuesta.json();
}

/**
 * Publica una figurita del álbum para intercambio.
 * Corresponde a: POST /api/v1/publicaciones/
 */
export async function publicarFigurita(figurita_personal_id, tipo_intercambio, cantidad_disponible) {
  const respuesta = await fetch(`${API_BASE}/publicaciones/`, {
    method: "POST",
    headers: headersAuth,
    body: JSON.stringify({ figurita_personal_id, tipo_intercambio, cantidad_disponible }),
  });

  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(error.detail || "Error al publicar figurita");
  }
  return await respuesta.json();
}

/**
 * Elimina una figurita del álbum personal.
 * Corresponde a: DELETE /api/v1/album/{id}
 */
export async function eliminarDelAlbum(id) {
  const respuesta = await fetch(`${API_BASE}/album/${id}`, {
    method: "DELETE",
    headers: headersAuth,
  });

  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(error.detail || "Error al eliminar figurita del álbum");
  }
}

/**
 * Retira una publicación de la oferta pública.
 * Corresponde a: DELETE /api/v1/publicaciones/{id}
 */
export async function retirarPublicacion(id) {
  const respuesta = await fetch(`${API_BASE}/publicaciones/${id}`, {
    method: "DELETE",
    headers: headersAuth,
  });

  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(error.detail || "Error al retirar publicación");
  }
}

/**
 * Obtiene las publicaciones activas del usuario autenticado.
 * A diferencia de getPublicaciones(), incluye las propias.
 * Corresponde a: GET /api/v1/publicaciones/mias
 */
export async function getMisPublicaciones() {
  const respuesta = await fetch(`${API_BASE}/publicaciones/mias`, {
    headers: headersAuth,
  });

  if (!respuesta.ok) throw new Error("Error al cargar mis publicaciones");
  return await respuesta.json();
}

/**
 * Registra una figurita como faltante.
 * Corresponde a: POST /api/v1/usuarios/faltantes
 */
export async function registrarFaltante(numero_figurita) {
  const respuesta = await fetch(`${API_BASE}/usuarios/faltantes`, {
    method: "POST",
    headers: headersAuth,
    body: JSON.stringify({ numero_figurita }),
  });

  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(error.detail || "Error al registrar faltante");
  }
  return await respuesta.json();
}

/**
 * Obtiene los faltantes del usuario autenticado.
 * Corresponde a: GET /api/v1/usuarios/faltantes
 */
export async function getMisFaltantes() {
  const respuesta = await fetch(`${API_BASE}/usuarios/faltantes`, {
    headers: headersAuth,
  });

  if (!respuesta.ok) throw new Error("Error al cargar faltantes");
  return await respuesta.json();
}