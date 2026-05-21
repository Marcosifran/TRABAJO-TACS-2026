# DUP-01 — `FiguritaCard` compact + `FiguritaMini` duplicate; `SubastaCardRow` re-rolls its own timer

**Severity:** L-M  ·  **Area:** Components  ·  **Effort:** S

## Diagnosis

Two near-twins in the components folder, and a small-but-real duplication of "ticking time" logic. None of this is dangerous; all of it is the kind of drift that gets a senior reviewer's attention because it's *the easiest tier of refactor* — pure mechanical consolidation, no API changes, no risk.

**1. `FiguritaCard` compact mode and `FiguritaMini` solve the same problem with different code.**

`FiguritaCard.jsx:32-51` (compact mode):

```jsx
if (compact) {
  return (
    <div className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl bg-surface-container cursor-pointer hover:bg-surface-variant transition-colors">
      <div className="w-10 h-12 rounded-md ..." style={{ background: cardGradient(figurita.seleccion) }}>
        <span className="text-base font-bold text-white drop-shadow">#{figurita.numero}</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-semibold text-on-surface truncate">{figurita.jugador}</div>
        <div className="text-xs text-on-surface-variant">{figurita.seleccion}</div>
      </div>
      {figurita.cantidad != null && <span className="...">x{figurita.cantidad}</span>}
    </div>
  )
}
```

`FiguritaMini.jsx:3-22`:

```jsx
export default function FiguritaMini({ figurita, selected, onToggle }) {
  return (
    <div onClick={onToggle} className={`flex items-center gap-2.5 px-3 py-2 rounded-[10px] cursor-pointer ... ${selected ? '...' : '...'}`}>
      {selected && <Icon name="check_circle" size={18} className="text-primary shrink-0" />}
      <span className="text-[13px] font-semibold text-on-surface">#{figurita.numero}</span>
      <span className="text-[13px] text-on-surface-variant flex-1">{figurita.jugador}</span>
      <span className="text-xs text-on-surface-variant">{figurita.seleccion}</span>
    </div>
  )
}
```

Both render the same fields (`numero`, `jugador`, `seleccion`) in the same order, in a flex row, with the same padding/rounded look. The differences are real but small:

- `FiguritaMini` supports a *selected* state with a check icon and border highlight; `FiguritaCard compact` doesn't.
- `FiguritaCard compact` shows a flag-gradient block for the number; `FiguritaMini` shows the number as a small badge.
- `FiguritaCard compact` shows a `cantidad` chip; `FiguritaMini` doesn't.

Neither is used in both modes — `FiguritaCard compact` is for "summary list" (HomePage, ProfilePage), `FiguritaMini` for "selection list" (modal pickers). But the visual vocabulary is so close that a future "selectable summary" widget will copy one and accidentally rebuild the other. The right consolidation isn't to merge them — they have different jobs — but to make the *shared parts* (flex row, padding, truncation) a single reusable layout primitive, and let each variant compose it.

**2. `SubastaCardRow` has its own 60s timer next to `AppShell`'s, which already has three.**

`SubastaCardRow.jsx:16-21`:

```jsx
const [now, setNow] = useState(() => Date.now())
useEffect(() => {
  const id = setInterval(() => setNow(Date.now()), 60000)
  return () => clearInterval(id)
}, [])
```

`AuctionsPage.jsx:83-87` also sets up `setNow(Date.now())` every 60s for the same reason — to make `activa` (whether the auction is still open) recompute. The motivation is identical, but the implementations are independent: an `AuctionsPage`-level tick and one `SubastaCardRow`-per-card tick. If `AuctionsPage` renders 10 auction rows, that's *11* parallel `setInterval` timers updating every 60s. Each tick re-renders one extra component for no benefit.

The right consolidation is a single `useNow(intervalMs)` hook. `SubastaCardRow` calls it; `AuctionsPage` calls it. They get the same `now` value within a render. Pulling it up to a context wouldn't help much (the value would still propagate via re-render), but **using a single shared interval** instead of N independent timers does help — it's a small perf win and a learning moment about how `useEffect` cleanup interacts with re-mounting in a list.

A small bonus: `formatTiempoRestante` and `lineaCierraEn` in `utils/auctionTime.js` are imported by `AppShell.jsx:11, 120` and `SubastaCardRow.jsx:3, 25`. That's the right shape — they're not duplicated, just used. Keep this; what *is* duplicated is the `new Date(sub.fin).getTime() - ahora` arithmetic in `AuctionsPage.jsx:225` and `SubastaCardRow.jsx:23-24` and `NotificationsPage.jsx:46` and `HomePage.jsx:81`. That's a `isAuctionActive(sub)` helper waiting to be extracted.

