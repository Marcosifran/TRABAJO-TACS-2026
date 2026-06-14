import { apiFetch } from './client'

/**
 * Inicia sesión con email + contraseña.
 * Devuelve { access_token, token_type, usuario }.
 */
export function loginRequest(email, password) {
  return apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

/**
 * Registra un usuario nuevo y lo deja logueado (devuelve un JWT).
 * Devuelve { access_token, token_type, usuario }.
 */
export function registerRequest(nombre, email, password) {
  return apiFetch('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ nombre, email, password }),
  })
}
