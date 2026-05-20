# Frontend Evaluation — TP TACS 2026-C1

Senior code review of the React 19 + Vite + Tailwind frontend. Companion to `../backend/`. Same shape as the backend reports: per-finding diagnosis, file:line evidence, one recommendation with a small code sample, and the tradeoff behind the recommendation.

## State of the frontend

The frontend reads well for an intern-team project this size. The layered split (`pages/`, `components/`, `components/ui/`, `context/`, `api/`, `utils/`) is intentional and consistent; the `apiFetch` wrapper sits cleanly between the pages and the backend; the six domain modules in `api/*.js` all funnel through it. The Tailwind setup is *especially* good — 20+ semantic CSS-variable-backed tokens (`primary`, `surface-container-low`, `on-primary-container`) defined in `index.css` and exposed via `tailwind.config.js`, with `darkMode: 'class'` correctly wired. The component primitives in `components/ui/` (Button, Modal, Tabs, Card, Chip, etc.) are mostly clean and small. The PATCH-on-state pattern from the backend is mirrored where it should be. Things to copy from internally: `HomePage.jsx:64-91`'s cancelled-flag effect (this is the *correct* async pattern, just not generalized), the `EMPTY_PUB`/`EMPTY_FALT` constants in `CollectionPage`, the `cargarDatos` helper composition in `AuctionsPage`, and the design-token approach across components.

The biggest debt is **server-state management**. Every page reinvents the same loading/error/refetch boilerplate, every error is silently swallowed by `.catch(() => {})`, no page uses `AbortController` (so unmount-during-fetch races are quietly waiting), and there's no cache — `listarMiAlbum()` runs four separate times across `HomePage`, `CollectionPage`, and `SearchPage`. This shows up as three intertwined reports: STATE-01 (the recommendation is **SWR**, deliberately not React Query or Redux), API-01 (the `apiFetch` shape SWR will use — structured errors, AbortController, timeout, 422 array handling), and ASYNC-01 (the fire-and-forget pattern and a `usePoll` helper to consolidate the three near-identical pollers in `AppShell`). Adopt SWR and most of the bug surface from those three reports dissolves at once.

The medium-severity findings are all hygiene: 13 `useState`s per page with modal/form state fragmented across 3-4 slots (HOOKS-01); `sessionStorage` writes during a `useState` initializer + `localStorage` storing what is conceptually server state (STORAGE-01); triple-nested ternaries and arbitrary pixel values across the otherwise-good Tailwind setup (STYLES-01); essentially zero mobile breakpoints across the entire `src/` tree (RESP-01); no Prettier, ESLint not in CI, no frontend job at all (TOOL-01). Start with STATE-01 + API-01 + ASYNC-01 — they're cross-referenced and benefit from being written together. Then take the mediums in any order. DUP-01 and LIB-01 are low-priority polish, worth doing during quiet moments between entregas.

## How to read these reports

Each report has the same shape:

- **Diagnosis** — what's happening, with file:line evidence, anchored to a named principle (Hook rules, UI = f(state), the staleness/race patterns in `useEffect`, the FastAPI 422 contract, etc.).
- **Evidence** — file:line bullets. No prose, just receipts.
- **Recommendation** — one named approach plus a short code sample (~10-25 lines).
- **Why this approach** — 2-3 bullets covering the tradeoff against the obvious alternative.

**Severity legend.** **C** critical (security or correctness), **H** high (debt that compounds), **M** medium (consistency / hygiene), **L** low (style / nit).
**Effort legend.** **S** small (under an hour), **M** medium (one session), **L** large (a sprint slice).

## Findings

| # | Code | Title | Sev | Effort | One-line synopsis |
|---|------|-------|-----|--------|-------------------|
| 1 | [STATE-01](./STATE-01-no-server-state-library.md) | No server-state library — every page reinvents loading/error/cache | **H** | M | Recommend SWR. One fetcher, one cache, no more `useState + useEffect + cancelled` boilerplate. |
| 2 | [API-01](./API-01-apifetch-shape.md) | `apiFetch` is too thin — no abort, no timeout, no 422 array handling | **H** | S-M | Build the fetcher SWR will consume: structured errors, AbortController, timeout, content-type sniffing. |
| 3 | [ASYNC-01](./ASYNC-01-fire-and-forget-and-races.md) | Fire-and-forget Promises + missing AbortController | **H** | M | Empty `.catch(() => {})` swallows errors across four pages; no page uses AbortController; unmount races are silently waiting. |
| 4 | [HOOKS-01](./HOOKS-01-state-explosion-custom-hooks.md) | `useState` explosion + fragmented modal/form state | **M** | S-M | 13 `useState`s on `HomePage`/`CollectionPage`/`AuctionsPage`. Custom hooks (`useModal`, `useForm`, `useAsync`) absorb the boilerplate. |
| 5 | [STORAGE-01](./STORAGE-01-session-and-local-storage.md) | `sessionStorage` write-during-render; `localStorage` holds server state | **M** | S | `UserContext` writes in a `useState` initializer; dismissed-alerts persistence belongs on the backend. |
| 6 | [STYLES-01](./STYLES-01-tailwind-discipline.md) | Long ternary classNames + arbitrary pixel values + inline-style/Tailwind mix | **M** | S-M | `Chip`, `Card`, `Button`, NavLink each grow a triple-ternary; `text-[13px]` repeats; `clsx` + lookup tables clean it up. |
| 7 | [RESP-01](./RESP-01-no-mobile-breakpoints.md) | No mobile breakpoints — the UI is desktop-only | **M** | M | Zero `sm:`/`md:`/`lg:` usage in `src/`; fixed pixel widths everywhere; the TP UI demo doesn't reflow below ~1100px. |
| 8 | [TOOL-01](./TOOL-01-prettier-eslint-ci.md) | No Prettier; ESLint not gated in CI; no frontend job at all | **M** | S | Backend CI runs pytest; frontend has `npm run lint` but nothing runs it. One YAML job closes the gap. |
| 9 | [DUP-01](./DUP-01-component-and-timer-duplication.md) | `FiguritaCard` compact mode + `FiguritaMini` duplicate; `SubastaCardRow` re-rolls its own timer | **L-M** | S | Two near-identical mini cards; AppShell and SubastaCardRow both tick at 60s. Consolidate. |
| 10 | [LIB-01](./LIB-01-date-and-class-utilities.md) | Hand-rolled date math; class-name concatenation begging for `clsx` | **L** | S | `date-fns` at the boundary; `clsx` everywhere a ternary becomes a template literal. Small but high-clarity. |

Reports above are roughly in execution order: HIGH first (and STATE-01 is the keystone that simplifies the others), then MEDIUM hygiene, then LOW polish. Severity is the source of truth for "what to fix next."
