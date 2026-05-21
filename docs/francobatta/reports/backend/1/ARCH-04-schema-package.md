# ARCH-04 — Schemas package: name drift and conflated Create/Response

**Severity:** M  ·  **Area:** Architecture / Pythonic  ·  **Effort:** S

## Diagnosis

The `schemas/` package contains the Pydantic models that define the request and response contracts. It has two cosmetic-but-recurring problems that confuse readers and amplify the deeper issue covered in [ARCH-03](./ARCH-03-anemic-repos-no-domain-model.md) (schemas are doing double duty as domain models).

**1. File names drift.** Four files use the `_sch.py` suffix (`album_sch.py`, `calificacion_sch.py`, `intercambio_sch.py`, `publicacion_sch.py`); five do not (`figurita.py`, `faltante.py`, `oferta.py`, `usuario.py`, `subasta.py`). CLAUDE.md notes the split explicitly: "Files end in `_sch.py` for the newer ones; older ones use the entity name only." That note is a *symptom*, not a fix — once a convention is documented as "the newer half does X," the team has already paid for the inconsistency in cognitive load and will keep paying every time a developer opens the directory.

Pick one. The `_sch.py` suffix is redundant given the package name (`schemas/album.py` is unambiguous), so the cleaner option is to drop the suffix entirely. A two-line `git mv` per file plus updating the imports.

**2. `Response` models inherit from `Create` models.** Pattern repeats everywhere:

- `figurita.py:20-22`: `class FiguritaResponse(FiguritaCreate): id, usuario_id`
- `album_sch.py:14-19`: `class FiguritaAlbumResponse(FiguritaAlbumCreate): id, usuario_id, en_intercambio`
- `publicacion_sch.py:18-29`: `class PublicacionResponse(PublicacionCreate): ...adds id, usuario_id, plus numero/equipo/jugador denormalized from the album`

It looks like reuse, but it's fragile reuse — *the contracts have different roles*. `Create` is "what the caller may send"; `Response` is "what the server guarantees to return." When they share fields by inheritance:

- Adding a server-computed field to `Create` (impossible to set from the client) becomes a code smell rather than a contract violation.
- Excluding a `Create` field from `Response` (e.g., a password) requires `model_config` games or field overrides.
- Validation rules attached to `Create` (e.g., `ge=1`) propagate to `Response` whether you want them or not.

`PublicacionResponse` shows the strain: it has to re-declare `figurita_personal_id, tipo_intercambio, cantidad_disponible` (lines 22-24) *even though they're inherited from `PublicacionCreate`* because the team added denormalized `numero/equipo/jugador` fields and wanted Pydantic to show all fields together in the schema. The result is the inheritance buys nothing and the class is harder to read than two flat classes would be.

