import { USERS, STORAGE_KEY_INDEX } from '../context/UserContext'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
const DEFAULT_TIMEOUT_MS = 15_000

function token() {
  const saved = sessionStorage.getItem(STORAGE_KEY_INDEX)
  const i = saved !== null ? parseInt(saved, 10) : 0
  return USERS[i]?.token || ''
}

/**
 * ApiError extends the native Error type to include HTTP status and the response body.
 * Consumers can check `err.status` to handle specific HTTP codes (eg. 422).
 */
export class ApiError extends Error {
  constructor(status, message, body) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

/**
 * Normalize a FastAPI `detail` value into a readable string.
 * - If `detail` is a string, return it.
 * - If it's an array (validation errors), format each entry into `field: msg`.
 * - Otherwise JSON-stringify the value.
 * Returns `null` for falsy values.
 */
function describeDetail(detail) {
  if (!detail) return null
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((e) => `${(e.loc || []).slice(1).join('.')}: ${e.msg}`).join('; ')
  }
  try {
    return JSON.stringify(detail)
  } catch {
    return String(detail)
  }
}

/**
 * Perform an HTTP request to the API with sensible defaults:
 * - JSON content-type header and token injection
 * - timeout (default via `DEFAULT_TIMEOUT_MS`)
 * - composed abort `signal` support
 * - content-type sniffing to avoid JSON parse errors
 * - structured `ApiError` on non-2xx responses
 *
 * @param {string} path - Path relative to the API base (eg. '/publicaciones')
 * @param {object} [opts] - Options. Supports `signal` and `timeoutMs` plus any `fetch` options.
 * @returns {Promise<any|null>} Parsed response body, or `null` for 204 responses.
 * @throws {ApiError} When the response is not ok.
 */
export async function apiFetch(path, { signal, timeoutMs = DEFAULT_TIMEOUT_MS, ...options } = {}) {
  const controller = new AbortController()
  const tid = timeoutMs ? setTimeout(() => controller.abort(new Error('Timeout')), timeoutMs) : null
  if (signal) signal.addEventListener('abort', () => controller.abort(signal.reason))

  let res
  try {
    res = await fetch(`${BASE}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        'X-User-Token': token(),
        ...options.headers,
      },
    })
  } finally {
    if (tid) clearTimeout(tid)
  }

  if (res.status === 204) return null

  const contentType = (res.headers.get('content-type') || '').toLowerCase()
  const isJson = contentType.includes('application/json')
  const body = isJson ? await res.json().catch(() => ({})) : await res.text().catch(() => '')

  if (!res.ok) {
    const message =
      describeDetail(body?.detail) ||
      (typeof body === 'string' ? body : null) ||
      `Error ${res.status}`
    throw new ApiError(res.status, message, body)
  }

  return body
}
