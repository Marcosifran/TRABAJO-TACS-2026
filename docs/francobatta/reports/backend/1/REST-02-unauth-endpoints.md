# REST-02 — Unauthenticated endpoints leak data

**Severity:** C  ·  **Area:** REST / Security  ·  **Effort:** S

## Diagnosis

Most protected resources correctly use `Depends(get_current_user)`. But four endpoints skip the dependency and are reachable by anyone who can hit the host. Three of them are reads; one of them is the **admin statistics endpoint**, which by name and by the user story (US-12 "Como administrador quiero ver estadísticas...") should be the most protected endpoint in the API.

The most concerning gap is **`admin.py:7-15`**: `GET /api/v1/admin/estadisticas` has no auth dependency *and* no role check. The handler signature is `def obtener_estadisticas():` — no `usuario` parameter at all. The TP spec mentions an admin role (US-12) but the implementation has no concept of one yet, so even adding `Depends(get_current_user)` is only a partial fix; what's needed is a role flag on the user dict and a small `require_admin` dependency that checks it.

The other three holes are less dramatic but follow the same root cause — endpoints declared without the dependency:

- **`subastas.py:9-19`** — `GET /api/v1/subastas/` returns every active auction. Auctions reference figuritas with `numero`, `equipo`, `jugador`, the owner's `usuario_id`, and times. An unauthenticated scraper can build a complete inventory.
- **`figuritas.py:10-26`** — `GET /api/v1/figuritas/` returns the figurita-publication index with `numero`, `equipo`, `jugador`, `usuario_id`. Same exposure as above; this is the most-trafficked endpoint.
- **`usuarios.py:78-87`** — `GET /api/v1/usuarios/{usuario_id}/reputacion`. Path-parameter user-id with no auth means anyone can enumerate `1..N` and harvest reputations. It also accepts the user id from the path even though the TP only has two users — i.e., the parameter exists only as an enumeration vector. (Compare with the *authenticated* endpoints in the same file like `listar_figuritas_usuario` at `usuarios.py:19`, which take the user id from the token. There's no reason for `obtener_reputacion` to be different.)

The shape of the holes is consistent: the FastAPI dependency system is opt-in per handler, and the failure mode of forgetting is silent. There's no app-wide default. That's a structural risk for an intern team. Even after closing these four, a fifth one tomorrow is one missing parameter away. The structural fix (Router-level dependency, see Recommendation) closes the class.

## Evidence

- `backend/app/routers/admin.py:13-15` — `def obtener_estadisticas():` — no `Depends`, no role check, returns full platform stats
- `backend/app/routers/subastas.py:15-19` — `def listar_subastas():` — no `Depends`
- `backend/app/routers/figuritas.py:16-26` — `def buscar_figuritas(...)` — no `Depends`; returns wrapped figuritas inventory
- `backend/app/routers/usuarios.py:86-87` — `def obtener_reputacion(usuario_id: int):` — path-id with no `Depends`; compare with `usuarios.py:19` which uses `Depends(get_current_user)`
- `backend/app/dependencies.py:7-11` — the dependency that should be applied

## Recommendation

Make auth a **router-level default** rather than a per-handler opt-in, then keep public endpoints (if any are truly public) as explicit exceptions.

```python
# backend/app/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user
from app.services import admin_service

def require_admin(usuario: dict = Depends(get_current_user)) -> dict:
    if not usuario.get("es_admin"):
        raise HTTPException(status_code=403, detail="Requiere rol de administrador")
    return usuario

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)],
)

@router.get("/estadisticas")
def obtener_estadisticas():
    return admin_service.obtener_estadisticas()
```

The router-level `dependencies=[Depends(require_admin)]` makes every route under `/admin` require an admin — there is no "I forgot the decorator" failure mode. Add an `es_admin: bool` flag to the seeded user dicts in `usuario_repo.py:4-7`.

For `subastas`, `figuritas`, and `usuarios`, apply the same pattern with `get_current_user` instead of `require_admin`:

```python
router = APIRouter(
    prefix="/subastas",
    tags=["Subastas"],
    dependencies=[Depends(get_current_user)],
)
```

…and remove the now-redundant `usuario: dict = Depends(get_current_user)` from each handler signature when the handler doesn't need the user dict, or leave it where the handler *does* (FastAPI deduplicates `Depends` instances in a single request).

The `/usuarios/{usuario_id}/reputacion` path is a separate question: do you want it public-but-authenticated (any logged-in user can see anyone's reputation, which matches the TP's reputation user-story) or scoped to self? The recommendation is the former — auth-gated but cross-user — because reputation is meant to inform a trading decision and would be useless if only visible to oneself.

Files that change: `backend/app/routers/admin.py`, `subastas.py`, `figuritas.py`, `usuarios.py`, `backend/app/repositories/usuario_repo.py` (add `es_admin`), `backend/app/core/config.py` (optionally accept an `ADMIN_USER_ID` env var instead of hardcoding which seeded user is admin).

## Why this approach

- **Router-level dependencies turn an opt-in safety check into the default.** The alternative — adding `Depends(get_current_user)` to each handler — is what's already in use everywhere *except* these four. The four holes prove that opt-in-per-handler is the wrong default; closing them by editing four handlers leaves the fifth one waiting.
- **`require_admin` belongs in the router, not the service.** Admins are an authorization concept, not a domain concept — `admin_service.obtener_estadisticas()` shouldn't care who's calling. Putting the check in the dependency keeps the boundary clean (see [ARCH-01](./ARCH-01-layer-leakage.md)).
- **The `usuario_id`-in-path antipattern is bigger than reputation.** The team should adopt a rule: protected endpoints derive the user from the token, not the URL. The only legitimate reason for a `{user_id}` path parameter is when the resource is *another* user (reputation, profile-by-id). Even then, **auth still applies** — `usuario_id` in the path is not authentication.
