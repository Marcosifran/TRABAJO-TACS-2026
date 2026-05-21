# STYLES-01 — Long ternary classNames + arbitrary pixel values + inline-style/Tailwind mix

**Severity:** M  ·  **Area:** Styles  ·  **Effort:** S-M

## Diagnosis

The Tailwind setup is impressively well-thought-through at the **token** layer. `tailwind.config.js:7-32` declares 20+ semantic color tokens (`primary`, `surface-container-low`, `on-primary-container`, etc.) that map to CSS variables defined in `index.css:6-63`, and `darkMode: 'class'` (`tailwind.config.js:4`) drives dark mode via a single class toggle. The vast majority of components use those tokens — `bg-primary`, `text-on-surface-variant`, `border-outline-variant`. That's the right way to use Tailwind for a themed app, and the team should be proud of it. **Keep this part.**

What's drifted, in three forms:

**1. Triple-nested ternary classNames.** The pattern repeats across primitives whenever there are three+ visual states:

- `Chip.jsx:9-18` — `disabled ? ... : selected ? ... : ...` produces a 4-line template literal embedded in JSX.
- `Card.jsx:11-20` — `elevated ? ... + (hovered ? ... : ...) : ...` plus three more conditional class fragments below. Eight class-string fragments in one element.
- `AppShell.jsx:163-169` — `isActive ? 'bg-primary-container text-on-primary-container font-semibold' : 'text-on-surface-variant hover:bg-surface-variant font-normal'` — only two states here, but the template literal with newlines makes it look like five.
- `Button.jsx:34` — `parseInt(SIZES[size].match(/text-\[(\d+)/)?.[1] || 14) + 2` — a *regex against a className string* to derive an icon size. Clever, fragile.

Each is fine in isolation. Together they teach the team that "long ternary chains in className" is normal. The fix is to extract the variant table into a JS object (the team already did this in `Button.jsx:3-14` with `VARIANTS`/`SIZES`), or to adopt `clsx` to compose conditional classes by name.

**2. Arbitrary pixel values bypass the theme scale.** A grep of `text-\[` and `w-\[` shows ~15 sites:

- `AppShell.jsx:142` — `w-[38px] h-[38px]`
- `AppShell.jsx:148` — `text-[18px]`
- `AppShell.jsx:149, 197, 205, 206` — `text-[13px]`, `text-[11px]`
- `FiguritaCard.jsx:62` — `h-[68px]`
- `FiguritaCard.jsx:81-82` — `text-[15px]`, `text-[13px]`
- `FiguritaMini.jsx:8, 17-18` — `rounded-[10px]`, `text-[13px]`, `border-[1.5px]`
- `Chip.jsx:10` — `text-[13px]`
- `Modal.jsx:13, 14` — `max-h-[85vh]`, `maxWidth: '90vw'` (the latter is *inline style*, not Tailwind)

`text-[13px]` and `text-[11px]` recur enough that they're really "the small variants of the text scale." Tailwind's default `text-xs` is 12px, `text-sm` is 14px — close but not what the design wants. The fix is to **extend `theme.fontSize` in `tailwind.config.js`** and use a named class. Same for the pixel-width tokens that recur.

**3. Inline `style={...}` mixed with Tailwind classes.** Eight sites:

