const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

function token() {
  return localStorage.getItem('figuswap-token') || ''
}

export async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-User-Token': token(),
      ...options.headers,
    },
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Error ${res.status}`)
  }

  return res.status === 204 ? null : res.json()
}
