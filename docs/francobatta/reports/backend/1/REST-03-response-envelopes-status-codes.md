# REST-03 — Inconsistent response envelopes & implicit status codes

**Severity:** M  ·  **Area:** REST  ·  **Effort:** S

## Diagnosis

The API mixes three different response shapes on success, and several endpoints declare HTTP status codes implicitly (or wrongly). Neither problem is dangerous; both are the kind of "small inconsistency" that becomes a constant tax on the frontend.

**1. Three success-envelope shapes coexist.** A frontend reading these responses has to learn three conventions:

- **Raw resource** — `album.py:8-15` `POST /album/` returns the `FiguritaAlbumResponse` directly. This is the right shape. `intercambios.py:22-35` and `publicaciones.py:12-19` also use it.
- **Wrapped with a `mensaje`** — `figuritas.py:39-44`: `{"mensaje": "Figurita a intercambiar publicada", "data": nueva}`. Also `subastas.py:32-40`: `{"mensaje": "Subasta creada exitosamente", "subasta": ...}`. The `mensaje` is human-readable Spanish that the frontend either ignores (in which case it's noise) or displays (in which case the *server* is choosing UI copy, which is the wrong layer).
- **Wrapped with the resource owner's id** — `usuarios.py:24` returns `{"usuario_id": ..., "figuritas": ...}`. Same shape at `usuarios.py:62, 75, 99, 114`. The `usuario_id` is *already known* to the caller (it's their own token). Including it duplicates information without adding any.

There's a fourth, smaller version: `figuritas.py:26` returns `{"figuritasDisponibles": resultado}` (camelCase key in an otherwise snake_case codebase). Same anti-pattern as the others — wrapping a list in an object so the response is "extensible" — except that JSON arrays are *already* extensible (the client just keys into the array vs. object identically in most parsers, but the server has chosen to make the parsing path different per route).

The right default is **return the resource (or list of resources) directly**. If you need to communicate metadata (pagination cursor, total count), use a stable envelope name once — `{"items": [...], "next_cursor": ...}` — and apply it consistently on *all* collections.

**2. Several status codes are implicit, and one is wrong.**

- `figuritas.py:47-62` declares `DELETE /figuritas/{id}` with `responses={200: ...}` and returns `{"mensaje": "Figurita eliminada"}`. The default `status_code` is 200, but DELETE should be 204 (No Content). Compare with `album.py:32` and `publicaciones.py:57` which correctly use `status_code=204` on their DELETEs.
- Almost every GET endpoint omits `status_code=200`. FastAPI defaults to 200, so the runtime behavior is correct, but the OpenAPI docs lose the explicit declaration that helps consumers. The pattern is inconsistent — `subastas.py:9-13` declares `responses={200: ...}` (descriptive) without `status_code=200`. The combination is harmless, but a reader has to verify each route.
- `intercambios.py:55-65` correctly uses `response_model=IntercambioResponse` and the implicit 200 — good. The OpenAPI schema is therefore correct here.

**3. Error responses follow the FastAPI default `{"detail": "..."}` shape, but the `mensaje`-wrapped successes mean the frontend has to parse two completely different bodies depending on status.** This crosses over with [ERR-01](./ERR-01-error-handling.md), which proposes a stable error envelope. Together, success-resource-directly + a single error envelope give the frontend exactly two shapes to learn.

## Evidence

- `backend/app/routers/figuritas.py:39-44` — POST returns `{"mensaje": "...", "data": ...}`
- `backend/app/routers/figuritas.py:47-62` — DELETE returns 200 (should be 204)
- `backend/app/routers/figuritas.py:26` — `{"figuritasDisponibles": resultado}` (camelCase + list-in-object)
- `backend/app/routers/subastas.py:40` — `{"mensaje": "...", "subasta": ...}`
- `backend/app/routers/subastas.py:52` — `{"mensaje": "Oferta aceptada", "resultado": ...}`
- `backend/app/routers/subastas.py:77` — `{"ofertas": ofertas}`
- `backend/app/routers/usuarios.py:24, 46, 62, 75, 99, 114` — `{"usuario_id": ..., ...}` envelope
- `backend/app/routers/album.py:32` — **the right shape**: `DELETE` with `status_code=204` and `usuarios.py` lacks this
- `backend/app/routers/publicaciones.py:57` — also the right shape

