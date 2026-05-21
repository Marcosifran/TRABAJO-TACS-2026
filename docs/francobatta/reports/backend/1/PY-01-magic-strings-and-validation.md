# PY-01 — Magic strings for domain states; Pydantic validation duplicated

**Severity:** M  ·  **Area:** Pythonic / Errors  ·  **Effort:** S

## Diagnosis

Three small idiomatic concerns that compound: the codebase already uses Pydantic `Enum`s for some domain states (`TipoIntercambio`, `EstadoRespuestaIntercambio`) but uses raw strings for others (`"pendiente"`, `"activa"`, `"finalizada"`); some constraints are duplicated between Pydantic `Field` declarations and explicit if-checks in services; and a handful of micro-conventions drift across files (dead imports, import style, mutating dicts mid-flow, defensive `.get()` calls). None of these is bad on its own, but they're the kind of things a senior reviewer reads as "the team hasn't sat down and aligned on conventions yet."

**1. Magic strings for `estado` fields, despite enums existing elsewhere.**

The team has `TipoIntercambio(str, Enum)` in `figurita.py:8-10` and `publicacion_sch.py:5-8`, and `EstadoRespuestaIntercambio(str, Enum)` in `intercambio_sch.py:4-6`. So the muscle is there. But `intercambio_repo.py:20` stores the literal `"pendiente"`:

```python
"estado": "pendiente",
```

…and `intercambio_service.py:262` reads it the same way:

```python
if intercambio["estado"] != "pendiente":
    raise HTTPException(status_code=400, detail="El intercambio ya fue respondido")
```

And `admin_service.py:10`:

```python
estados = {"pendiente": 0, "aceptado": 0, "rechazado": 0}
```

And `test_proponer_intercambio.py:78`: `assert data["estado"] == "pendiente"`.

`"pendiente"` is now hardcoded in four places. A typo (`"pendinete"`) compiles, runs, fails silently, and passes every test that doesn't read the failure mode. The same shape repeats for subastas: `subasta_repo.py:6, 19, 24-25` use `"activa"` and `"inactiva"` as strings; `subasta_service.py:203` writes `"finalizada"`. No `EstadoSubasta` enum exists.

**2. Pydantic constraints duplicated by hand.**

`intercambio_service.py:9-13`:

```python
if not intercambio.figuritas_ofrecidas_numero:
    raise HTTPException(status_code=400, detail="Debés ofrecer al menos una figurita")
if len(intercambio.figuritas_ofrecidas_numero) != len(set(intercambio.figuritas_ofrecidas_numero)):
    raise HTTPException(status_code=400, detail="No podés repetir figuritas en la oferta")
```

Both checks could be expressed in the schema:

```python
# intercambio_sch.py
figuritas_ofrecidas_numero: list[int] = Field(..., min_length=1)
```

…and the duplicate-detection via a `@field_validator`. Pydantic would return 422 with a per-field error, which is more useful to clients than the service-side 400 with a string. Move the validation **up** to where the data enters the system. This is also a small win for [ERR-01](./ERR-01-error-handling.md) — fewer service-side `HTTPException` raises is fewer reasons for a service to import FastAPI.

`publicacion_service.py:15-16` is a *real* cross-record check (`publicacion.cantidad_disponible > figurita["cantidad"]` depends on data outside the request) — that one belongs in the service, not the schema. The team should make the distinction explicit: **schema validates what the request can self-describe; service validates anything that depends on stored state.**

**3. Drift in micro-conventions.**

- **Dead import.** `usuarios.py:7` imports `usuario_repo` but never uses it. `ruff` would catch this immediately ([TEST-01](./TEST-01-tests-and-ci.md)).
- **Local import inside a function.** `intercambio_service.py:154` imports `FiguritaAlbumCreate` inside the function body. This is sometimes a circular-import workaround, but here it's just inconsistent — the same import works at module level. (Verify circulars first; if the cycle is real, the right fix is the domain model in [ARCH-03](./ARCH-03-anemic-repos-no-domain-model.md).)
- **`.get(default)` on dicts that should have the key.** `admin_service.py:13, 18` — `i.get("estado", "pendiente")`, `p.get("equipo", "Desconocido")`. These are defensive reads against the "anemic dict" shape that [ARCH-03](./ARCH-03-anemic-repos-no-domain-model.md) recommends replacing. With a typed model the `.get(default)` disappears.
- **Mutating storage by reference.** `subasta_service.py:185-188, 195-196` mutate a dict that came from the repo and then call `album_repo.update(...)`. The dict identity is the one in `_db`; the second call is redundant *and* the first call (the mutation) is the kind of thing that's invisible if you read the service in isolation. Discussed in [ARCH-03](./ARCH-03-anemic-repos-no-domain-model.md); flagged again here as a Python smell.
- **Datetime is timezone-aware — good.** `subasta_service.py:12` and `subasta_repo.py:6,19,25` use `dt.datetime.now(dt.timezone.utc)`. Keep this discipline — it's something the team got right and shouldn't lose in a refactor.
- **Mutable default arguments — none found.** Good.

## Evidence

