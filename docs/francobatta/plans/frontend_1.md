 Frontend Evaluation Plan — TP TACS 2026-C1

 Context

 This plan covers the frontend review, the companion to the backend evaluation already delivered at docs/francobatta/reports/backend/. The team is
 interning on a React 19 + Vite + Tailwind SPA that talks to the FastAPI backend over X-User-Token-authenticated REST. The UI is fully built
 (Entrega 2 is complete) and the team is heading into Entrega 3 (real persistence). The user — acting as a senior reviewer — wants the same shape of
  deliverable: a set of per-finding reports each describing what's off, how to fix it, and why, written so an intern can act on them without further
  explanation.

 Three Explore sweeps mapped the codebase down to file:line evidence: (1) pages — hooks, state shape, async patterns; (2) data layer — apiFetch,
 contexts, storage, library survey; (3) presentation — components, Tailwind discipline, libraries. The findings below are curated from those sweeps
 and tuned by three clarifying choices the user made during planning:

 - JS-only. Stay in JavaScript. Mention where typing would help, but no dedicated TS / JSDoc migration report.
 - Lightweight state management. The team should adopt SWR (or a small custom cache hook) — not React Query, not Redux. The concept surface needs to
  be small enough that the team can absorb it mid-entrega.
 - Skip the accessibility round. The TP doesn't ask for it; intern bandwidth is finite. A future entrega can layer it in.

 Scope

 In scope. Everything under frontend/src/. Specifically:
 - React-idiomatic hook usage, state shape, derived data, effect cleanup, custom-hook opportunities.
 - Async/Promise discipline — fire-and-forget, race conditions on unmount/filter-change, AbortController absence, error swallowing.
 - Server-state management — the cost of useState + useEffect for every endpoint, recommendation of a lightweight library (SWR-shaped).
 - API client (api/client.js) — error normalization (incl. FastAPI 422 array detail), timeout, abort, header injection, token-read pattern.
 - Storage (sessionStorage / localStorage) — what's stored, why, where it would be better held in module state, server state, or URL state.
 - Styling — Tailwind discipline, ternary-className sprawl, arbitrary pixel values, custom-token usage, dark-mode patterns, responsive design.
 - Component decomposition — duplication between FiguritaCard and FiguritaMini, timer ownership in AppShell vs SubastaCardRow, primitives in
 components/ui/.
 - Tooling — ESLint config, Prettier absence, CI gates for the frontend (today: none).
 - Small library opportunities — date-fns at the boundary, where utility helpers help.

 Out of scope (this round).
 - Backend (already delivered).
 - TypeScript migration / dedicated JSDoc track.
 - Accessibility / WCAG.
 - Spanish naming — treat as OK.
 - Visual design review (color choices, typography). Tailwind discipline is in scope; aesthetics are not.
 - Telegram bot bonus, cloud deployment, load testing.

 Evaluation Framework

 For each dimension, the evaluator asks these questions. Answers — backed by file:line evidence — feed the inventory.

 Hook usage and state shape

 - Does each page collapse multiple useStates for the same logical domain into a structured value or custom hook?
 - Are useEffects purposeful (single concern, narrow deps), or do they fan out unrelated side-effects?
 - Are useMemo/useCallback justified by real cost, or premature?
 - Are there custom hooks pulling out repeated fetch / loading / error / refetch boilerplate?
 - Does any state hold something derivable from other state or props?

 Server-state management

 - Is there any library handling cache, dedup, refetch, mounted-state? (Today: no.)
 - How much of every page is loading/error/refetch boilerplate that a 10-line useFetch would absorb?
 - Which user stories actively suffer from the absence — polling, after-action refresh, cross-page consistency?
 - What's the lightest tool that buys back the most value (SWR, a custom hook, none)?

 Async/Promise safety

 - Is every async call awaited? Are errors caught (and surfaced) or swallowed?
 - Is there an AbortController (or a "mounted" flag) protecting effects?
 - Race conditions when filters/user/route change mid-fetch — are they considered?
 - Promise.all for independent ops vs sequential await? setTimeout/setInterval cleanup?

 API client

 - apiFetch error normalization — does it handle FastAPI 422 (detail is an array, not a string)?
 - Timeout, AbortController, retry, content-type sniffing — present or absent?
 - Token read — fresh per call, or cached? Coupling between UserContext writing and apiFetch reading?
 - Per-domain modules — uniform shape, naming, no fetch bypasses?

 Storage

 - Every site that touches sessionStorage / localStorage. What's there, why?
 - Are write-during-render patterns present? Hydration risks?
 - Is anything in client storage that's really server state (NotificationsPage dismissed alerts)?
 - Are there better alternatives — in-memory module state, URL params, server-owned state?

 Styling and components

 - Tailwind: utility-first vs @apply mixes? Long ternary classNames vs cva/lookup tables?
 - Arbitrary pixel values (text-[13px]) vs theme scale?
 - Custom-token usage vs one-off hex values?
 - Dark-mode wiring; responsive design (the audit found essentially zero sm:/md: use).
 - Primitives in components/ui/ — clean prop API, ref forwarding, sensible defaults?
 - Domain components — duplication between FiguritaCard compact mode and FiguritaMini; timer logic shared between AppShell and SubastaCardRow.

 Tooling

 - ESLint config: which rules, run where (today: only locally via npm run lint; not in CI).
 - Prettier presence (today: absent).
 - Frontend CI (today: none — only backend pytest).
 - Small library wins — date-fns, maybe clsx/cn, possibly class-variance-authority for variants.

 Major Findings Inventory

 The audits surfaced ~25 issues. The curated set below rises to "major finding" — each becomes one report. Sub-findings get folded into the most
 relevant major so the deliverable stays focused.

 Severity legend (same as backend): C critical, H high, M medium, L low. Effort: S small (under an hour), M medium (one session), L large.

 ┌─────┬────────────┬────────────────────────────────────────────┬─────┬────────────────────────────────────────────────────────────────────────┐
 │  #  │    Code    │                   Title                    │ Sev │                              Key evidence                              │
 ├─────┼────────────┼────────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────┤
 │ 1   │ STATE-01   │ No server-state library — every page       │ H   │ Pages each maintain 4-13 useStates, every fetch repeats the            │
 │     │            │ reinvents loading/error/cache              │     │ loading/error/refetch shape; package.json has no SWR/RQ/Zustand        │
 ├─────┼────────────┼────────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────┤
 │     │            │ apiFetch is too thin — no abort, no        │     │ api/client.js:17-19 stringifies array detail; no AbortController; no   │
 │ 2   │ API-01     │ timeout, no 422 array handling, no         │ H   │ timeout; assumes JSON response                                         │
 │     │            │ validation-error surface                   │     │                                                                        │
 ├─────┼────────────┼────────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────┤
 │     │            │ Fire-and-forget Promises + missing         │     │ HomePage:41-62, ProfilePage:21-40, AdminPage:25-28,                    │
 │ 3   │ ASYNC-01   │ AbortController → unmount races and silent │ H   │ NotificationsPage:33-53 start fetches with empty .catch(() => {}); no  │
 │     │            │  failures                                  │     │ page uses AbortController                                              │
 ├─────┼────────────┼────────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────┤
 │     │            │ useState explosion + fragmented modal/form │     │ 13 useStates on HomePage, CollectionPage, AuctionsPage; modal state    │
 │ 4   │ HOOKS-01   │  state; missing custom hooks               │ M   │ split across 3-4 useStates per page; dismiss/dismissAll setTimeouts in │
 │     │            │                                            │     │  NotificationsPage:55-82 lack cleanup                                  │
 ├─────┼────────────┼────────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────┤
 │     │            │ sessionStorage write-during-render in      │     │ UserContext.jsx:20-25 writes to sessionStorage inside the useState     │
 │ 5   │ STORAGE-01 │ UserContext; localStorage holds what is    │ M   │ initializer; NotificationsPage.jsx:16-20 persists dismissed alert IDs  │
 │     │            │ really server state                        │     │ in localStorage (no cross-tab/cross-device sync)                       │
 ├─────┼────────────┼────────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────┤
 │     │            │ Long ternary classNames + arbitrary pixel  │     │ Chip.jsx:9-18, Card.jsx:11-20, AppShell.jsx:163-169 triple-nested      │
 │ 6   │ STYLES-01  │ values + mixing inline style={...} with    │ M   │ ternaries; text-[13px], w-[38px], text-[15px] ~15 sites; inline        │
 │     │            │ Tailwind                                   │     │ gradients in FiguritaCard.jsx:5-16, 37, 59, 63                         │
 ├─────┼────────────┼────────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────┤
 │ 7   │ RESP-01    │ No mobile breakpoints — the UI is          │ M   │ Across the entire src/, no sm:/md:/lg: Tailwind prefix is used;        │
 │     │            │ desktop-only                               │     │ fixed-pixel widths in AppShell, Modal, FiguritaCard                    │
 ├─────┼────────────┼────────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────┤
 │     │            │ No Prettier; ESLint not run in CI; npm run │     │ eslint.config.js enables react-hooks rules; .github/workflows/         │
 │ 8   │ TOOL-01    │  lint exists but is not gated              │ M   │ contains only the backend job; no .prettierrc; usuarios.py:7-style     │
 │     │            │                                            │     │ dead imports go uncaught in the frontend equally                       │
 ├─────┼────────────┼────────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────┤
 │     │            │ FiguritaCard compact mode + FiguritaMini   │     │ FiguritaCard.jsx:32-51 vs FiguritaMini.jsx; SubastaCardRow.jsx:23-24   │
 │ 9   │ DUP-01     │ duplicate logic; SubastaCardRow            │ L-M │ does its own new Date().getTime() math next to the existing            │
 │     │            │ reimplements auctionTime utilities         │     │ utils/auctionTime.js                                                   │
 ├─────┼────────────┼────────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────┤
 │     │            │ Hand-rolled date math; small library wins  │     │ utils/auctionTime.js:1-24, WorldCupSchedule.jsx:83-91,                 │
 │ 10  │ LIB-01     │ (date-fns, clsx)                           │ L   │ SubastaCardRow.jsx:23-24; long className concatenations across         │
 │     │            │                                            │     │ primitives that clsx would clean up                                    │
 └─────┴────────────┴────────────────────────────────────────────┴─────┴────────────────────────────────────────────────────────────────────────┘

 Sub-findings folded in (so they don't get lost):
 - The four-times-fetched buscarPublicaciones across HomePage, SearchPage, CollectionPage — STATE-01 (dedup).
 - Card.jsx:4 useState for hover where CSS :hover would do — HOOKS-01.
 - ThemeContext not persisted — STORAGE-01.
 - Modal.jsx:13 inline style={{ maxWidth: '90vw' }} mixed with Tailwind — STYLES-01.
 - AppShell.jsx:250-255 inline <style> tag for @keyframes slideInRight — STYLES-01 (move to index.css).
 - No ref forwarding on Input.jsx — STYLES-01 (prop API hygiene), noted but not the headline.
 - FLAG_COLORS hex literals in FiguritaCard.jsx:5-16 — STYLES-01.

 Report Template (Medium Depth)

 Each finding is one Markdown file under docs/francobatta/reports/frontend/. Filename pattern: {CODE}-{kebab-title}.md, e.g.
 STATE-01-no-server-state-library.md. Each follows the same shape as the backend reports so the team has one reading model:

 # {CODE} — {Title}

 **Severity:** {C|H|M|L}  ·  **Area:** {State | API | Async | Hooks | Storage | Styles | Responsive | Tooling | Duplication | Libraries}  ·
 **Effort:** {S|M|L}

 ## Diagnosis
 Two or three paragraphs. What is happening, with file:line evidence. Anchor to a named principle (React Hook rules, UI = f(state), the
 staleness/race patterns in `useEffect`, the FastAPI 422 contract, etc.). Connect cross-cutting impact (e.g. STATE-01 dissolves much of ASYNC-01).

 ## Evidence
 Short list of file:line citations. One line each.

 ## Recommendation
 One named approach + one short code sample (~10-25 lines), before/after. If the fix touches multiple files, note them by path under the sample.

 ## Why this approach
 2-3 bullets. The tradeoff against the obvious alternative (e.g. why SWR not React Query, why a custom hook not Redux, why `cva` not raw ternaries).
  Connect to a longer-lived constraint (Entrega 3 swap, future Telegram bot, performance budget).

 Matches the user's prior "Medium" depth choice.

 Deliverables

 docs/francobatta/reports/frontend/
 ├── README.md                                ← executive summary / index
 ├── STATE-01-no-server-state-library.md
 ├── API-01-apifetch-shape.md
 ├── ASYNC-01-fire-and-forget-and-races.md
 ├── HOOKS-01-state-explosion-custom-hooks.md
 ├── STORAGE-01-session-and-local-storage.md
 ├── STYLES-01-tailwind-discipline.md
 ├── RESP-01-no-mobile-breakpoints.md
 ├── TOOL-01-prettier-eslint-ci.md
 ├── DUP-01-component-and-timer-duplication.md
 └── LIB-01-date-and-class-utilities.md

 README.md mirrors the backend index:
 - A 3-paragraph "state of the frontend" preamble (what's good, what's the biggest debt, what to do first).
 - An inventory table identical in shape to the backend's, with severity column.
 - A "How to read these reports" note (severity legend, effort legend, template shape).

 No standalone roadmap — severity in the index is the roadmap.

 Execution Order

 When the user approves and we leave plan mode:

 1. Scaffold docs/francobatta/reports/frontend/ with README.md (header + empty inventory table).
 2. Write the three HIGH reports first (STATE-01, API-01, ASYNC-01). They're the most cross-referenced and they share file evidence — writing them
 together keeps the citations consistent. STATE-01 writes last of the three because API-01's recommended apiFetch shape is the fetcher that SWR will
  consume.
 3. Write the MEDIUM reports (HOOKS-01, STORAGE-01, STYLES-01, RESP-01, TOOL-01) — order is interchangeable; do them in whatever order keeps reviews
  small.
 4. Write the LOW-M / LOW reports (DUP-01, LIB-01).
 5. Polish the executive summary — once all rows are filled, write the 3-paragraph "state of the frontend" preamble.

 Critical files to keep referenced while writing (recurring anchors):
 - frontend/src/api/client.js (the fetcher; STATE-01, API-01)
 - frontend/src/api/*.js (per-domain modules; STATE-01, API-01)
 - frontend/src/context/UserContext.jsx, ThemeContext.jsx (STORAGE-01, STATE-01)
 - frontend/src/pages/HomePage.jsx, CollectionPage.jsx, AuctionsPage.jsx, NotificationsPage.jsx (HOOKS-01, ASYNC-01)
 - frontend/src/components/AppShell.jsx, SubastaCardRow.jsx, FiguritaCard.jsx, FiguritaMini.jsx (DUP-01, STYLES-01)
 - frontend/src/components/ui/Chip.jsx, Card.jsx, Button.jsx, Modal.jsx, Tabs.jsx, Input.jsx (STYLES-01)
 - frontend/src/utils/auctionTime.js (LIB-01)
 - frontend/tailwind.config.js, frontend/src/index.css (STYLES-01)
 - frontend/eslint.config.js, frontend/package.json (TOOL-01, STATE-01 — lib selection)

 Verification

 Deliverable is documentation. Verification is editorial:

 - Per-report self-check: every file:line cited resolves to the line claimed (open and confirm); the code sample reads as valid JS/JSX; the "Why
 this approach" addresses at least one explicit tradeoff (no "always do X").
 - Cross-report consistency: STATE-01's useSWR snippet and API-01's apiFetch shape must compose (the same fetcher passed into SWR). ASYNC-01's
 recommendations should say "SWR handles much of this; if you don't adopt SWR, here's the manual fix." Run a final consistency pass over all three
 HIGH reports as a group.
 - Index completeness: every report in the inventory exists and is linked from README.md; every report links back to README.md; severity in the file
  header matches severity in the index.
 - Intern-readability spot check: read STATE-01 and HOOKS-01 cold, pretend you're a 2nd-year student — can you act on them without asking a
 question? If not, expand the "Why this approach" bullets or the code sample.

 Optional follow-up after the reports land: open a draft PR with the docs folder so the team can comment inline. Not requested — don't push without
 explicit approval.
 