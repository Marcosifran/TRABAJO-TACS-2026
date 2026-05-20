# ARCH-01 — Layer leakage: routers call repos, services raise `HTTPException`

**Severity:** H  ·  **Area:** Architecture  ·  **Effort:** M

## Diagnosis

CLAUDE.md describes the intended four-layer split: **router → service → repository → schema**. The split is real and mostly honored — services exist, they coordinate repos, repos own state. But two leaks meet in the middle and erase the boundary in practice:

**1. Routers reach into repositories directly.** In `intercambios.py:22-35`, the create handler calls `intercambio_service.validar_intercambio(...)` and then *itself* calls `intercambio_repo.crear_intercambio(...)`. The service validates, the router persists. There is no single function that says "propose this intercambio"; the logic is sprawled across two layers. Worse, in `intercambios.py:45-52`, `listar_intercambios` calls `intercambio_repo.listar_intercambios_por_usuario(...)` *and* `calificacion_repo.buscar_por_intercambio_y_calificador(...)` to enrich each row with a `ya_calificado` flag. That enrichment is business logic — it joins two domains — and it lives in the HTTP handler. A second developer adding a similar enrichment will copy the pattern into another router, and the service layer becomes optional.

**2. Services raise `HTTPException`.** `intercambio_service.py` raises `HTTPException` 14 times (`:10, :13, :19, :28, :34, :68, :76, :96, :110, :115, :254, :257, :263, :274`). A pure business-logic function should not know that HTTP exists — it expresses domain failures (a self-trade, a missing destination, an already-responded proposal) and *the boundary* decides what HTTP status those map to. Today, `intercambio_service` and `intercambios.py` are inseparable: you cannot reuse the service from a CLI, a background job, or a unit test without dragging FastAPI in.

The same code reveals that the team has **already discovered the right pattern** — but only in one corner. `subasta_service.py` raises `ValueError` for "not found / invalid state" (`:31, :34, :37, :41, :55, ...`) and `PermissionError` for "not yours" (`:148, :164`), and `subastas.py` translates them at the boundary. That's the correct shape. Unfortunately the translation is done by inspecting the *message*:

```python
# subastas.py:57-59
detail = str(e)
if "no encontrada" in detail.lower() or "no existe" in detail.lower():
    raise HTTPException(status_code=404, detail=detail)
raise HTTPException(status_code=400, detail=detail)
```

Substring-matching on an error string is the same bug pattern as parsing exceptions from `printf`. It moves status-code logic into the error message, which means any future translator (i18n, Spanish vs English) silently mis-maps statuses. See [ERR-01](./ERR-01-error-handling.md) for the full treatment; the point here is that **the leak has both shapes** — services that raise `HTTPException` (over-coupled), and services that raise `ValueError` then are decoded by string-matching (under-typed). Neither is the right answer.

Finally: `intercambio_service.py:149-233` (`realizar_intercambio_aceptado`) is an 85-line procedure that mutates two albums, two publications lists, and the faltantes list with two near-symmetrical loops. It is the highest-leverage refactor target in the service layer — not because it's wrong, but because it cannot be partially tested. Anything that fails halfway leaves the in-memory store in a hybrid state. Splitting it into `_transferir_figurita(...)` would make each transfer testable in isolation and would make the eventual Entrega-3 DB transaction visible (one obvious `with session.begin():` around the loop).

## Evidence

- `backend/app/routers/intercambios.py:6` — router imports `intercambio_repo, calificacion_repo` directly
- `backend/app/routers/intercambios.py:29-33` — router persists via `intercambio_repo.crear_intercambio(...)`
- `backend/app/routers/intercambios.py:46-51` — router joins intercambios with calificaciones in-handler
- `backend/app/services/intercambio_service.py:10,13,19,28,34,68,76,96,110,115,254,257,263,274` — 14 `HTTPException` raises inside a pure-business service
- `backend/app/services/subasta_service.py:31,34,37,41,55,82,84,87,92,95,101,105,146,148,151,161,164,166,170,174,182` — `ValueError`/`PermissionError` raises (the other shape of the same problem)
- `backend/app/routers/subastas.py:57-59, 100-103, 128-131` — substring-matching on error messages to choose status code
- `backend/app/services/intercambio_service.py:149-233` — 85-line god procedure with no atomicity

## Recommendation

Two moves, in order. First, **stop persisting from routers**. Second, **introduce a small domain-exception hierarchy and centralize the translation** (see [ERR-01](./ERR-01-error-handling.md) for the full exception design — here we just show how a service should *return*).

### Push the create logic into the service

```python
# backend/app/services/intercambio_service.py
def proponer_intercambio(
    intercambio: IntercambioCreate, propuesto_por: int
) -> dict:
    validar_intercambio(intercambio, usuario_id=propuesto_por)
    return intercambio_repo.crear_intercambio(
        intercambio,
        propuesto_por=propuesto_por,
        solicitado_a=intercambio.solicitado_a_id,
    )

# backend/app/routers/intercambios.py
@router.post("/", status_code=201)
def proponer_intercambio(
    intercambio: IntercambioCreate,
    usuario: dict = Depends(get_current_user),
):
    return intercambio_service.proponer_intercambio(intercambio, usuario["id"])
```

The router becomes "parse + delegate + return." That is the entire job of an HTTP handler. The same shape applies to `listar_intercambios`: a service method `listar_intercambios_de(usuario_id)` does the join with calificaciones and returns the enriched list.

### Replace `HTTPException` raises with domain exceptions

```python
# backend/app/domain/errors.py  (new file)
class DomainError(Exception): ...
class NotFound(DomainError): ...
class Forbidden(DomainError): ...
class Conflict(DomainError): ...
class Invalid(DomainError): ...

# in intercambio_service.py
from app.domain.errors import Invalid, Forbidden, NotFound

def validar_usuario_destino(intercambio, usuario_id):
    if intercambio.solicitado_a_id == usuario_id:
        raise Invalid("No podés proponerte un intercambio a vos mismo")
    if not usuario_repo.get_by_id(intercambio.solicitado_a_id):
        raise NotFound("El usuario destinatario no existe")
```

The HTTP-status translation then lives in a single global exception handler — see [ERR-01](./ERR-01-error-handling.md) for the handler. The router goes back to being one line.

## Why this approach

- **Routers as facades let you swap protocols.** The same `intercambio_service.proponer_intercambio(...)` is callable from a future Telegram bot (the TP bonus mentions one) or a background reconciliation job. Today, both would have to fake an `HTTPException` catch.
- **String-matching on error messages is technical debt that compounds.** A second translator in another router (or a third one when i18n shows up) will fork the regex. Domain exceptions cost about 20 lines once and replace the regex everywhere.
- **A god function that mutates two stores is a transaction boundary waiting to be discovered.** Splitting `realizar_intercambio_aceptado` *before* Entrega 3 is much cheaper than after, because the in-memory version has no rollback to design around. The Entrega-3 PR can then literally wrap the same calls in a DB transaction.