- `backend/app/repositories/intercambio_repo.py:20` — `"estado": "pendiente"`
- `backend/app/services/intercambio_service.py:262` — `intercambio["estado"] != "pendiente"`
- `backend/app/services/admin_service.py:10` — `{"pendiente": 0, "aceptado": 0, "rechazado": 0}`
- `backend/tests/integration/test_proponer_intercambio.py:78` — `assert data["estado"] == "pendiente"`
- `backend/app/repositories/subasta_repo.py:6, 19, 24-25` — `"activa"`, `"inactiva"` literals
- `backend/app/services/subasta_service.py:203` — `subasta["estado"] = "finalizada"`
- `backend/app/services/intercambio_service.py:9-13` — duplicate-of-Pydantic empty-list check
- `backend/app/routers/usuarios.py:7` — `from app.repositories import usuario_repo` (unused)
- `backend/app/services/intercambio_service.py:154` — local import inside function body
- `backend/app/services/admin_service.py:13, 18` — defensive `.get(default)` on dicts the code owns
- `backend/app/services/subasta_service.py:12` — `dt.datetime.now(dt.timezone.utc)` (positive: keep this)

## Recommendation

Introduce two enums, push two constraints into the schema, and add `ruff` to CI to mop up the rest.

### Define the missing enums

```python
# backend/app/schemas/intercambio.py   (after rename, see ARCH-04)
from enum import Enum

class EstadoIntercambio(str, Enum):
    PENDIENTE = "pendiente"
    ACEPTADO = "aceptado"
    RECHAZADO = "rechazado"

# backend/app/schemas/subasta.py
class EstadoSubasta(str, Enum):
    ACTIVA = "activa"
    INACTIVA = "inactiva"
    FINALIZADA = "finalizada"
```

Use them everywhere:

```python
# intercambio_repo.py:20
"estado": EstadoIntercambio.PENDIENTE.value,

# intercambio_service.py:262
if intercambio["estado"] != EstadoIntercambio.PENDIENTE.value:
    raise Invalid("El intercambio ya fue respondido")          # see ERR-01

# admin_service.py:10
estados = {e.value: 0 for e in EstadoIntercambio}
```

If [ARCH-03](./ARCH-03-anemic-repos-no-domain-model.md) lands, the comparison drops the `.value` because the dataclass field is typed as `EstadoIntercambio` directly.

### Push schema-expressible constraints into the schema

```python
# backend/app/schemas/intercambio.py
from pydantic import BaseModel, Field, field_validator

class IntercambioCreate(BaseModel):
    figuritas_ofrecidas_numero: list[int] = Field(..., min_length=1)
    figurita_solicitada_numero: int = Field(..., ge=1)
    solicitado_a_id: int = Field(..., ge=1)

    @field_validator("figuritas_ofrecidas_numero")
    @classmethod
    def sin_repetidos(cls, v: list[int]) -> list[int]:
        if len(v) != len(set(v)):
            raise ValueError("No podés repetir figuritas en la oferta")
        return v
```

Then delete `validar_figuritas_ofrecidas` from `intercambio_service.py:7-13` — Pydantic already enforced it. Pydantic returns 422 with a structured field-level error, which is strictly more informative than the old 400-string-detail response. Update the affected tests' expected status code (they currently expect 400 — they'll be 422 after, which is the more correct code per RFC 4918).

### Mop up with `ruff`

Add to CI (already in [TEST-01](./TEST-01-tests-and-ci.md)'s recommendation):

```
ruff check . --select F,E,W,I,UP,B
```

`F` (pyflakes) catches the dead `usuario_repo` import in `usuarios.py:7`. `B` (bugbear) catches mutable defaults, function-default datetime, etc. `UP` flags Python 3.12 modernizations.

Files that change: `backend/app/schemas/intercambio.py`, `subasta.py` (add enums); every reference to the magic strings (`intercambio_repo.py:20`, `intercambio_service.py:262`, `admin_service.py:10`, `subasta_repo.py:6,19,25`, `subasta_service.py:203`); `intercambio_sch.py` (move duplicate check to validator); delete `validar_figuritas_ofrecidas` from `intercambio_service.py`; remove dead import in `usuarios.py:7`; promote local import in `intercambio_service.py:154`; affected tests update from 400 → 422 where Pydantic now owns the check.

## Why this approach

- **An enum is type-checked once and grep-able forever.** A typo on `"pendinete"` fails at definition time; a typo on `EstadoIntercambio.PENDINETE` fails at edit time in any IDE. The cost is one `class` definition per state field; the upside is that adding `"cancelado"` becomes adding one enum value with the compiler showing you every site that needs to handle it.
- **Validation belongs at the boundary.** Pydantic exists specifically to catch malformed requests *before* the service runs. Every duplicate check in a service is a sign the schema is missing something. Pushing the empty-list check up makes the service body shorter and the API's error responses more useful (422 with `figuritas_ofrecidas_numero: list_too_short` vs. 400 with a Spanish sentence).
- **`ruff` catches small fish at zero cognitive cost.** A dead import is the kind of finding that should *never* reach a human reviewer. Configure once, forget. The other PY-01 micro-smells (local import, defensive `.get(default)`) get cleaned up incrementally — none of them are urgent on their own, and `ruff` will surface them in PRs when they appear next.