## Evidence

- `frontend/src/components/FiguritaCard.jsx:32-51` — compact mode
- `frontend/src/components/FiguritaMini.jsx:3-22` — mini selection card
- `frontend/src/components/SubastaCardRow.jsx:16-21` — per-row 60s tick
- `frontend/src/pages/AuctionsPage.jsx:83-87` — page-level 60s tick (same purpose)
- `frontend/src/pages/AuctionsPage.jsx:225`, `frontend/src/components/SubastaCardRow.jsx:23-24`, `frontend/src/pages/NotificationsPage.jsx:46`, `frontend/src/pages/HomePage.jsx:81` — `new Date(sub.fin).getTime() > ahora` repeated four times

## Recommendation

Three small extractions.

**Extraction 1 — `FiguritaRow` layout primitive.**

```jsx
// frontend/src/components/FiguritaRow.jsx — new
export default function FiguritaRow({ children, onClick, selected, className = '' }) {
  return (
    <div
      onClick={onClick}
      className={clsx(
        'flex items-center gap-3 px-3.5 py-2.5 rounded-xl transition-colors',
        onClick && 'cursor-pointer',
        selected ? 'bg-primary-container border border-primary' : 'bg-surface-container hover:bg-surface-variant',
        className,
      )}
    >
      {children}
    </div>
  )
}
```

`FiguritaCard` (compact branch) and `FiguritaMini` both render `<FiguritaRow>` with their own children. The shared concerns — padding, rounded, hover, selected — live in one place. Each variant keeps its own children (check icon, gradient block, cantidad chip) — that's the *interesting* part of each.

**Extraction 2 — `useNow(intervalMs)` hook.**

```js
// frontend/src/hooks/useNow.js
import { useEffect, useState } from 'react'

/** Returns `Date.now()` and re-renders every `intervalMs`. Pure utility. */
export function useNow(intervalMs = 60_000) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), intervalMs)
    return () => clearInterval(id)
  }, [intervalMs])
  return now
}
```

`AuctionsPage` and `SubastaCardRow` both call `useNow()`. If `AuctionsPage` mounts 10 rows, each row owns its own interval but the interval is *named the same way*, lives in one place, and is the obvious thing to swap out if you decide a single shared tick is worth the context/provider boilerplate.

**Extraction 3 — `isAuctionActive(sub, now)` helper.**

```js
// frontend/src/utils/auctionTime.js — extend
export function isAuctionActive(sub, now = Date.now()) {
  if (!sub || sub.estado !== 'activa') return false
  const fin = sub.fin ? new Date(sub.fin).getTime() : 0
  return fin > now
}
```

Replace the four duplicated boolean expressions with `isAuctionActive(sub, now)`. The repeated `&& s.estado === 'activa' && ms > 0` boolean fragments collapse to a named predicate.

Files that change: new `frontend/src/components/FiguritaRow.jsx`; `frontend/src/components/FiguritaCard.jsx` (compact branch uses `FiguritaRow`); `frontend/src/components/FiguritaMini.jsx` (uses `FiguritaRow`); new `frontend/src/hooks/useNow.js`; `frontend/src/components/SubastaCardRow.jsx` + `frontend/src/pages/AuctionsPage.jsx` (use `useNow`); `frontend/src/utils/auctionTime.js` (add `isAuctionActive`); `frontend/src/pages/AuctionsPage.jsx`, `NotificationsPage.jsx`, `HomePage.jsx`, `SubastaCardRow.jsx` (use `isAuctionActive`).

## Why this approach

- **Extract the *layout*, not the *component*.** `FiguritaMini` and `FiguritaCard compact` are two products of the same layout idea. Merging them into one bigger component with a "mode" prop is the wrong move — the variants would balloon. Extracting the shared *layout* primitive (`FiguritaRow`) keeps each variant focused on its job (selection vs. summary) while sharing the visual chassis. This is the "favor composition over inheritance" rule, applied to JSX.
- **`useNow` is a one-line hook with a permanent home.** It's tempting to think it's not worth abstracting "two lines of `setInterval`+state." It is — because the name says *what*, and the deps array won't drift. The next "ticking timer" the team writes will use it instead of reinventing the pattern. Cheap to define, cheap to use, expensive to forget.
- **`isAuctionActive` makes the rules grep-able.** Today, four files independently know "active means `estado === 'activa'` AND `fin > now`." Tomorrow that definition changes (say, the backend introduces a `paused` state). Four files need editing if the predicate isn't named; one if it is. This is the cheapest form of the Domain Driven Design "ubiquitous language" idea — pick a name, use it everywhere.
