# REST-04 — CORS wildcard with credentials; no pagination or versioning strategy

**Severity:** M  ·  **Area:** REST / Infra  ·  **Effort:** S

## Diagnosis

Three related but independent gaps in the HTTP infrastructure: CORS is misconfigured in a way that browsers will silently reject, every collection endpoint is unbounded, and versioning consists of a single `/api/v1` prefix with no plan for what `/v2` would mean.

**1. CORS is invalid.** `main.py:10-15` registers the CORS middleware as:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

The W3C CORS spec **forbids** the combination `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true`. Browsers will refuse to send cookies or `Authorization` headers under this config. The backend doesn't crash and the auth token *happens* to be in a custom `X-User-Token` header rather than a cookie, so the frontend works — but the configuration is wrong-shaped and will break the day someone tries to send a cookie or expects `credentials: 'include'` to work.

The right shape depends on what the team actually wants:
- **Dev:** specific origins (`http://localhost:5173`) with `allow_credentials=True`. The frontend is on the same machine; you don't need the wildcard.
- **Prod:** the deployed frontend origin (a list, not `["*"]`) with `allow_credentials=True` only if the API actually uses credentials.
- **Public read-only API (not this case):** `allow_origins=["*"]` with `allow_credentials=False`.

**2. No pagination on collection endpoints.** Every `GET /<resource>/` returns the full table. Today with two seeded users and a handful of figuritas that's irrelevant. The day a load test hits 10,000 rows (the TP non-functional requirements explicitly mention load testing with Vegeta/Wrk), the test fails by timeout, not by a 4xx that's debuggable. The endpoints affected:

- `album.py:17-29` — `GET /album/`
- `publicaciones.py:21-37` — `GET /publicaciones/`
- `figuritas.py:10-26` — `GET /figuritas/`
- `subastas.py:9-19` — `GET /subastas/`
- `intercambios.py:38-52` — `GET /intercambios/`
- `usuarios.py:50-62` — `GET /usuarios/faltantes`
- `subastas.py:62-77` — `GET /subastas/{id}/ofertas`

Pagination doesn't have to be cursor-based; for an in-memory store, simple `limit` and `offset` query parameters with sensible defaults are enough. The point is **bound the query**, not invent the perfect scheme today.

**3. Versioning is shallow.** `main.py:19-24` mounts every router at `/api/v1`. That's fine as a default, but there is no policy for what triggers a `v2`. A breaking change to `IntercambioResponse` today either:
- Goes out under `v1` and quietly breaks every client, or
- Forces a stand-up of `v2/` routers that share 90% of the code with `v1/`.

The team doesn't need a *full* versioning policy yet — Entrega 3 will reshape responses anyway — but they should write down the rule: "we only `v2` when we break a Pydantic response model in a way that can't be made backward-compatible via additive fields." That rule, combined with `response_model_exclude_unset=True` on routes, lets the API add fields safely for as long as the schema permits. Header-based versioning (`Accept: application/vnd.figuswap.v1+json`) is *not* recommended here — it's heavier than the team needs.

A small adjacent miss: there are no cache headers on the read-mostly endpoints. `figuritas.py` returning the same dataset for the same query parameters is a textbook ETag candidate. Not urgent, but worth flagging.

## Evidence

- `backend/app/main.py:10-15` — invalid `allow_origins=["*"] + allow_credentials=True`
- `backend/app/main.py:18-24` — only `/api/v1` prefix, no versioning policy
- `backend/app/routers/album.py:17-29` — unbounded `GET /album/`
- `backend/app/routers/publicaciones.py:21-37` — unbounded `GET /publicaciones/`
- `backend/app/routers/figuritas.py:10-26` — unbounded `GET /figuritas/`
- `backend/app/routers/subastas.py:9-19` — unbounded `GET /subastas/`
- `backend/app/routers/intercambios.py:38-52` — unbounded `GET /intercambios/`
- TP spec — "La aplicación debe soportar un load test, se utilizará alguna tool como Vegeta, Wrk, etc." (no bounded queries makes this fail)

## Recommendation

### CORS

Move the allowed origins into config and stop using the wildcard with credentials:

```python
# backend/app/core/config.py
class Settings(BaseSettings):
    # ...existing fields...
    cors_origins: list[str] = ["http://localhost:5173"]

# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Read `CORS_ORIGINS` (a comma-separated string) from `.env` if you want to override per-environment; pydantic-settings handles that with a `Field(default_factory=...)` or a JSON-encoded value.

### Pagination

Add a shared dependency:

```python
# backend/app/dependencies.py
from fastapi import Query

def page_params(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    return {"limit": limit, "offset": offset}

# backend/app/routers/publicaciones.py
@router.get("/", response_model=list[PublicacionResponse])
def listar_publicaciones(
    # ...existing filters...
    page: dict = Depends(page_params),
    usuario: dict = Depends(get_current_user),
):
    return publicacion_service.listar_publicaciones(
        # ...
        limit=page["limit"], offset=page["offset"],
    )
```

The service passes `limit`/`offset` to the repo; the repo applies `_db[offset:offset+limit]` after filtering. Bound `le=200` so a misbehaving client can't ask for 100k rows. This is enough for the load test the TP asks for and is forward-compatible with cursor pagination later.

### Versioning

Write a one-line rule in CLAUDE.md (which already exists):

> Versioning policy: `/api/v1` stays additive-only. Bumping to `/api/v2` requires breaking a response model in a way that can't be expressed as an optional new field. We do not version requests via Accept header.

That's the whole thing. The cost of having the rule is one line; the cost of not having it is the next argument in a code review.

Files that change: `backend/app/main.py` (CORS), `backend/app/core/config.py` (cors_origins), `.env.example` (document CORS_ORIGINS), `backend/app/dependencies.py` (page_params helper), every `routers/*.py` that owns a collection GET (add the `Depends(page_params)`), every `services/*.py` collection function (accept `limit`/`offset`), every `repositories/*.py` collection function (apply the slice), and `CLAUDE.md` (versioning note).

## Why this approach

- **A wildcard CORS with credentials is the kind of thing a reviewer notices immediately.** The fix is small, the message it sends about the team's understanding is large. Hardcoding `http://localhost:5173` for dev is fine — the point is "we know which origins we allow."
- **`limit`/`offset` is the right default before there's data.** Cursor pagination is better when you have stable ordering and a long tail; that's an Entrega-3 conversation. For now, get the *bound* in, with a hard ceiling, and the load test passes by design.
- **A one-line versioning policy is cheaper than the alternative.** The team won't read a long doc, and a long doc isn't justified — `v2` won't happen until something breaks. The rule's job is to make the team stop and notice when a change would force a `v2`, so they can choose to keep it backward-compatible instead.
