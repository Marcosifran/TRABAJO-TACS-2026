# HOOKS-01 — `useState` explosion + fragmented modal/form state

**Severity:** M  ·  **Area:** Hooks  ·  **Effort:** S-M

## Diagnosis

The Dan Abramov-style maxim **UI = f(state)** only stays simple when the state stays simple. Three pages have grown past the threshold where individual primitives can be reasoned about together: `HomePage`, `CollectionPage`, and `AuctionsPage` each declare 13 separate `useState` calls. Several of them describe the same logical thing — a modal — split into three or four parallel slots.

The clearest case is the auction-bidding flow in `HomePage:31-39` and again in `AuctionsPage:38-44`:

```jsx
const [bidModal, setBidModal] = useState(null)        // open + which subasta
const [offerIds, setOfferIds] = useState([])          // selected figurita ids
const [miAlbum, setMiAlbum] = useState([])            // the data the modal renders
const [loadingOferta, setLoadingOferta] = useState(false)
```

These four are one *idea*: "the bid modal." They're written, read, and reset together. When you close the modal you want to reset all four at once. Today, closing requires `setBidModal(null); setOfferIds([])` (`HomePage:118-119, 222`) and any future field — say "comment to seller" — adds a fifth `setX(...)` call to every close site. The structure invites bugs: `AuctionsPage:368-371` resets `offerIds` on open, but the snackbar/loading slot uses the page-wide `loading` flag, so two modals can clobber each other's pending state if a user is fast enough.

The same shape repeats for forms. `CollectionPage:20-21` defines `EMPTY_PUB` and `EMPTY_FALT` (good — at least the empty value is centralized) but then carries `pubForm`, `faltForm`, `showPub`, `showFalt`, `submitting`, `submittingFalt` as six independent useStates. The submitting flag is per-modal, which is correct, but two parallel submitting flags are a sign that the *modal* should own its own pending state. `TradesPage:24-34` is the worst offender — `ratingModal`, `rating`, `comment`, `calificados` are four useStates for one rating modal, and `sugTradeModal`, `sugAlbum`, `sugSelectedOffer`, `sugSubmitting` are four more for the "suggestion → trade" modal.

A second axis of the same problem is **derived state held in `useState`**. `Card.jsx:4` tracks `hovered` via `useState` plus `onMouseEnter`/`onMouseLeave`. CSS `:hover` does this without re-rendering. Every hover toggles a state update that re-renders the card — invisible in dev, visible on a 4×4 stat grid scrolled rapidly on a mid-tier laptop. `HomePage:127-132` builds the `STATS` array on every render from four state values; that's fine (cheap to recompute, no need for `useMemo`) but is sometimes mistakenly memoized in other codebases — flag the pattern as a learning point.

A third related issue: **useState clusters are exactly the boundary where a custom hook belongs.** The "fetch + loading + error" pattern is the obvious one (handled in [STATE-01](./STATE-01-no-server-state-library.md) by SWR). The next-most-frequent pattern is "modal with a form" — open/close, form state, submitting flag, server error, success callback. Pulling that into a hook is a 30-line exercise that cleans up four pages at once.

A small but real correctness bug: `NotificationsPage:55-65` uses `setTimeout` inside `dismiss` with no cleanup ref. If the user dismisses an alert and navigates away within 400ms, the timeout still fires after unmount. The `setLeidas` call no-ops (React handles it), but the `saveLeidas` write to localStorage at `:60` *does* happen, and the next mount reads it back. The user-visible effect: an alert the user "almost" dismissed gets remembered as dismissed anyway. Captured in [ASYNC-01](./ASYNC-01-fire-and-forget-and-races.md) for completeness.

## Evidence

- `frontend/src/pages/HomePage.jsx:22-39` — 13 `useState`s
- `frontend/src/pages/CollectionPage.jsx:20-21, 33-49` — `EMPTY_PUB`/`EMPTY_FALT` constants plus six useStates for the two modal flows
- `frontend/src/pages/AuctionsPage.jsx:30-54` — 13 `useState`s, four of them describing "the bid modal"
- `frontend/src/pages/TradesPage.jsx:24-34` — eight useStates split between two modal flows
- `frontend/src/components/ui/Card.jsx:1-4` — `useState(false)` for hover; CSS `:hover` would do
- `frontend/src/pages/NotificationsPage.jsx:55-65, 67-82` — `setTimeout` in `dismiss`/`dismissAll` without unmount cleanup
- `frontend/src/pages/HomePage.jsx:118-119, 222` and `AuctionsPage.jsx:369-370` — manual multi-`setState` reset code at every modal-close site

