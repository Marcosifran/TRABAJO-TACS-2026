# TOOL-01 — No Prettier; ESLint not in CI; no frontend job at all

**Severity:** M  ·  **Area:** Tooling  ·  **Effort:** S

## Diagnosis

The frontend has the *configuration* for a healthy toolchain — and almost none of the *enforcement*. `eslint.config.js:1-29` declares the flat-config-style ESLint setup, including `reactHooks.configs.flat.recommended` (which enables the hook-rules linter — `react-hooks/exhaustive-deps`, etc.) and `reactRefresh.configs.vite`. `package.json:9` exposes `npm run lint`. Both are correct. The gap is that **nothing runs them**:

- The CI workflow at `.github/workflows/backend-tests.yml` only runs `pytest tests/` (see backend [TEST-01](../backend/TEST-01-tests-and-ci.md)). There is no `frontend-checks.yml`. No PR can fail CI because of a lint error.
- There is no `.prettierrc` or `.prettierrc.json`. Formatting drifts file-by-file — some pages use double quotes (`AuctionsPage.jsx` uses `"..."` consistently), most use single quotes (`HomePage.jsx`, `CollectionPage.jsx`, etc.). Indent style is consistent (2 spaces) but trailing commas and semicolons vary. The team appears to be relying on editor settings, which is silent drift waiting to happen across machines.
- ESLint inconsistencies that are uncaught today and would be caught the moment CI runs:
  - The `usuarios.py:7` style of dead import probably exists in the frontend too. Local lint hasn't been run recently enough to know.
  - `react-hooks/exhaustive-deps` would flag `HomePage.jsx:62` (effect depends on `users` but only lists `user`), `NotificationsPage.jsx:53` (no dependency on anything outside, fine, but warning if eslint detects something off), `AppShell.jsx:76, 104, 133` (each pushes via `pushNotif` which is *not* in deps — currently safe because `pushNotif` is stable in identity but ESLint can't prove it).
  - `react/jsx-key` is not in the recommended set by default (recommended config doesn't include the React plugin's rules), and the codebase mostly does this right, but a future bug here would slip through.

The team should also add a **build** step in CI — `npm run build` catches type-of-import bugs and Vite-specific issues (missing `index.html`, bad env-var refs) that lint can't.

A few smaller observations bundled in:

**Local `lint` is not in `package.json` as a `precommit` or `prepush` hook.** That's fine — heavy hooks slow people down — but the CI gate replaces the need.

**The `no-unused-vars` rule has a forgiving pattern.** `eslint.config.js:26` — `varsIgnorePattern: '^[A-Z_]'` allows unused uppercase constants. That covers things like a deliberately-unused `STATUS` enum, but also masks dead `EMPTY_PUB`-style constants that *are* exported but no longer used. Acceptable for now; flag it if it bites.

**Type-checking is not part of this report.** The project is JS-only and the user explicitly chose to stay JS-only during planning. If `// @ts-check` ever appears in `client.js` or context files, the CI step would natively type-check those files via VS Code or `tsc --noEmit --allowJs --checkJs`, but that's an opt-in per file and not within scope.

## Evidence

- `frontend/eslint.config.js:1-29` — ESLint flat config with `react-hooks/exhaustive-deps` enabled
- `frontend/package.json:8-10` — `"lint": "eslint ."` exists
- `.github/workflows/backend-tests.yml:1-30` — only backend job; no frontend job
- `frontend/` (repo root) — no `.prettierrc`, no `prettier.config.js`, no `prettier` in `package.json` devDeps
- `frontend/src/pages/AuctionsPage.jsx` vs `frontend/src/pages/HomePage.jsx` — double-quote vs single-quote inconsistency
- `frontend/src/pages/HomePage.jsx:62` — effect `[user]` deps but body reads `users` (likely `exhaustive-deps` warning)
- `frontend/src/components/AppShell.jsx:76, 104, 133` — three effects calling `pushNotif` (defined in component scope) without listing it as a dep

## Recommendation

Add a frontend CI job that runs `lint` and `build`; add Prettier as a formatter; integrate the two with ESLint so they don't fight.

**Step 1 — add Prettier.**

```json
// frontend/.prettierrc.json
{
  "singleQuote": true,
  "semi": false,
  "trailingComma": "all",
  "printWidth": 100,
  "arrowParens": "always"
}
```

```bash
npm install --save-dev prettier eslint-config-prettier
```

`eslint-config-prettier` turns off the ESLint rules that conflict with Prettier (formatting concerns); ESLint focuses on bugs, Prettier on formatting. Update `eslint.config.js`:

```js
import prettier from 'eslint-config-prettier'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
      prettier,    // ← last, so it disables conflicting rules
    ],
    // ...rest unchanged...
  },
])
```

Add `"format": "prettier --write ."` and `"format:check": "prettier --check ."` to `package.json` scripts.

**Step 2 — add a frontend CI job.**

```yaml
# .github/workflows/frontend-checks.yml
name: Frontend Checks

on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["**"]

jobs:
  check:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json
      - name: Install
        run: npm ci
      - name: Lint
        run: npm run lint
      - name: Format check
        run: npm run format:check
      - name: Build
        run: npm run build
        env:
          VITE_USER_1_TOKEN: dummy-ci-token-1
          VITE_USER_2_TOKEN: dummy-ci-token-2
```

The build step uses dummy env vars because the bundle reads `VITE_USER_*_TOKEN` at build time. They don't need to be real — they just need to exist so Vite doesn't fail on `import.meta.env.VITE_USER_1_TOKEN` resolving to `undefined`.

**Step 3 — run the formatter once across the codebase** to align the existing files, then let CI keep them aligned. Commit the result as a single PR titled "chore: apply Prettier formatting" so the diff doesn't pollute future code-review noise.

Files that change: new `frontend/.prettierrc.json`, new `.github/workflows/frontend-checks.yml`, modified `frontend/eslint.config.js`, modified `frontend/package.json` (devDeps + scripts), and a one-shot formatting commit touching most files.

## Why this approach

- **CI gates teach the team the rules without the team having to remember them.** A failing red mark on a PR for "missing dep in `useEffect`" is more pedagogical than a verbal review comment, and it scales. The team learns the React Hook rules by hitting them, then internalizes them.
- **Prettier + ESLint with the separation-of-concerns plugin (`eslint-config-prettier`) is the boring industry default.** ESLint catches *bugs* and *style violations that can't be auto-fixed* (e.g., empty catch blocks, accidental globals, hook-dep violations). Prettier catches *formatting*. Don't try to make ESLint format — the rules conflict and the experience is worse. Use both, with each doing one thing.
- **Adding the `build` step to CI is the secret weapon.** Lint catches a lot, but it doesn't catch `import` typos, missing exports, broken Vite plugin config, or env-var refs that don't resolve. `npm run build` does. It also takes about 15 seconds in CI, so the cost is trivial. Many of the bugs the team will hit between now and Entrega 3 are bundle-build bugs, and this catches them before they merge.
