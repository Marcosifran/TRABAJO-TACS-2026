# REST-01 — Verbs in URLs and ad-hoc state transitions

**Severity:** H  ·  **Area:** REST  ·  **Effort:** M

## Diagnosis

The API sits at **Richardson Level 2** for most endpoints (resources + HTTP verbs + status codes), with a handful of Level-1 leaks where the action is encoded in the URL path. The leaks are small in count but big in optics: they're the endpoints a reviewer (the *ayudante*) is most likely to point at first.

**1. `POST /subastas/{subasta_id}/ofertas/{oferta_id}/aceptar`** (`subastas.py:43`). This is the canonical "verb in URL" antipattern. Accepting an offer is a *state transition* on the offer (or on the auction, depending on how you model it). REST expresses state transitions with `PATCH` or `PUT` on the resource itself:

- The offer transitions from `pending` to `accepted` → `PATCH /subastas/{subasta_id}/ofertas/{oferta_id}` with body `{"estado": "aceptada"}`.
- Or, modelling it as a side-effect of finalizing the auction → `PATCH /subastas/{subasta_id}` with body `{"estado": "finalizada", "oferta_ganadora_id": ...}`.

The team has *already* used PATCH-on-state correctly for intercambios (`intercambios.py:55-66`: `PATCH /intercambios/{id}/estado` with `{"estado": "aceptado" | "rechazado"}`). Pick that pattern and copy it across.

**2. `POST /subastas/{subasta_id}/ofertar`** (`subastas.py:107`). "Ofertar" is a verb. The action is "create an offer in this auction's offers collection" — the natural REST URL is `POST /subastas/{subasta_id}/ofertas` (collection nested under the auction). The collection already exists on the GET side (`subastas.py:62-77`: `GET /subastas/{subasta_id}/ofertas`). Adding POST to the same URL closes the symmetry.

**3. `GET /publicaciones/mias`** (`publicaciones.py:39`). "Mías" is a possessive, not a resource. Two clean alternatives:
- Filter the existing collection: `GET /publicaciones/?owner=me` (or `?usuario_id=me` — the existing `GET /publicaciones/` already excludes the caller's own publications at `publicacion_service.py` via the `excluir_usuario_id` parameter, so the semantics are simply *inverting that flag*).
- Promote it under the user resource: `GET /usuarios/me/publicaciones`. `usuarios.py` already has a precedent at `usuarios.py:19` for "things owned by the authenticated user."

**4. The same endpoint exists at two URLs.** `obtener_sugerencias` is registered in `publicaciones.py:49-55` *and* in `usuarios.py:73-75`. Both call the same service function. One of them is dead routing — pick the more domain-correct path (`/usuarios/me/sugerencias` if framing it as a per-user view, or `/publicaciones/sugerencias` if framing it as a discovery filter) and delete the other. Duplicate routes are a load-bearing source of confusion: when a future bug needs fixing, half the team patches one route and not the other.

There's a separate, smaller observation: the endpoints that *are* RESTful use proper status codes — `POST → 201`, `DELETE → 204`, `PATCH → 200`. That's good and shouldn't be lost in the cleanup. See [REST-03](./REST-03-response-envelopes-status-codes.md) for the spots where the status code is missing or wrong.

## Evidence

- `backend/app/routers/subastas.py:42-59` — `POST /subastas/{id}/ofertas/{id}/aceptar`
- `backend/app/routers/subastas.py:106-133` — `POST /subastas/{id}/ofertar`
- `backend/app/routers/publicaciones.py:39-47` — `GET /publicaciones/mias`
- `backend/app/routers/publicaciones.py:49-55` — `GET /publicaciones/sugerencias`
- `backend/app/routers/usuarios.py:73-75` — duplicate `GET /usuarios/sugerencias`
- `backend/app/routers/intercambios.py:55-66` — **the right shape**, to copy from: `PATCH /intercambios/{id}/estado` with `{"estado": "aceptado"}`

## Recommendation

Mirror the `intercambios` pattern across `subastas`, fold the `/mias` and `/sugerencias` duplicates into proper resource URLs, and delete the dead duplicate.

```python
# backend/app/routers/subastas.py
@router.patch(
    "/{subasta_id}/ofertas/{oferta_id}",
    response_model=OfertaResponse,
    responses={
        200: {"description": "Oferta actualizada (aceptada o rechazada)"},
        403: {"description": "Solo el creador de la subasta puede aceptar ofertas"},
        404: {"description": "Subasta u oferta no encontrada"},
    },
)
def responder_oferta(
    subasta_id: int,
    oferta_id: int,
    decision: OfertaDecision,         # {"estado": "aceptada" | "rechazada"}
    usuario: dict = Depends(get_current_user),
):
    return subasta_service.responder_oferta(
        subasta_id, oferta_id, decision.estado, usuario["id"]
    )

@router.post(
    "/{subasta_id}/ofertas",
    response_model=OfertaResponse,
    status_code=201,
)
def crear_oferta(
    subasta_id: int,
    oferta: OfertaCreate,
    usuario: dict = Depends(get_current_user),
):
    return subasta_service.ofertar(subasta_id, oferta, usuario["id"])
```

For `/publicaciones/mias`, the recommendation is to **delete the route** and use the existing collection with an explicit filter:

```python
# backend/app/routers/publicaciones.py
@router.get("/", response_model=list[PublicacionResponse])
def listar_publicaciones(
    # ...existing filters...
    incluir_propias: bool = Query(default=False),
    usuario: dict = Depends(get_current_user),
):
    return publicacion_service.listar_publicaciones(
        # ...
        excluir_usuario_id=None if incluir_propias else usuario["id"],
    )
```

`/publicaciones/?incluir_propias=true` replaces `/publicaciones/mias`. Frontend swap is a one-line change in `frontend/src/api/publicaciones.js`.

For `obtener_sugerencias`, **delete the `/usuarios/sugerencias` copy** at `usuarios.py:67-75`. Keep the one in `publicaciones.py` because it's where the related collection lives. Update the frontend accordingly.

Files that change: `backend/app/routers/subastas.py` (rewrite two routes), `backend/app/routers/publicaciones.py` (one route deleted, one filter added), `backend/app/routers/usuarios.py` (one route deleted), `backend/app/services/subasta_service.py` (rename `aceptar_oferta` → `responder_oferta` if you want the API to support rejection too — currently it only accepts), `backend/app/schemas/oferta.py` (add `OfertaDecision`), and the corresponding frontend `api/` calls.

## Why this approach

- **Consistency with `intercambios` is free design re-use.** The team has already paid the cost of getting one state-transition right. The PATCH-on-state shape generalizes to any future "respond to X" action (calificaciones could move to a similar shape if needed). Copying an existing internal pattern beats inventing a new one.
- **`/mias` as a filter is honest about the model.** A "publicación mía" is not a different *kind* of resource — it's the same resource with a different filter. Two routes implying two kinds is a Level-1 leak that costs documentation effort forever. One route + a flag is what the user actually wants.
- **The dead duplicate is the cheapest fix and the most pedagogical.** It teaches the team to grep the routers list before adding a route — a discipline that will scale. Deleting one of the two `obtener_sugerencias` is ~3 lines and immediately removes a source of "wait, which URL?" in code review.
