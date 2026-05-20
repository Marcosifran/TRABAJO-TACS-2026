# STATE-01 — No server-state library; every page reinvents loading/error/cache

**Severity:** H  ·  **Area:** State management  ·  **Effort:** M

## Diagnosis

There is no library managing server state. `package.json` lists React, React DOM, and React Router — nothing else. Every page therefore does the same three things by hand: call `apiFetch` in a `useEffect`, hold the result in `useState`, hold a `loading` flag in another `useState`, hold an `error` flag in a third, and remember to refetch after every mutation that might affect the data. The shape repeats ten or twelve times across the codebase and the failure modes — silent errors ([ASYNC-01](./ASYNC-01-fire-and-forget-and-races.md)), redundant requests, stale data after writes, race conditions — repeat with it.

The clearest evidence is `HomePage.jsx:22-91`. The page declares 13 `useState`s, most of them server data; an effect that fires six independent `apiFetch` calls in parallel (`:41-62`), with no shared loading state; and another effect that fires four more (`:64-91`) for the auction widget. Six of those ten calls overlap with calls the user has already made on other pages — for instance, `listarMiAlbum()` runs in `HomePage:42` *and* `HomePage:72` *and again* in `CollectionPage:56` if the user navigates there. Without a cache, the same request fires every time. In dev that's invisible; under load, that's hundreds of duplicate hits.

The second symptom is that writes don't propagate. When a user accepts a trade in `TradesPage`, the local `intercambios` list updates because the page manually refetches — but `HomePage`'s `intercambiosCount` is stale until the user reloads. The team's workarounds for this currently look like `cargarDatos()` called manually after each `await` (`AuctionsPage.jsx:118, 208`), which works one page at a time and breaks cross-page coherency.

The third symptom is the absence of pessimistic-vs-optimistic UX. Today, after `await ofertarSubasta(...)` returns, the modal closes and a snackbar fires — the user only knows it worked when the round-trip completes. Optimistic updates require a cache to mutate-then-revalidate, which doesn't exist.

The user has explicitly **ruled out React Query and Redux** during plan refinement — the concept surface (queryClient, queryKeys, hydration, mutations, invalidation) is too much for an intern team mid-entrega. **SWR** is the right size: one hook (`useSWR(key, fetcher)`), one cache, one mutation API (`mutate(key)`). The whole library is ~4kB gzipped and the learning curve is "the key is a string; the fetcher is your existing `apiFetch`." That fits the team and the project. The alternative — a custom `useFetch` hook with a Map-based cache — is also fine and slightly more pedagogical; it's mentioned at the end of "Why this approach."

This report depends on [API-01](./API-01-apifetch-shape.md) (the fetcher SWR will use) and largely dissolves [ASYNC-01](./ASYNC-01-fire-and-forget-and-races.md) (SWR cancels stale requests and provides `data`/`error`/`isLoading` natively). The three reports are best read together.

## Evidence

- `frontend/package.json:12-16` — only `react`, `react-dom`, `react-router-dom` as runtime deps; no state-management library
- `frontend/src/pages/HomePage.jsx:22-39` — 9 `useState`s for data + UI state
- `frontend/src/pages/HomePage.jsx:41-62` — six independent `apiFetch` calls in one effect; no shared loading
- `frontend/src/pages/HomePage.jsx:42`, `HomePage.jsx:72`, `CollectionPage.jsx:56`, `SearchPage.jsx:81` — `listarMiAlbum()` called from four call sites with no shared cache
- `frontend/src/pages/AuctionsPage.jsx:118, 208` — manual `cargarDatos()` after writes (per-page refetch)
- `frontend/src/pages/NotificationsPage.jsx:33-53` — manual `Promise.all` over three reads with hand-rolled loading
- `frontend/src/components/AppShell.jsx:52-133` — three near-identical poll effects, each maintaining its own "seen ids" memory

## Recommendation

Adopt **SWR**. Use the existing `apiFetch` (improved per [API-01](./API-01-apifetch-shape.md)) as the global fetcher. Page bodies collapse to a `useSWR` call per resource. Mutations call `mutate('/foo')` to invalidate the relevant cache key.

