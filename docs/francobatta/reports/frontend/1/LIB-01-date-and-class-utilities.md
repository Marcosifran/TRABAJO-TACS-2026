# LIB-01 — Hand-rolled date math; class-name concatenation begging for `clsx`

**Severity:** L  ·  **Area:** Libraries  ·  **Effort:** S

## Diagnosis

Two small library introductions would clean up code that has already been written by hand and would be re-written by hand for every new feature. Neither is urgent. Both are educational and trivial to adopt. They're in the same report because the rationale is identical: **borrow boring solved problems instead of growing them in-house.**

**1. Date math is hand-rolled.** The team has correctly centralized two formatting helpers in `utils/auctionTime.js:1-23`:

```js
export function formatTiempoRestante(finIso) {
  if (!finIso) return ''
  const ms = new Date(finIso).getTime() - Date.now()
  if (ms <= 0) return 'Finalizada'
  const horas = Math.floor(ms / 3600000)
  const mins = Math.floor((ms % 3600000) / 60000)
  return horas > 0 ? `${horas}h ${mins}m` : `${mins}m`
}
```

That works, today. The reasons it's worth replacing:

- The "auction has 1 day, 4 hours left" case becomes verbose to add by hand (`24+ hours` requires another branch). With `date-fns`, `formatDistanceToNow(new Date(finIso), { addSuffix: false, locale: es })` returns `"alrededor de 4 horas"` / `"5 días"` natively.
- Locale support: the team is writing Spanish strings. `date-fns/locale/es` exists and gives the correct pluralization (`"hace 1 hora"` vs `"hace 2 horas"`) without the team writing `s ? 'horas' : 'hora'` ternaries everywhere.
- `WorldCupSchedule.jsx:83-91` parses dates from `dd-mm-yyyy` strings by hand. `date-fns/parse(str, 'dd-MM-yyyy', new Date())` does the same in one call with proper error handling for malformed inputs.

`date-fns` is tree-shakeable — `import { formatDistanceToNow } from 'date-fns'` only bundles that one function. Total cost: ~3kB gzipped for the typical set. The alternative — `dayjs`, `luxon`, `moment` — are larger and/or more opinionated. `date-fns` is the boring default.

**2. Class-name concatenation across the UI primitives.** Same observation as [STYLES-01](./STYLES-01-tailwind-discipline.md) but at the library-introduction level: `clsx` is a 240-byte gzipped helper that replaces template-literal-with-ternaries with an idiomatic function call.

Before:

```jsx
className={`
  flex items-center gap-2.5 px-3 py-2 rounded-[10px] cursor-pointer transition-all
  border-[1.5px]
  ${selected
    ? 'bg-primary-container border-primary'
    : 'bg-surface-container border-transparent hover:border-outline-variant'
  }
`}
```

After (with `clsx`):

```jsx
className={clsx(
  'flex items-center gap-2.5 px-3 py-2 rounded-xs-plus cursor-pointer transition-all border-[1.5px]',
  selected
    ? 'bg-primary-container border-primary'
    : 'bg-surface-container border-transparent hover:border-outline-variant',
)}
```

Marginal in a single component. Adds up across the 14 component files. More importantly, `clsx` *encourages* the team to keep the static and dynamic class fragments separate, which makes the dynamic decisions easy to spot when reading.

**3. The team should resist adding lodash.** A quick grep across `src/` for the patterns lodash typically targets — `_.groupBy`, `_.uniqBy`, `_.debounce`, `_.cloneDeep` — finds essentially none. The single debounce is in `SearchPage.jsx` via a manual `setTimeout`/`clearTimeout` ref dance; that's worth a tiny `useDebounce` hook locally but not a lodash dependency. Modern JS plus a couple of one-liners covers what the team needs. **Don't preemptively add lodash.** Mention only if a real grouping/deep-equality use case appears.

## Evidence

- `frontend/src/utils/auctionTime.js:1-23` — hand-rolled formatter, no locale support
- `frontend/src/sections/WorldCupSchedule.jsx:83-91` — manual date string parsing with `split('-')` and `parseInt`
- `frontend/src/components/ui/Chip.jsx:9-18`, `Card.jsx:11-20`, `Button.jsx:27-32`, `AppShell.jsx:163-169` — template-literal + ternary class composition (the `clsx` case)
- `frontend/src/components/FiguritaMini.jsx:7-14` — same template-literal pattern in a domain component
- `frontend/package.json:12-16` — no utility library deps
- `frontend/src/pages/SearchPage.jsx` — debounce implementation (manual `setTimeout`/`clearTimeout`); the only debounce in the codebase

## Recommendation

```bash
npm install date-fns clsx
```

**Date refactor.**

```js
// frontend/src/utils/auctionTime.js — after
import { formatDistanceToNow, parseISO } from 'date-fns'
import { es } from 'date-fns/locale'

export function formatTiempoRestante(finIso) {
  if (!finIso) return ''
  const fin = typeof finIso === 'string' ? parseISO(finIso) : finIso
  if (fin.getTime() <= Date.now()) return 'Finalizada'
  return formatDistanceToNow(fin, { locale: es })  // e.g. "alrededor de 2 horas"
}

export function lineaCierraEn(finIso) {
  const t = formatTiempoRestante(finIso)
  if (t === '' || t === 'Finalizada') return t
  return `Cierra en ${t}`
}
```

Note the test fixtures probably check string format like `"2h 15m"` — those tests (there are none today, but if [TOOL-01](./TOOL-01-prettier-eslint-ci.md) ever introduces frontend tests) would need to update to the `date-fns` output format. Worth keeping the output format consistent if you want to avoid a UI-text change: stick with the custom formatter for *this* function and use `date-fns` for the *new* needs only (24h+ branches, the World Cup parser). Either is defensible — the recommendation is to migrate fully, but the team can choose to keep the existing strings and use `date-fns` only for `parseISO` and the WorldCup parser.

For the WorldCup schedule:

```js
import { parse, format } from 'date-fns'
import { es } from 'date-fns/locale'

const fecha = parse(item.fecha, 'dd-MM-yyyy', new Date())
const label = format(fecha, "d 'de' MMMM", { locale: es })  // "10 de junio"
```

**`clsx` refactor.** Covered in [STYLES-01](./STYLES-01-tailwind-discipline.md). Don't duplicate the code samples here.

Files that change: `frontend/package.json`; `frontend/src/utils/auctionTime.js`; `frontend/src/sections/WorldCupSchedule.jsx`; every component file using `clsx` (already covered by STYLES-01's plan).

## Why this approach

- **`date-fns` is the smallest library that solves the real problem.** Manual date arithmetic works until the day someone writes `now.getHours() - fin.getHours()` to compute hours-difference and gets it wrong across midnight or DST. The library has tested those edge cases for years. The bundle cost is bounded because of tree-shaking — you only pay for what you import.
- **`clsx` doesn't add concepts.** It's a glorified `[a, b, c].filter(Boolean).join(' ')`. The team learns nothing new; they just write less. That's the right trade-off for a low-severity library introduction: the team's time is better spent on the higher-impact reports (STATE-01, ASYNC-01) than on inventing class composition primitives.
- **Hold the line on dependencies otherwise.** No lodash, no `moment`, no `react-icons` (the team is using Material Symbols via class names, which works), no Redux. Two small adds, well-justified, with clear use sites. The TP grading favors clean dependency lists; senior reviewers favor honest ones. Don't add a library you won't use in three places by the end of the entrega.
