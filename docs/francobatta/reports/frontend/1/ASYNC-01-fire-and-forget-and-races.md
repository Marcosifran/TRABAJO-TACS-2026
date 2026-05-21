# ASYNC-01 — Fire-and-forget Promises and unmount races

**Severity:** H  ·  **Area:** Async  ·  **Effort:** M

## Diagnosis

Four pages launch network requests from `useEffect` and either swallow errors with `.catch(() => {})` or write a `try { ... } catch { /* ignorar */ }` with no surfacing. None of them use `AbortController`. The combination is exactly the React anti-pattern that the FAQ in the React docs warns about, and it produces three failure modes the team will hit before Entrega 3:

1. **Silent failures.** When the API returns an error (token wrong, server down, validation failure), the user sees the page render `—` or `0` and assumes "no data yet" — there's nothing on screen distinguishing "still loading" from "failed." `HomePage.jsx:41-62` fires six independent calls and swallows every one. `ProfilePage.jsx:21-40`, `AdminPage.jsx:25-28` (single call, swallowed), and `NotificationsPage.jsx:33-53` (the whole `Promise.all` swallowed in a `catch { /* ignorar */ }`) follow the same shape.

2. **Unmount-during-fetch state updates.** None of these effects pass a signal to `apiFetch`. When the user navigates away during a slow request, the response still arrives and calls `setX(...)`. React 18+ silently no-ops the update (it does not warn anymore), but the side-effects — caches, logs, `console.error` from a `JSON.parse` — still run. Worse, the `Promise.all` shape in `HomePage:64-91` does correctly use a `let cancelled = true` flag on the cleanup, which means **the team already knows the pattern** — they just haven't applied it consistently. `HomePage:41-62` ignores its own playbook.

3. **Race conditions when the dependency key changes.** `SearchPage` (debounced fetch by query terms) and `AppShell`'s three polling loops (`AppShell.jsx:52-76, 79-104, 107-133`) each re-fire on user switch. The polling loops at least clear their `setInterval` on cleanup — but neither aborts the *in-flight* request from the previous user, so the new tokenized response could arrive after the user has been switched, then write that user's data into the wrong user's cache. With `setInterval(20s)` and a backend that's instant in dev, the window is small; under network latency it becomes visible.

A subset of pages get partial credit. `HomePage:64-91` uses `let cancelled = false` correctly. `AuctionsPage:83-87` uses a `setInterval` for the 60-second `now` tick and cleans it up. `NotificationsPage:55-65 dismiss()` uses `setTimeout` for a fade animation **without** unmount cleanup — if the user navigates away within 400ms of dismissing, the timeout still fires and `setLeidas(...)` is called on an unmounted component (no-ops but wasteful, and the localStorage write at `:60` *does* happen).

The cross-page polling layer in `AppShell.jsx:52-133` deserves a callout. Three `useEffect`s — sugerencias, trade proposals, auction-by-vencer — each set up an independent 20s poll. They all share the same idea ("compare current ids to seen ids, fire a notif if there are new ones") implemented three times with three subtle differences in the cleanup. This is the duplication ratio that makes a custom hook (`usePoll(fn, intervalMs, deps)`) compelling.

