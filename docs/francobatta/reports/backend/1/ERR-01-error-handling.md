# ERR-01 — Inconsistent error idiom; routers do substring-matching

**Severity:** H  ·  **Area:** Errors / Architecture  ·  **Effort:** M

## Diagnosis

The backend has **two different error idioms** in use, and one of the translation paths between them relies on string matching. The result is that error handling is local — every router file reinvents how to translate domain failures into HTTP — and there is no shared error contract for the frontend to lean on.

**Idiom A — Service raises `HTTPException`.** Used in `intercambio_service.py` (14 raises), `calificacion_service.py`, `publicacion_service.py:9-16`, `usuario_service.py`, and the auth dependency itself. The service knows the HTTP status code. The router calls the service and returns its result. Translation is implicit.

**Idiom B — Service raises domain-ish exceptions, router translates.** Used in `subasta_service.py` (`ValueError` for "not found / bad state", `PermissionError` for "not yours"). The router decodes them:

```python
# subastas.py:55-59
except PermissionError as e:
    raise HTTPException(status_code=403, detail=str(e))
except ValueError as e:
    detail = str(e)
    if "no encontrada" in detail.lower() or "no existe" in detail.lower():
        raise HTTPException(status_code=404, detail=detail)
    raise HTTPException(status_code=400, detail=detail)
```

This idiom is repeated in `subastas.py:96-103` (`cancelar_oferta`) and `subastas.py:128-131` (`ofertar_en_subasta`), each with a slightly different substring list. The substring `"inexistente"` shows up in `ofertar_en_subasta` but not in `cancelar_oferta`; if `subasta_service.py:55` ever changes its message from `"Subasta inexistente"` to `"Subasta no encontrada"`, only one of the three routers translates it correctly.

Both idioms have the same shape problem: the status-code logic is duplicated across the codebase. In Idiom A it's duplicated as "any service that raises this same condition has to remember to use the same status code." In Idiom B it's duplicated as "any router that catches this same error has to remember the substring rule."