**3. There are no `Update` schemas.** PATCH endpoints today (e.g., `intercambios.py:55`: `PATCH /intercambios/{id}/estado`) accept the appropriate small "decision" body (`IntercambioDecision` in `intercambio_sch.py:14-15`) — that's good, the team has *informally* started splitting update semantics. But there's no general convention. When the inevitable "update auction end time" or "update faltante note" request lands, the next dev will either reuse `XxxCreate` (and accept fields they shouldn't) or invent a fourth file (and increase drift).

**4. The package name itself.** `schemas/` is fine, but the import sites are noisy:

```python
from app.schemas.album_sch import FiguritaAlbumCreate, FiguritaAlbumResponse
from app.schemas.figurita import FiguritaCreate
```

After dropping the `_sch.py` suffix and adding a thin `__init__.py` that re-exports the most-used types, the routers can simply do:

```python
from app.schemas import FiguritaAlbumCreate, FiguritaAlbumResponse, FiguritaCreate
```

Small, but readers parse it once instead of every file.

## Evidence

- `backend/app/schemas/album_sch.py`, `calificacion_sch.py`, `intercambio_sch.py`, `publicacion_sch.py` — `_sch.py` suffix
- `backend/app/schemas/figurita.py`, `faltante.py`, `oferta.py`, `usuario.py`, `subasta.py` — no suffix
- `backend/app/schemas/figurita.py:20-22` — `class FiguritaResponse(FiguritaCreate): ...`
- `backend/app/schemas/album_sch.py:14-19` — `class FiguritaAlbumResponse(FiguritaAlbumCreate): ...`
- `backend/app/schemas/publicacion_sch.py:18-29` — Response re-declares Create fields, inheritance buys nothing
- `backend/app/schemas/intercambio_sch.py:14-15` — `IntercambioDecision` (the right shape for an update body, but ad-hoc)

## Recommendation

Three coordinated moves, each tiny.

**Move 1 — Drop the `_sch.py` suffix.** `git mv album_sch.py album.py`, etc. Update the imports in each router and service. The change is mechanical, fits in one PR, and removes the asymmetry forever.

**Move 2 — Flatten Create/Response, share via composition or `BaseModel` interpolation, not inheritance.**

```python
# backend/app/schemas/figurita.py
from pydantic import BaseModel, Field
from enum import Enum

class TipoIntercambio(str, Enum):
    INTERCAMBIO_DIRECTO = "intercambio_directo"
    SUBASTA = "subasta"

class _FiguritaFields(BaseModel):
    numero: int = Field(..., ge=1)
    equipo: str = Field(..., min_length=1)
    jugador: str = Field(..., min_length=1)
    cantidad: int = Field(..., ge=1)
    tipo_intercambio: TipoIntercambio

class FiguritaCreate(_FiguritaFields):
    """Request body for POST /figuritas/."""

class FiguritaResponse(_FiguritaFields):
    """Response body for figurita endpoints."""
    id: int
    usuario_id: int

class FiguritaUpdate(BaseModel):
    """PATCH body — every field optional."""
    equipo: str | None = Field(default=None, min_length=1)
    jugador: str | None = Field(default=None, min_length=1)
    cantidad: int | None = Field(default=None, ge=1)
```

The `_FiguritaFields` mixin documents intent ("these fields describe a figurita") without committing to "Response is a Create with extras." `FiguritaUpdate` is the missing third member, ready for the day a PATCH endpoint needs it. Note that `tipo_intercambio` and `numero` are deliberately *not* in `FiguritaUpdate` — those are immutable, and the Update class enforces that by omission, not by exception messages.

**Move 3 — Re-export through `__init__.py`.**

```python
# backend/app/schemas/__init__.py
from .figurita import FiguritaCreate, FiguritaResponse, FiguritaUpdate, TipoIntercambio
from .album import FiguritaAlbumCreate, FiguritaAlbumResponse
from .publicacion import PublicacionCreate, PublicacionResponse, SugerenciaResponse
# ...
```

…and update imports in routers from `from app.schemas.publicacion_sch import ...` to `from app.schemas import ...`. Optional but improves the read.

Files that change: every file in `backend/app/schemas/` (rename, flatten), every router (update imports), and `backend/app/services/intercambio_service.py:154` (`from app.schemas.album_sch import FiguritaAlbumCreate` — note the *deferred import*, which is itself a small smell that the flatten + re-export removes naturally).

## Why this approach

- **The `_FiguritaFields` mixin separates "the data" from "the role"** (request vs. response vs. update). Inheriting `Response from Create` conflates the two. Once you split, each contract becomes a one-screen object you can read top to bottom and understand fully.
- **Adding `Update` now is much cheaper than adding it on demand.** Even if it goes unused for an entrega, having the slot reserved nudges the team to think about which fields are immutable. The current `Create`-only world says "everything is mutable on creation, ask me again if you want to update" — which is the wrong default.
- **A flat naming convention is invisible when it's working.** Today `schemas/album_sch.py` vs. `schemas/figurita.py` is visible — every new dev asks why. After the cleanup, no one asks. That's the goal of consistency work: cease to be noticed.
