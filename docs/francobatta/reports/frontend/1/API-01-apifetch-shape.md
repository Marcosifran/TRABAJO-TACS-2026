# API-01 — `apiFetch` is too thin: no abort, no timeout, no 422 array handling

**Severity:** H  ·  **Area:** API  ·  **Effort:** S-M

## Diagnosis

`api/client.js` is the entire frontend data layer's contract with the server — every page, every component, every domain module talks to the backend through `apiFetch`. At 23 lines it is impressively small, and that's the problem: the things it doesn't do, every caller has to do (or, more commonly, doesn't do). Three gaps stand out, plus one structural detail worth fixing today because [STATE-01](./STATE-01-no-server-state-library.md) will reuse this same fetcher as SWR's `fetcher`.

**1. Errors are stringified blindly.** `client.js:17-19` assumes the response body has a string `detail`:

```js
if (!res.ok) {
  const body = await res.json().catch(() => ({}))
  throw new Error(body.detail || `Error ${res.status}`)
}
```

FastAPI's default 422 response — fired by every Pydantic validation failure — returns an **array** at `detail`, not a string:

```json
{ "detail": [{ "loc": ["body","cantidad"], "msg": "field required", "type": "..." }] }
```

The current code does `body.detail || ...` which is truthy on a non-empty array, then passes it to `new Error(...)`, which calls `.toString()` and yields the unhelpful `[object Object]`-via-comma-join. The team has already worked around this by writing validation in services rather than schemas (see backend [PY-01](../backend/PY-01-magic-strings-and-validation.md)), but the moment they push a `min_length` check into a Pydantic `Field`, the frontend shows `[object Object]` to the user. Fix this once, here.

**2. Nothing can be cancelled.** No `AbortController` is plumbed through. When a user types in `SearchPage` and the debounced fetch fires, then types again, the older Promise still completes and overwrites the newer state if it arrives second. Same issue when the user switches between tabs in `AuctionsPage`, when they navigate away from `NotificationsPage` while three parallel fetches are in flight (`NotificationsPage.jsx:37-41`), or when `UserContext.switchUser` swaps tokens mid-request. The fix is structural — pass a `signal` parameter — and is the same change SWR needs from a `fetcher`. This connects directly to [ASYNC-01](./ASYNC-01-fire-and-forget-and-races.md).

**3. No timeout, no content-type sniffing.** A hung TCP connection holds the request indefinitely. The 204 branch (`client.js:22`) is correctly handled, but any 2xx response with a non-JSON content type (e.g. `text/plain`, an HTML 502 page from a reverse proxy) will throw on `res.json()` with no helpful diagnostic. For a small project these are edge cases; the cost of adding the guards is the same.

**4. Token reading is a tight coupling with `UserContext`.** `client.js:3-5` reads `sessionStorage.getItem('figuswap-token')` synchronously on every call. `UserContext.jsx:23, 31` writes it. Two modules touching the same key by string — and both call sites do a `sessionStorage` round-trip per render and per fetch respectively. The smaller fix is acceptable for the current "two demo users" model, but flagging here because (a) the fetcher is the natural place for that wiring to be made explicit, and (b) [STORAGE-01](./STORAGE-01-session-and-local-storage.md) covers the deeper question about the storage choice itself.

## Evidence

- `frontend/src/api/client.js:1-23` — full file: BASE URL, token reader, headers, error branch, 204 path
- `frontend/src/api/client.js:17-19` — error normalization treats `body.detail` as a string; breaks on FastAPI 422 array
- `frontend/src/api/client.js:3-5` — `token()` reads `sessionStorage` per call
- `frontend/src/api/client.js:8-22` — no `signal`, no `AbortSignal.timeout`, no content-type check
- `frontend/src/api/admin.js`, `album.js`, `faltantes.js`, `intercambios.js`, `publicaciones.js`, `subastas.js` — all six domain modules delegate to `apiFetch` (consistent surface, no bypasses — that's the good news)
- `frontend/src/api/publicaciones.js:30-38` — the only call site that builds query strings; everyone else just hits the endpoint

## Recommendation

Grow `apiFetch` into the fetcher SWR will consume — same return shape, structured error, optional `signal`, default timeout. Keep the surface small; this is not the place to add retries (SWR handles that), only the things that *every* caller would otherwise have to handle.

```js
// frontend/src/api/client.js
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
const DEFAULT_TIMEOUT_MS = 15_000

function token() {
  return sessionStorage.getItem('figuswap-token') || ''
}

export class ApiError extends Error {
  constructor(status, message, body) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

function describeDetail(detail) {
  if (!detail) return null
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    // FastAPI 422 shape
    return detail
      .map(e => `${(e.loc || []).slice(1).join('.')}: ${e.msg}`)
      .join('; ')
  }
  return JSON.stringify(detail)
}

export async function apiFetch(path, { signal, timeoutMs = DEFAULT_TIMEOUT_MS, ...options } = {}) {
  const controller = new AbortController()
  const tid = setTimeout(() => controller.abort(new Error('Timeout')), timeoutMs)
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
    clearTimeout(tid)
  }

  if (res.status === 204) return null

  const isJson = (res.headers.get('content-type') || '').includes('application/json')
  const body = isJson ? await res.json().catch(() => ({})) : await res.text().catch(() => '')

  if (!res.ok) {
    const message = describeDetail(body?.detail) || (typeof body === 'string' ? body : null) || `Error ${res.status}`
    throw new ApiError(res.status, message, body)
  }
  return body
}
```

This change is **backwards-compatible**: every existing caller still does `await apiFetch('/foo')` and gets the parsed JSON. The new capabilities are opt-in: callers that want to cancel pass `{ signal: controller.signal }`; callers that want to catch a specific status check `err.status` on the thrown `ApiError`. SWR's signature is `fetcher(key, { signal })` — it now lines up exactly.

Files that change: only `frontend/src/api/client.js`. The six domain modules need no edits because the public signature is unchanged. The pages that want cancellation opt-in one at a time (see [ASYNC-01](./ASYNC-01-fire-and-forget-and-races.md)).

## Why this approach

- **`ApiError` is the contract that lets every layer above this be cleaner.** Snackbar code (`HomePage.jsx:121`, `AuctionsPage.jsx:120`) currently shows `error.message` raw. With a typed error the same snackbar can choose to display `err.status === 422 ? 'Datos inválidos' : err.message`. Pages don't need to do that today; they *can* tomorrow.
- **`AbortSignal.timeout()` exists in modern Node and the browser, but the manual `setTimeout + controller.abort` form composes with caller-provided signals.** That's needed because SWR passes its own signal in via the second argument; we need to abort if *either* fires. The composed pattern is the canonical one in the React Query / SWR docs.
- **No retry, no cache here.** Resist building those into the fetcher. SWR (or a tiny custom cache hook) owns retry semantics, dedup, and revalidation. The fetcher's job is "one request, with timeout, with abort, with structured errors." Conflating the two layers is how `apiFetch` ends up reinventing SWR badly.