A third symptom: **there is no global exception handler.** `main.py:1-29` registers the routers and CORS, nothing else. That means:
- Any unexpected exception leaks a 500 with `{"detail": "Internal Server Error"}` and the FastAPI default body.
- The error body shape is not contractually stable. `subastas.py:39` returns `{"detail": str(e)}` (FastAPI's default for HTTPException), but `publicaciones.py:67-69` does the same shape *manually*. A frontend reading `body.detail` is parsing two different conventions that happen to coincide today.

A fourth observation, smaller but worth fixing: **Pydantic validation duplicates.** `publicacion_service.py:15-16` checks `publicacion.cantidad_disponible > figurita["cantidad"]` and raises 400. That's not duplication of a Pydantic constraint (it depends on a cross-record value), so this specific check is fine. But `intercambio_service.py:9-13` checks "list not empty" and "no repeats" — the empty check could be expressed in the schema as `figuritas_ofrecidas_numero: list[int] = Field(..., min_length=1)`, which would let Pydantic return 422 with field-level detail rather than the service returning 400 with a string. See [PY-01](./PY-01-magic-strings-and-validation.md) for the broader duplication theme.

Status-code discipline is mostly fine but has spots worth fixing along with this refactor:
- `intercambios.py:67-74` — `responder_intercambio` returns 404 when the issue is "you're not the receiver" — `intercambio_service.responder_intercambio` already raises 403 at line 257; the router's secondary 404 fallback at line 74 is unreachable but confusing.
- `usuarios.py:43` — 409 ("duplicate") is raised on *any* `ValueError` from `registrar_faltante`, regardless of cause. That's the kind of correlation that ages badly.

## Evidence

- `backend/app/services/intercambio_service.py:10,13,19,28,34,68,76,96,110,115,254,257,263,274` — Idiom A (HTTPException-in-service)
- `backend/app/services/subasta_service.py:31,34,37,41,55,82,84,87,92,95,101,105,146,148,151,161,164,166,170,174,182` — Idiom B (ValueError/PermissionError-in-service)
- `backend/app/routers/subastas.py:55-59, 97-103, 128-131` — substring-matching translation
- `backend/app/main.py:1-29` — no `@app.exception_handler(...)` registered
- `backend/app/services/publicacion_service.py:9-16` — Idiom A with 404/403/409/400
- `backend/app/routers/usuarios.py:41-43` — coarse 409 mapping in router
- `backend/app/dependencies.py:9-10` — auth 401 has no `WWW-Authenticate` header (see [SEC-01](./SEC-01-token-model.md))

## Recommendation

A small domain-exception hierarchy plus a single global handler that maps each exception class to a status code. The translation moves out of the routers entirely; services stop knowing HTTP exists.

```python
# backend/app/domain/errors.py  (new file)
class DomainError(Exception):
    """Base for all domain-level failures."""

class NotFound(DomainError): ...
class Forbidden(DomainError): ...
class Conflict(DomainError): ...
class Invalid(DomainError):
    """400-level: caller's input is malformed in a way Pydantic can't express."""

# backend/app/main.py
from fastapi import Request
from fastapi.responses import JSONResponse
from app.domain.errors import DomainError, NotFound, Forbidden, Conflict, Invalid

_STATUS = {NotFound: 404, Forbidden: 403, Conflict: 409, Invalid: 400}

@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(
        status_code=_STATUS.get(type(exc), 500),
        content={
            "type": exc.__class__.__name__.lower(),
            "title": exc.__class__.__name__,
            "detail": str(exc),
            "status": _STATUS.get(type(exc), 500),
        },
    )
```

This shape is RFC 7807-compatible without adopting the full spec. The `type`/`title`/`detail`/`status` quartet is a stable contract the frontend can rely on — and is forward-compatible if you later add `instance` or extension fields.

Services then look like:

```python
# backend/app/services/intercambio_service.py
from app.domain.errors import Invalid, Forbidden, NotFound

def validar_usuario_destino(intercambio, usuario_id):
    if intercambio.solicitado_a_id == usuario_id:
        raise Invalid("No podés proponerte un intercambio a vos mismo")
    if not usuario_repo.get_by_id(intercambio.solicitado_a_id):
        raise NotFound("El usuario destinatario no existe")
```

And routers go back to one line:

```python
# subastas.py
@router.post("/{subasta_id}/ofertas", status_code=201)
def crear_oferta(
    subasta_id: int,
    oferta: OfertaCreate,
    usuario: dict = Depends(get_current_user),
):
    return subasta_service.ofertar(subasta_id, oferta, usuario["id"])
```

Every `try/except` block in `subastas.py` disappears.

Files that change: new `backend/app/domain/errors.py`; `backend/app/main.py` gets the handler; every `services/*.py` swaps `HTTPException` and `ValueError`/`PermissionError` for the domain exceptions; every router that has `try/except` blocks deletes them. The `routers/intercambios.py:73-74` dead fallback gets removed in the process.

## Why this approach

- **One stable error contract beats "look at the route, decide the rule."** Today the frontend has to know that `subastas.py` returns 404 with `"detail"` containing the word `"no encontrada"`, but `intercambios.py` returns 404 with whatever the service decided. Tomorrow a third route invents a fourth shape. The handler-based fix is one place that produces one shape forever.
- **Services should not import FastAPI.** Today `intercambio_service.py:1` does `from fastapi import HTTPException`. After the fix it doesn't. The mental rule is "if a file imports FastAPI, it sits at the boundary." That rule survives Entrega 3 (a Celery worker can call the service), a future Telegram bot (TP bonus), and unit tests (no `TestClient` needed for a service-level test).
- **Substring-matching is a special case of "encoding logic in messages."** The fix removes the temptation. Once exceptions are typed, no one ever reaches for `if "x" in str(e)` again — they just catch the type.