```jsx
// frontend/src/main.jsx — add SWRConfig at the root
import { SWRConfig } from 'swr'
import { apiFetch } from './api/client'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <SWRConfig value={{
      fetcher: (key) => apiFetch(key),
      revalidateOnFocus: false,        // start conservative; turn on per-hook if useful
      shouldRetryOnError: false,       // we don't have idempotent retries everywhere
    }}>
      <App />
    </SWRConfig>
  </StrictMode>,
)
```

```jsx
// frontend/src/pages/AdminPage.jsx — before
const [stats, setStats] = useState(null)
const [loading, setLoading] = useState(true)
useEffect(() => {
  obtenerEstadisticas().then(setStats).catch(() => {}).finally(() => setLoading(false))
}, [])

// after
import useSWR from 'swr'
const { data: stats, isLoading, error } = useSWR('/admin/estadisticas')
// then in JSX:  loading ? '…' : (stats?.[c.key] ?? 0)   →   isLoading ? '…' : (stats?.[c.key] ?? 0)
```

For writes, after `await aceptarOferta(...)` returns, invalidate the affected keys:

```jsx
import { mutate } from 'swr'

await aceptarOferta(subasta_id, oferta_id)
mutate('/subastas/')
mutate('/usuarios/ofertas')           // "my offers" — affected, this user lost one
mutate(`/subastas/${subasta_id}/ofertas`)  // the modal's data — stale now
```

The cache key becomes the URL path. That's also the SWR convention and means **`HomePage`'s `intercambiosCount` updates automatically** when `TradesPage` calls `mutate('/intercambios/')` — no cross-page wiring needed, no event bus, no Redux store.

For the three `AppShell` polls, SWR's `refreshInterval` option replaces the hand-rolled `setInterval`:

```jsx
useSWR('/intercambios/', { refreshInterval: 20_000 })
```

Files that change: `frontend/package.json` (`npm install swr`); `frontend/src/main.jsx` (wrap in `SWRConfig`); every page that reads (`HomePage`, `CollectionPage`, `SearchPage`, `TradesPage`, `AuctionsPage`, `NotificationsPage`, `ProfilePage`, `AdminPage`); every page that writes adds a `mutate(...)` after the `await`; `AppShell.jsx` three pollers become three `useSWR` calls. The six API modules in `src/api/*.js` are unchanged because they wrap `apiFetch`, which SWR now wraps in turn.

**Migration order.** Do not migrate all pages at once. SWR coexists with raw `useEffect`s. Start with `AdminPage` (one fetch, no mutations — easiest win), then `ProfilePage` (four reads), then the polling cluster (`AppShell`), then the pages with mutations (`AuctionsPage`, `TradesPage`, `CollectionPage`).

## Why this approach

- **SWR is the smallest thing that buys back the listed bugs.** Caching, dedup, cancellation, refetch-on-focus, refetch-on-interval, mutation invalidation — all behind a single hook. The team learns *one* primitive (`useSWR(key, fetcher)`). Compare to React Query's `QueryClient` + `QueryClientProvider` + `useQuery` + `useMutation` + `invalidateQueries` + `queryKey` — same idea, four times the surface.
- **Cache key = URL path is the cheapest mental model.** No `['album', usuario_id]` key arrays, no key factories. The cache key is the thing in the URL bar (conceptually). Invalidation reads as "this URL's response is stale." For a project this size, that's enough — and it lines up perfectly with the backend's REST shape (see [REST-01](../backend/REST-01-verbs-in-urls.md) for why making URLs *the* identifier matters).
- **The custom-hook alternative is honest but more work.** A 30-line `useFetch(key)` with a `Map` cache is a great learning exercise and the team would understand SWR more deeply for having tried it. The downside is that the team then maintains it forever, including the edge cases SWR has already solved (focus revalidation, request dedup under React strict mode, abort propagation). If a team member wants the exercise, do it for one page as a learning tour, then keep SWR for the rest. Don't ship the hand-rolled version as the production answer.