- `AppShell.jsx:143` — `style={{ background: 'linear-gradient(135deg, var(--color-primary), var(--color-tertiary))' }}` (valid; CSS vars in inline gradients can't be Tailwind-ified easily)
- `AppShell.jsx:231` — `style={{ animation: 'slideInRight 0.3s ease' }}` with `:250-255` inline `<style>` tag in JSX defining the keyframes. Move both to `index.css`.
- `FiguritaCard.jsx:37, 59, 63` — `style={{ background: cardGradient(figurita.seleccion) }}` driven by `FLAG_COLORS` hex literals at `:5-16` (`#74ACDF`, `#009C3B`, etc.). These are *team colors* — they're domain data, not theme. The hex literals are fine because they encode real-world flag colors; what's missing is that they're declared in a component file instead of `src/utils/flagColors.js`.
- `Card.jsx:10` — `style={style}` passthrough (allows callers to inject arbitrary inline styles; weak boundary).
- `Modal.jsx:14` — `style={{ width, maxWidth: '90vw' }}` where `width` is a prop. `width` could be a Tailwind class (`w-[520px]`) but at the boundary of "this prop is a number from the caller" inline style is the least-bad option. Note that responsive sizing belongs in [RESP-01](./RESP-01-no-mobile-breakpoints.md).
- `HomePage.jsx:148, 150, 231-234` — inline gradient using a CSS variable, fine.

The inline-style choices that **are** fine are the ones where the value is dynamic (a gradient computed from a runtime value). The ones to fix are the static animation in `AppShell` and the hard-coded `maxWidth: '90vw'` in `Modal` (`max-w-[90vw]` is a one-character swap that keeps the rule in the class string with everything else).

**4. Component-level inline `<style>` tag in JSX.** `AppShell.jsx:250-255` injects a `@keyframes slideInRight` rule by rendering a `<style>` element. The rule survives unmount (it stays in the DOM), but conceptually animations belong in `index.css`. Two-line move.

## Evidence

- `frontend/src/components/ui/Chip.jsx:9-18` — triple-nested ternary
- `frontend/src/components/ui/Card.jsx:11-20` — multi-conditional className with hover-state-as-useState (see also [HOOKS-01](./HOOKS-01-state-explosion-custom-hooks.md))
- `frontend/src/components/AppShell.jsx:163-169` — `NavLink` className
- `frontend/src/components/ui/Button.jsx:34` — regex against className to compute icon size
- `frontend/src/components/AppShell.jsx:142, 148, 149, 197, 205, 206` — `text-[Npx]`, `w-[Npx]` arbitrary values
- `frontend/src/components/FiguritaCard.jsx:5-16` — `FLAG_COLORS` hex literals declared in a component file
- `frontend/src/components/AppShell.jsx:231, 250-255` — inline `style={{ animation }}` + inline `<style>` tag
- `frontend/src/components/ui/Modal.jsx:14` — `maxWidth: '90vw'` as inline style
- `frontend/src/components/ui/Card.jsx:10` — `style={style}` passthrough

## Recommendation

Four small moves. Each fits in its own PR.

**Move 1 — adopt `clsx` for conditional classes.**

```jsx
// frontend/src/components/ui/Chip.jsx
import clsx from 'clsx'
import Icon from './Icon'

const STATES = {
  disabled: 'border-outline/40 bg-transparent text-on-surface/30 cursor-not-allowed',
  selected: 'border-primary bg-primary-container text-on-primary-container cursor-pointer',
  default:  'border-outline bg-transparent text-on-surface-variant hover:bg-surface-variant cursor-pointer',
}

export default function Chip({ children, selected, onClick, icon, disabled }) {
  const state = disabled ? 'disabled' : selected ? 'selected' : 'default'
  return (
    <button
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      title={disabled ? 'Próximamente' : undefined}
      className={clsx(
        'inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs-plus font-medium border transition-all duration-200',
        STATES[state],
      )}
    >
      {icon && <Icon name={icon} size={16} className={clsx({
        'text-on-surface/30': disabled,
        'text-on-primary-container': !disabled && selected,
        'text-on-surface-variant': !disabled && !selected,
      })} />}
      {children}
    </button>
  )
}
```

The triple-nested ternary becomes a state-name lookup. The `Icon`'s color uses `clsx`'s object syntax which reads like a truth table. `text-xs-plus` is the named font-size from Move 3.

**Move 2 — kill the regex in `Button.jsx`.** Replace the icon-size computation with an explicit map:

```jsx
const ICON_SIZE = { sm: 14, md: 16, lg: 18 }
// in JSX:
{icon && <Icon name={icon} size={ICON_SIZE[size]} />}
```

Same intent, no regex against a className.

**Move 3 — extend the theme scale instead of arbitrary values.**

```js
// frontend/tailwind.config.js
fontSize: {
  '2xs':       ['11px', '14px'],   // current text-[11px]
  'xs-plus':   ['13px', '18px'],   // current text-[13px]
  'sm-plus':   ['15px', '22px'],   // current text-[15px]
  'lg-plus':   ['18px', '24px'],   // current text-[18px]
},
spacing: {
  '38':        '38px',             // current w-[38px] h-[38px]
  '68':        '68px',
},
```

Then `text-[13px]` becomes `text-xs-plus`, `w-[38px]` becomes `w-38`. The pattern documents itself and a future "small font is now 12px" change is one config edit.

**Move 4 — move `FLAG_COLORS` to `src/utils/flagColors.js`** (domain data, not component code) and the inline `<style>` keyframe to `index.css`:

```css
/* frontend/src/index.css */
@keyframes slideInRight {
  from { transform: translateX(110%); opacity: 0; }
  to   { transform: translateX(0);    opacity: 1; }
}
.animate-slide-in-right { animation: slideInRight 0.3s ease; }
```

```jsx
// frontend/src/components/AppShell.jsx — replace inline style and inline <style>
<div className="... animate-slide-in-right">
```

Files that change: `frontend/package.json` (`npm install clsx`); `frontend/src/components/ui/{Chip,Card,Button,Modal}.jsx`, `frontend/src/components/AppShell.jsx`; `frontend/tailwind.config.js` (extend scale); `frontend/src/index.css` (add animation); new `frontend/src/utils/flagColors.js`; `frontend/src/components/FiguritaCard.jsx` (import flag colors from utils).

## Why this approach

- **`clsx` is the minimal Tailwind-idiomatic helper.** It's ~250 bytes gzipped, no learning curve (the API is "pass strings, objects, or arrays; falsy values are skipped"), and it composes with itself. The team should not adopt `class-variance-authority` *yet* — `cva` is the right tool when the variant matrix grows past three dimensions; today most components have ≤2 dimensions (state × size) and `clsx` + a lookup table is plenty.
- **Theme scale beats arbitrary values, even for two repeats.** The moment `text-[13px]` appears in three files, naming it (`text-xs-plus`) creates a vocabulary. The cost is one config line; the benefit is the next developer searches for the name, finds the convention, and copies it instead of inventing a new arbitrary value. Tailwind specifically warns about arbitrary-value sprawl for this reason.
- **Animations and domain data belong in their natural homes.** The inline `<style>` tag in `AppShell` works — it doesn't break anything — but it teaches the wrong pattern. The team will reach for it again the next time they need a one-off keyframe, and the second instance is the one that gets duplicated. `FLAG_COLORS` belongs in `utils/` because it's data that other components might use (`FiguritaMini` doesn't today, but a future "team summary" card might). Move data out of components on the first opportunity, not the third.
