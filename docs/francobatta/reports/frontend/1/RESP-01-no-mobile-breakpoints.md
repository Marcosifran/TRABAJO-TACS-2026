# RESP-01 — No mobile breakpoints; the UI is desktop-only

**Severity:** M  ·  **Area:** Responsive  ·  **Effort:** M

## Diagnosis

The TP spec asks for a UI that's "fácil de utilizar" and explicitly allows either web or Telegram. The team chose web — and the web app today is **desktop-only**. Across the entire `src/` tree there is essentially one Tailwind responsive prefix: `AuctionsPage.jsx:359` (`grid-cols-1 md:grid-cols-2`). Everywhere else the layout assumes a viewport wide enough for a 256px sidebar plus a 700-1100px content column.

The shape of the problem:

**1. `AppShell` sidebar is `w-64` (256px) and not collapsible.** `AppShell.jsx:138`. Below ~700px viewport, the sidebar plus any content column overflows; the user gets horizontal scroll. There's no hamburger trigger, no `md:hidden` to hide the sidebar, no drawer overlay for mobile.

**2. Page-level `max-w-[Npx]` is fixed.** `HomePage.jsx:135` (`max-w-[1100px]`), `CollectionPage`, `SearchPage`, `TradesPage`, `AuctionsPage.jsx:232` (`max-w-[1000px]`), `NotificationsPage.jsx:94` (`max-w-[700px]`), `ProfilePage.jsx:52` (`max-w-[800px]`). These are container widths, but the *grids inside* are sized in fixed columns: `HomePage.jsx:142` is `grid-cols-4 gap-4` for the stats — four cards across, no fallback. On a 375px-wide phone screen, four stat cards each become ~70px wide, which clips numbers.

**3. Modals are sized to 520px / 480px / 500px** (`Modal.jsx:14` default `width = 520`). The `maxWidth: '90vw'` fallback keeps them inside the viewport, which is good — they at least fit. But the *content* inside is laid out in a 2-column grid (`HomePage.jsx:280`, `AuctionsPage.jsx:397` — `grid-cols-2 gap-2` for figurita selection). Two columns in 90vw of a 375px phone leaves ~150px per column, which truncates names.

**4. `FiguritaCard` and `SubastaCardRow` use `flex justify-between` with text on one side and a button on the other.** `FiguritaCard.jsx:54` is the card mode; `SubastaCardRow.jsx:28`. The flex layout doesn't wrap — at narrow widths the button shrinks until the icon clips. Wrapping is a one-line fix (`flex-wrap`) but the team would also need `gap-2` to look reasonable when wrapped.

**5. Inline media-query expressions.** None. Tailwind has `sm:` (640px), `md:` (768px), `lg:` (1024px), `xl:` (1280px) breakpoints out of the box. The team is using none of them except the one site noted above.

The good news is that **the design tokens are already responsive-friendly** — the color/elevation/border-radius system from [STYLES-01](./STYLES-01-tailwind-discipline.md) doesn't change at breakpoints. So the cost of adding mobile is purely *layout* changes (`grid-cols-N` becomes `grid-cols-1 md:grid-cols-N`; sidebar collapses to a drawer below `md:`; fixed widths drop). The cost is also **time-bounded** to one work session if approached system-wide, instead of the page-by-page fix that the team will be tempted to do.

This is a Medium severity finding only because the TP doesn't explicitly require mobile and because the team is grading on web. The reason it's *not* Low: the next time a reviewer opens this app on their phone (and they will), the desktop-only-ness is the first thing they see. The fix is mechanical; the perception cost of *not* fixing it is large.

## Evidence

- `grep -r 'sm:\|md:\|lg:\|xl:' frontend/src/` → only `AuctionsPage.jsx:359` matches
- `frontend/src/components/AppShell.jsx:138` — `w-64 shrink-0` (fixed 256px sidebar, no mobile collapse)
- `frontend/src/components/AppShell.jsx:136` — `flex h-screen overflow-hidden` (no mobile rearrange)
- `frontend/src/pages/HomePage.jsx:142` — `grid-cols-4 gap-4` stats (no `grid-cols-1 md:grid-cols-4`)
- `frontend/src/pages/HomePage.jsx:168` — `grid-cols-2 gap-6` content area
- `frontend/src/pages/HomePage.jsx:280, AuctionsPage.jsx:397` — modal content `grid-cols-2 gap-2`
- `frontend/src/components/ui/Modal.jsx:14` — `style={{ width, maxWidth: '90vw' }}` (only this dimension is responsive)
- `frontend/src/components/FiguritaCard.jsx:54, SubastaCardRow.jsx:28` — `flex justify-between` without `flex-wrap`

## Recommendation

Three layered fixes, each shippable independently. **Start with the grids — they're the highest leverage for the least work** — then handle the sidebar drawer, then the cards.