## Recommendation

Two patterns. First, a `useModalForm` custom hook that gathers the four pieces of state every "modal that submits a form" needs. Second, replace `Card`'s `useState` hover with CSS.

```jsx
// frontend/src/hooks/useModalForm.js
import { useState, useCallback } from 'react'

export function useModalForm(initial) {
  const [open, setOpen] = useState(null)         // null | <context> ; truthy = open
  const [form, setForm] = useState(initial)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState(null)

  const close = useCallback(() => {
    setOpen(null)
    setForm(initial)
    setError(null)
  }, [initial])

  const openWith = useCallback((ctx = true) => {
    setForm(initial)
    setError(null)
    setOpen(ctx)
  }, [initial])

  return { open, openWith, close, form, setForm, pending, setPending, error, setError }
}
```

Usage in `HomePage.jsx`, replacing four useStates and the two manual reset sites:

```jsx
const bid = useModalForm({ offerIds: [] })

function toggleOferta(id) {
  bid.setForm(f => ({
    ...f,
    offerIds: f.offerIds.includes(id) ? f.offerIds.filter(x => x !== id) : [...f.offerIds, id],
  }))
}

async function handleOfertar() {
  if (bid.form.offerIds.length === 0) { /* snackbar */ return }
  bid.setPending(true)
  try {
    await ofertarSubasta(bid.open.id, bid.form.offerIds)
    setSnack({ open: true, message: 'Oferta enviada con éxito', type: 'success' })
    bid.close()
  } catch (e) {
    bid.setError(e); setSnack({ open: true, message: e.message, type: 'error' })
  } finally {
    bid.setPending(false)
  }
}

// in JSX:
<Modal open={!!bid.open} onClose={bid.close} title={`Ofertar en Subasta #${bid.open?.id}`} width={520}>
  {/* ...uses bid.form, bid.setForm, bid.pending... */}
</Modal>

// to open:
<SubastaCardRow ... onOfertar={s => bid.openWith(s)} />
```

`Card.jsx` hover fix:

```jsx
// before
const [hovered, setHovered] = useState(false)
<div onMouseEnter={...} onMouseLeave={...} className={`... ${hovered ? 'shadow-elev-2' : 'shadow-elev-1'} ...`}>

// after — pure CSS, no re-render
<div className={`... ${elevated ? 'shadow-elev-1 dark:shadow-elev-1-dark hover:shadow-elev-2 dark:hover:shadow-elev-2-dark hover:-translate-y-0.5' : 'border border-outline-variant'} ...`}>
```

(See also [STYLES-01](./STYLES-01-tailwind-discipline.md) for the longer-term shape of the `Card` className.)

Files that change: new `frontend/src/hooks/useModalForm.js`; `HomePage`, `CollectionPage`, `AuctionsPage`, `TradesPage`, `SearchPage` (each loses 3-4 useStates per modal); `Card.jsx` (delete the `useState`).

## Why this approach

- **A custom hook is the right *shape* for "things that change together."** Four useStates that always change together are conceptually one piece of state — they're only separate because `useState` is a primitive. A custom hook is the React-idiomatic way to bundle them while keeping the local-state model. Don't reach for `useReducer` here; reducers are for state machines, and these are mostly "set this, set that." `useReducer` is two steps further along the same path and worth introducing later if the modal flows get true branches (e.g. confirm-vs-cancel-vs-cooling-period).
- **CSS for hover is a tiny perf win and a much bigger correctness win.** A `useState`-driven hover means every mouseenter renders the component. Multiply by N cards on a page and the framework is doing a lot of work for a result that the browser already knows. The same applies to focus, active, and visited states — keep them in CSS unless React genuinely needs to know.
- **Don't migrate everything at once.** Move one modal in one page (e.g. `HomePage`'s bid modal) to `useModalForm`, ship it, see if it reads well. The hook will mutate as you discover real needs (a "confirm-before-close" flag, an "after-submit refetch key" — those should not be added speculatively). When all four modal pages use it, the test of whether the hook is right will be obvious: which one needed the most adjusting? That's the hook's API boundary.
