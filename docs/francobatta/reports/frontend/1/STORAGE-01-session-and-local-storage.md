# STORAGE-01 — `sessionStorage` write-during-render; `localStorage` holds server state

**Severity:** M  ·  **Area:** Storage / State  ·  **Effort:** S

## Diagnosis

Browser storage shows up in three places in the frontend. Each one is doing something subtly off — none of them critical, all of them worth correcting because storage choices set conventions the team will copy in the next entrega.

**1. `UserContext` writes `sessionStorage` during a `useState` initializer.** `UserContext.jsx:18-25`:

```jsx
const [index, setIndex] = useState(() => {
  const saved = sessionStorage.getItem('figuswap-user-index')
  const i = saved !== null ? parseInt(saved) : 0
  // Síncrono: el token queda disponible antes de cualquier efecto hijo
  sessionStorage.setItem('figuswap-token', USERS[i].token)
  return i
})
```

The comment is honest about the motivation: the token must be in storage *before* any child effect fires, otherwise `apiFetch` reads an empty token. The mechanism — performing a side-effect inside an initializer — is what React Strict Mode is specifically designed to catch. In dev, Strict Mode runs the initializer twice; the side-effect runs twice. Today the side-effect is idempotent (writing the same string twice), so nothing observable breaks. But the pattern itself is the kind of thing a senior reviewer notices, and the moment a future developer adds a non-idempotent side-effect (incrementing a counter, logging an analytics event), the second run causes a bug.

The right fix is to make the token a *derivation* of the active index — read it on demand, don't store it twice. Storage holds one thing (the active index); `apiFetch` reads it through a getter, not from a redundant second key.

**2. `figuswap-token` exists twice, in two modules, by string.** `UserContext.jsx:23, 31` writes it; `client.js:3-5` reads it; no other module knows the key name. If the key is ever renamed, both files must change in lockstep. The `figuswap-user-index` key has the same issue but only `UserContext` touches it, so it's lower risk.

**3. `NotificationsPage` persists dismissed alert IDs in `localStorage`.** `NotificationsPage.jsx:12, 15-20`:

```jsx
const STORAGE_KEY = 'figuswap-alertas-leidas'
function loadLeidas() { ... return new Set(JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')) }
function saveLeidas(set) { localStorage.setItem(STORAGE_KEY, JSON.stringify([...set])) }
```

The intent is reasonable — when the user dismisses a notification, it should stay dismissed across page refreshes. But the implementation locates that fact in the wrong place: **"this user has seen alert X" is server state masquerading as client state**. Symptoms:

- Open the app in two tabs. Dismiss an alert in tab A; tab B still shows it as un-dismissed. There's no sync.
- Open the app on a different device or browser. All previously dismissed alerts are back.
- Two users share a browser (the TP literally runs with two seeded test users in the same bundle). Dismissals leak between them because the key isn't user-scoped — every user shares one `figuswap-alertas-leidas`.

The right model is server-side: a `POST /usuarios/me/alertas/{id}/dismiss` endpoint, plus the alert payload carrying a `dismissed: bool` flag. That's an Entrega-3 conversation, so the recommendation here is to **scope the localStorage key by user** (one cheap fix) **and** to flag the deeper migration for when the backend grows the route.

**4. `ThemeContext` is not persisted at all.** `ThemeContext.jsx:5-12`:

```jsx
const [dark, setDark] = useState(() =>
  window.matchMedia('(prefers-color-scheme: dark)').matches
)
useEffect(() => {
  document.documentElement.classList.toggle('dark', dark)
}, [dark])
```

The first render reads the OS preference, which is the right default. But every time the user explicitly toggles to "dark" or "light" against their OS preference, the choice is forgotten on the next page load. This is the opposite of the alertas-leidas problem — here the team has an *under*-storage, where the others have *over*-storage. The fix is a single `localStorage` write on toggle and a single read on mount, falling back to the OS preference.

## Evidence

- `frontend/src/context/UserContext.jsx:18-25` — sessionStorage side-effect inside `useState` initializer
- `frontend/src/context/UserContext.jsx:23, 31` and `frontend/src/api/client.js:3-5` — `figuswap-token` key referenced by two modules
- `frontend/src/context/UserContext.jsx:19, 30` — `figuswap-user-index` key
- `frontend/src/pages/NotificationsPage.jsx:12, 15-20, 30, 58-62, 75-78` — `figuswap-alertas-leidas` in localStorage, not user-scoped
- `frontend/src/context/ThemeContext.jsx:5-12` — `dark` state not persisted