**Fix 1 — responsive grids in pages.** Pattern: `grid-cols-N` → `grid-cols-1 sm:grid-cols-2 md:grid-cols-N`. Apply to every grid in every page. About 12 sites.

```jsx
// frontend/src/pages/HomePage.jsx:142 — stats
<div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">

// frontend/src/pages/HomePage.jsx:168 — main content
<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

// frontend/src/pages/AdminPage.jsx:40 — admin cards
<div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">

// modal figurita-picker
<div className="max-h-[300px] overflow-y-auto grid grid-cols-1 sm:grid-cols-2 gap-2 p-1">
```

**Fix 2 — sidebar becomes a drawer below `md:`.** Two parts: render the sidebar as a fixed overlay on small screens with a hamburger toggle in the header; collapse the main area to be full-width below the same breakpoint.

```jsx
// frontend/src/components/AppShell.jsx — sketch
const [sidebarOpen, setSidebarOpen] = useState(false)

return (
  <div className="flex h-screen bg-surface text-on-surface overflow-hidden">
    {/* Mobile header — only visible below md */}
    <header className="md:hidden fixed top-0 left-0 right-0 z-40 bg-surface-container px-4 py-3 flex items-center justify-between border-b border-outline-variant">
      <button onClick={() => setSidebarOpen(true)} aria-label="Menú">
        <Icon name="menu" size={24} />
      </button>
      <div className="font-bold">FiguSwap</div>
    </header>

    {/* Backdrop for mobile drawer */}
    {sidebarOpen && (
      <div className="md:hidden fixed inset-0 bg-black/40 z-40" onClick={() => setSidebarOpen(false)} />
    )}

    {/* Sidebar: fixed overlay on mobile, static column on desktop */}
    <nav className={clsx(
      'w-64 shrink-0 bg-surface-container-low border-r border-outline-variant flex flex-col overflow-y-auto scrollbar-none',
      'fixed inset-y-0 left-0 z-50 transition-transform md:static md:translate-x-0',
      sidebarOpen ? 'translate-x-0' : '-translate-x-full',
    )}>
      {/* ...existing nav content... */}
    </nav>

    <main className="flex-1 overflow-y-auto pt-14 md:pt-0">
      {children}
    </main>
    {/* ...notification stack unchanged... */}
  </div>
)
```

The drawer uses `transform` (GPU-accelerated, no reflow) and `transition-transform` for the slide. `pt-14 md:pt-0` gives room for the mobile header without changing desktop layout.

**Fix 3 — card layouts wrap cleanly.**

```jsx
// frontend/src/components/SubastaCardRow.jsx:28
<div className="p-5 bg-surface rounded-2xl border border-outline-variant flex flex-wrap items-center gap-4 justify-between shadow-sm">
```

`flex-wrap` plus `gap-4` lets the button drop to a second line on narrow widths without overflow. The same pattern applies to `FiguritaCard` non-compact mode if needed; compact mode is already constrained enough that it fits.

**Page max-widths can stay fixed** because the `max-w-[1100px]` only triggers above 1100px viewport — under it, the page is naturally `100%`. The grid changes do the real work.

Files that change: every `pages/*.jsx` for grid attrs; `frontend/src/components/AppShell.jsx` for the drawer; `frontend/src/components/SubastaCardRow.jsx` and `FiguritaCard.jsx:54` for `flex-wrap`; `frontend/src/components/ui/Modal.jsx:14` if you want to make `width` `auto`-on-mobile (`style={{ width: typeof window !== 'undefined' && window.innerWidth < 640 ? '100%' : width }}` is *not* the right pattern — use a Tailwind class instead, see "Why this approach").

## Why this approach

- **Start with grids, not the sidebar.** Grids are pure className changes — no logic, no state, no risk. Each change is one PR and one visual diff. The team gets visible mobile progress immediately. The sidebar drawer is a larger change with state (the `sidebarOpen` flag, the body-scroll-lock concern) — do it second, when the small fixes have built confidence.
- **Don't read `window.innerWidth` from JS.** It's tempting (`if (mobile) ...`) but introduces hydration-style bugs and re-render thrash. Tailwind's `md:` prefix evaluates in CSS, which is faster, simpler, and works during SSR if the team ever adds it. The drawer pattern above keeps *all* the responsive logic in classNames; the only state is "is the drawer currently open," which is mobile-only and dismissible.
- **Mobile is not a feature — it's a configuration.** The current code makes mobile a feature by *not* writing it. Adding mobile is making the existing components work at multiple widths. Once `md:` prefixes exist in the page-level grids and the sidebar, every future component the team writes will naturally pick up the convention because it'll be the example next to where they're working. Without `md:` prefixes anywhere, the convention is "we don't think about mobile," which is sticky.