## Recommendation

Adopt two rules and apply them across the routers.

**Rule 1 — return the resource directly; envelopes only for paginated collections.**

```python
# Bad (current figuritas.py:39-44)
@router.post("/", status_code=201)
def publicar_figurita(figu: FiguritaCreate, usuario: dict = Depends(get_current_user)):
    nueva = figurita_service.publicar(figu, usuario["id"])
    return {"mensaje": "Figurita a intercambiar publicada", "data": nueva}

# Good
@router.post("/", response_model=FiguritaResponse, status_code=201)
def publicar_figurita(figu: FiguritaCreate, usuario: dict = Depends(get_current_user)):
    return figurita_service.publicar(figu, usuario["id"])
```

The `mensaje` was redundant — the 201 status code is the "it worked" signal. The `data` wrapping was equally redundant — Pydantic plus `response_model` is the contract.

For collections that might paginate (see [REST-04](./REST-04-cors-versioning-pagination.md)), if envelopes are needed, agree on **one** shape:

```python
class Page[T](BaseModel):
    items: list[T]
    next_cursor: str | None = None
```

…and use it everywhere a collection might page, never on single-resource responses.

**Rule 2 — declare status codes explicitly, and use 204 for "no representation to return".**

```python
# figuritas.py — fix DELETE
@router.delete(
    "/{figurita_id}",
    status_code=204,
    responses={
        204: {"description": "Figurita eliminada"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "No tenés permiso para eliminar esta figurita"},
        404: {"description": "Figurita no encontrada"},
    },
)
def eliminar_figurita(figurita_id: int, usuario: dict = Depends(get_current_user)):
    resultado = figurita_service.eliminar(figurita_id, usuario["id"])
    if resultado is False:
        raise HTTPException(status_code=404, detail="Figurita no encontrada")
    if resultado is None:
        raise HTTPException(status_code=403, detail="No tenés permiso para eliminar esta figurita")
    # No return body for 204
```

For every GET endpoint, add an explicit `status_code=200` *only if* you also pass `responses={...}`; otherwise the default is fine and adding it is noise. The rule the team should adopt is: "if your route documents `responses=`, document `status_code=` too — and keep them in sync."

Files that change: `backend/app/routers/figuritas.py` (DELETE → 204; POST/GET return raw), `subastas.py` (drop `mensaje`/`subasta`/`resultado` envelopes), `usuarios.py` (drop `{usuario_id, ...}` envelopes — six endpoints), and corresponding `frontend/src/api/*.js` callers (they currently parse the envelopes; they need to parse the raw resource instead).

## Why this approach

- **The status code is the message.** 201/204/200 already carry the success semantics. Adding `mensaje: "..."` next to them is double-bookkeeping and pulls UI copy into the API. The frontend should choose the wording (and translate it).
- **`response_model` + a Pydantic schema is a stronger contract than a hand-rolled envelope.** It populates OpenAPI, drives auto-generated client types (if the team wants `openapi-typescript`), and validates outgoing shape in dev. The `{"mensaje": ..., "data": ...}` envelope disables `response_model` because the actual response shape no longer matches.
- **204 for DELETE is the small thing that signals "we read the HTTP spec".** It's a 30-second fix on one route. The reason to do it is not the bytes saved on the wire; it's the consistency with `album.py:32` and `publicaciones.py:57`, which are already correct. Three matching DELETEs is a learnable pattern; two-and-a-half is a wart.