The single highest-leverage fix here is not "patch every fetch with AbortController." It is **adopt SWR** ([STATE-01](./STATE-01-no-server-state-library.md)) and let it own the staleness/cancellation/dedup. SWR's `useSWR(key, fetcher)` handles each of the three failure modes above as a side effect of how the cache is structured. This report's recommendation therefore comes in two layers: the SWR path (preferred) and the manual fix (for the corners SWR doesn't cover, like the `setTimeout` in `dismiss()`).

## Evidence

- `frontend/src/pages/HomePage.jsx:41-62` — six `.catch(() => {})` Promise chains in a single effect; no cancellation
- `frontend/src/pages/ProfilePage.jsx:21-40` — four fetches, every error swallowed
- `frontend/src/pages/AdminPage.jsx:24-29` — `obtenerEstadisticas().then(...).catch(() => {}).finally(...)`
- `frontend/src/pages/NotificationsPage.jsx:33-53` — `try { Promise.all([...]) } catch { /* ignorar */ }`
- `frontend/src/pages/HomePage.jsx:64-91` — **the correct pattern, locally**: `let cancelled = false` + check before each `setX`
- `frontend/src/components/AppShell.jsx:52-76, 79-104, 107-133` — three near-identical poll effects with hand-rolled `seenXIds.current` state and `setInterval` cleanup
- `frontend/src/pages/NotificationsPage.jsx:55-65, 67-82` — `dismiss`/`dismissAll` setTimeouts without unmount cleanup
- `frontend/src/components/SubastaCardRow.jsx:18-21` — 60s `setInterval` correctly cleared

## Recommendation

**Layer 1 — adopt SWR for the read path** (see [STATE-01](./STATE-01-no-server-state-library.md) for the broader case). SWR cancels stale requests on key change, dedups in-flight requests, and provides `data`/`error`/`isLoading` natively. The fire-and-forget pattern stops existing.

**Layer 2 — for the cases SWR doesn't cover (write actions, animations, polling side-effects)**, two small primitives close the rest:

```js
// frontend/src/hooks/useAsyncAction.js
import { useState, useCallback } from 'react'

export function useAsyncAction(fn) {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState(null)
  const run = useCallback(async (...args) => {
    setPending(true); setError(null)
    try {
      return await fn(...args)
    } catch (e) {
      setError(e); throw e
    } finally {
      setPending(false)
    }
  }, [fn])
  return { run, pending, error }
}

// frontend/src/hooks/usePoll.js
import { useEffect } from 'react'

export function usePoll(fn, intervalMs, deps = []) {
  useEffect(() => {
    let cancelled = false
    const controller = new AbortController()
    async function tick() {
      try { await fn(controller.signal) } catch { /* swallowed by design */ }
    }
    tick()
    const id = setInterval(() => { if (!cancelled) tick() }, intervalMs)
    return () => {
      cancelled = true
      controller.abort()
      clearInterval(id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
}
```

`usePoll` replaces the three near-identical effects in `AppShell.jsx:52-133` with three one-liners. The `fn` receives a `signal` it can pass to `apiFetch` (after [API-01](./API-01-apifetch-shape.md) lands), so the previous request is cancelled before the next tick fires — race resolved.

For the `setTimeout` in `NotificationsPage:55-65`, the fix is to track the timer in a ref and clear it on unmount:

```js
const fadeTimers = useRef(new Map())
const dismiss = useCallback((id) => {
  setFading(prev => new Set([...prev, id]))
  const tid = setTimeout(() => {
    setLeidas(prev => { const next = new Set([...prev, id]); saveLeidas(next); return next })
    setFading(prev => { const s = new Set(prev); s.delete(id); return s })
    fadeTimers.current.delete(id)
  }, FADE_MS)
  fadeTimers.current.set(id, tid)
}, [])

useEffect(() => () => {
  fadeTimers.current.forEach(clearTimeout)
}, [])
```

Files that change: new `frontend/src/hooks/useAsyncAction.js`, `frontend/src/hooks/usePoll.js`; `AppShell.jsx` (three effects collapse); `NotificationsPage.jsx` (`dismiss`/`dismissAll` timer cleanup); pages that issue write actions (`HomePage`, `CollectionPage`, `TradesPage`, `AuctionsPage`, `SearchPage`) opt into `useAsyncAction` for cleaner pending/error.

## Why this approach

- **Most of the bugs go away "for free" once SWR is in.** Don't fix the fire-and-forget reads by hand — replace them with `useSWR`. The reads become cancel-on-unmount, dedup-in-flight, refetch-on-focus by default. Layer 2 only exists for the *writes* (POST/PATCH/DELETE) and the *non-network* timers, both of which SWR intentionally leaves to you.
- **A `usePoll(fn, ms)` hook is a forcing function for consistency.** Today the three `AppShell` polls drift apart in detail (one uses a `Set`, one starts with `new Set()`, one starts with `null` and reassigns on first tick). Tomorrow none of them drift, because there's one implementation. This is the *real* benefit — not lines saved, but invariants captured.
- **Don't catch-and-ignore as the default.** If a fetch failure is acceptable (best-effort poll), say so by **passing an explicit `onError: () => {}`** to SWR or by writing `// best-effort: stat fails close to '—'` next to the catch. The reader should be able to tell whether the silence is intentional. Today every `.catch(() => {})` looks identical, whether the author meant "ignore" or "I'll handle this later." Naming the intent costs nothing.