## Recommendation

Four small moves. Each is independently shippable.

**Move 1 — make the token a derivation, not a separate stored value.**

```jsx
// frontend/src/context/UserContext.jsx
const STORAGE_KEY_INDEX = 'figuswap-user-index'

export function UserProvider({ children }) {
  const [index, setIndex] = useState(() => {
    const saved = sessionStorage.getItem(STORAGE_KEY_INDEX)
    return saved !== null ? parseInt(saved, 10) : 0
  })

  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY_INDEX, String(index))
  }, [index])

  const user = USERS[index]
  return (
    <UserContext.Provider value={{ user, users: USERS, switchUser: setIndex }}>
      {children}
    </UserContext.Provider>
  )
}
```

```js
// frontend/src/api/client.js — read the token from the active index
import { USERS, STORAGE_KEY_INDEX } from '../context/UserContext'

function token() {
  const saved = sessionStorage.getItem(STORAGE_KEY_INDEX)
  const i = saved !== null ? parseInt(saved, 10) : 0
  return USERS[i]?.token || ''
}
```

The `figuswap-token` key disappears. One module (`UserContext`) owns the active index; another (`client.js`) derives the token. No more "two keys must agree."

**Move 2 — scope `figuswap-alertas-leidas` by user.**

```js
// frontend/src/pages/NotificationsPage.jsx
const STORAGE_KEY = (userId) => `figuswap-alertas-leidas:user-${userId}`

function loadLeidas(userId) {
  try { return new Set(JSON.parse(localStorage.getItem(STORAGE_KEY(userId)) || '[]')) }
  catch { return new Set() }
}
// ...same for saveLeidas, plus useEffect-driven reload when user changes
```

This is a one-day fix. The medium-term goal is server-side dismissal — flagged for Entrega 3 when alerts become a proper resource on the backend (today they're computed live in `AppShell:52-133` and have no persistent identity).

**Move 3 — persist theme.**

```jsx
// frontend/src/context/ThemeContext.jsx
const THEME_KEY = 'figuswap-theme'
const initial = () => {
  const saved = localStorage.getItem(THEME_KEY)
  if (saved === 'dark' || saved === 'light') return saved === 'dark'
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}
// ...useEffect writes localStorage.setItem(THEME_KEY, dark ? 'dark' : 'light')
```

**Move 4 — `useLocalStorageState` hook (optional but cleans the next case up).**

```js
// frontend/src/hooks/useLocalStorageState.js
import { useState, useEffect } from 'react'

export function useLocalStorageState(key, initial) {
  const [value, setValue] = useState(() => {
    try {
      const saved = localStorage.getItem(key)
      return saved !== null ? JSON.parse(saved) : (typeof initial === 'function' ? initial() : initial)
    } catch { return initial }
  })
  useEffect(() => {
    try { localStorage.setItem(key, JSON.stringify(value)) } catch { /* quota */ }
  }, [key, value])
  return [value, setValue]
}
```

Files that change: `frontend/src/context/UserContext.jsx`, `frontend/src/api/client.js`, `frontend/src/pages/NotificationsPage.jsx`, `frontend/src/context/ThemeContext.jsx`, new `frontend/src/hooks/useLocalStorageState.js`.

## Why this approach

- **Storage should hold one fact, derive the rest.** Today there are two storage keys for the same fact (active user index ↔ active user's token). Two keys cannot diverge if there's only one — that's the invariant the derivation gives you. The pattern repeats whenever you find two keys that always update together: collapse them to one.
- **Persisting through `useEffect` instead of inside an initializer is the React-idiomatic fix.** The initializer is for *reading*. The effect is for *writing in response to state changes*. Strict Mode then can't break you, and the pattern works for any client storage (sessionStorage, localStorage, IndexedDB).
- **The dismissed-alerts case teaches the broader rule: "if it matters across sessions, devices, or users, it lives on the server."** localStorage is fine for per-browser preferences (theme, sidebar collapsed/expanded, "I dismissed this banner once"). It is not fine for read state, draft data the user cares about not losing, or anything other-user-visible. Scoping by user is a good *interim* fix; flagging that this resource should move server-side in Entrega 3 is the *real* one.
