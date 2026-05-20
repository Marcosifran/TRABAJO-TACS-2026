# ARCH-03 — Anemic dict-returning repos; no domain model layer

**Severity:** H  ·  **Area:** Architecture / Pythonic  ·  **Effort:** L

## Diagnosis

Every repository returns `dict[str, Any]` (or `list[dict]`) and every service consumes them as such. Pydantic schemas (`schemas/`) are used as **request and response contracts** at the HTTP boundary, but the moment the request crosses into the service layer the data is `.model_dump()`-ed into a plain dict and stays a dict for the rest of its life. There is no domain model. As a consequence, the project's type system is effectively turned off at the layer where it matters most.

The shape recurs in every repo:

```python
# album_repo.py:37-45
def create(figurita: FiguritaAlbumCreate, usuario_id: int) -> dict:
    global _next_id
    nueva = figurita.model_dump()
    nueva["id"] = _next_id
    nueva["usuario_id"] = usuario_id
    _next_id += 1
    _db.append(nueva)
    return nueva
```

Returning `dict` has three downstream consequences:

**1. The type checker is blind to fields.** `mypy` sees `dict` and can't distinguish `nueva["nombre"]` (which doesn't exist) from `nueva["jugador"]` (which does). The bug surfaces as a `KeyError` at runtime, in a test if you're lucky, in prod if not. Today the team gets by because the codebase is small and grep-able. At Entrega 3, with twice the surface and a real DB to hide schema drift, the cost compounds.

**2. Domain logic gets *anchored* to dict access.** `intercambio_service.py:262` reads `intercambio["estado"] != "pendiente"`; `subasta_service.py:163` reads `subasta["usuario_id"]`; `admin_service.py:18` reads `p.get("equipo", "Desconocido")`. The `.get()` with a default is the tell — it's a defensive read against fields that might not be in the dict, which is a question that should be impossible to ask if the data had a type. The defensive reads are how anemic models slowly grow.

**3. The boundary between API schema and domain object is invisible.** `schemas/` is doing two jobs: it's the input/output Pydantic contract *and* it's the de-facto domain shape (because the repo dict is just a `.model_dump()` of it). Today these align. The day they need to diverge — say, the API wants `usuario` as a nested object but the storage wants `usuario_id` — every service function has to know which shape the dict is in, because the same key name (`usuario_id`) might or might not exist. This is the moment the team will discover the domain model the hard way. Building it before is much cheaper.

A specific consequence visible today: `subasta_service.py:185-188` does `figurita_album["usuario_id"] = ofertante_id` directly on a dict returned by `album_repo.get_by_id(...)`. That dict is the actual `_db` row. The service is mutating storage by side effect. With a real domain object that's read-only (e.g., a frozen dataclass), the temptation is gone and the service is forced to express the change as `album_repo.transfer_to(album_id, ofertante_id)` — which is also where the eventual DB UPDATE lives. The domain model isn't a vanity layer; it shapes how the rest of the code is forced to talk about state.

## Evidence

- `backend/app/repositories/album_repo.py:37-45` — `.model_dump() + id` pattern, returns `dict`
- `backend/app/repositories/intercambio_repo.py:13-23` — `crear_intercambio` builds a dict literal and returns it
- `backend/app/repositories/usuario_repo.py:16-25` — `get_all`, `get_by_id`, `get_by_token` all `-> dict` / `list[dict]`
- `backend/app/services/intercambio_service.py:262` — `intercambio["estado"] != "pendiente"` (magic string + dict access)
- `backend/app/services/subasta_service.py:185-188` — service mutates `figurita_album["usuario_id"]` on a dict that *is* storage
- `backend/app/services/admin_service.py:18` — `p.get("equipo", "Desconocido")` — defensive read against an "any" shape
- `backend/app/schemas/album_sch.py:14-19` — `FiguritaAlbumResponse(FiguritaAlbumCreate)` — schemas doing double duty as domain

## Recommendation

Introduce a `domain/` layer with frozen dataclasses (or `pydantic.BaseModel` with `model_config = {"frozen": True}`) for each entity. Repos return domain objects. Services consume and produce domain objects. Pydantic schemas continue to live at the *edge* (request bodies, response bodies) and convert at the boundary.

```python
# backend/app/domain/album.py  (new file)
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class FiguritaAlbum:
    id: int
    usuario_id: int
    numero: int
    equipo: str
    jugador: str
    cantidad: int

# backend/app/repositories/album_repo.py
from app.domain.album import FiguritaAlbum
from app.repositories._id import id_seq        # see ARCH-02

_ids = id_seq()
_db: list[FiguritaAlbum] = []

def create(figurita: FiguritaAlbumCreate, usuario_id: int) -> FiguritaAlbum:
    nueva = FiguritaAlbum(
        id=next(_ids), usuario_id=usuario_id,
        numero=figurita.numero, equipo=figurita.equipo,
        jugador=figurita.jugador, cantidad=figurita.cantidad,
    )
    _db.append(nueva)
    return nueva

def transfer_to(album_id: int, new_usuario_id: int) -> FiguritaAlbum | None:
    for i, f in enumerate(_db):
        if f.id == album_id:
            _db[i] = replace(f, usuario_id=new_usuario_id)   # from dataclasses
            return _db[i]
    return None
```

The router then converts at the boundary using `FiguritaAlbumResponse.model_validate(domain_obj, from_attributes=True)` — Pydantic v2 handles dataclass → BaseModel via attribute access. FastAPI does this for free when `response_model=FiguritaAlbumResponse` is declared.

For the `subasta_service.py:185-188` "mutate storage" case, the redesign forces a proper method:

```python
# subasta_service.py  (sketch)
album_repo.transfer_to(publicacion.figurita_personal_id, ofertante_id)
```

The service no longer reaches into a dict; the repo owns the mutation. This is the same instinct that will produce the `UPDATE` in Entrega 3.

Files that change: new `backend/app/domain/` package (one file per entity), every `backend/app/repositories/*.py` (the `dict` ⇒ domain conversion), every `backend/app/services/*.py` (consume domain objects, no more `["key"]`), and the routers' `response_model=` lines pick up the conversion for free.

## Why this approach

- **Frozen dataclasses are the cheapest domain layer Python offers.** No ORM, no metaclass magic. `slots=True` keeps memory tight; `frozen=True` blocks the `figurita_album["usuario_id"] = ...` antipattern at the language level. The team learns the *principle* without paying the cognitive cost of SQLAlchemy yet.
- **Pydantic at the edge, dataclass in the middle is a well-trodden pattern.** It mirrors what mature FastAPI codebases settle on. Pydantic is heavy when used everywhere (every read parses + validates again), whereas a frozen dataclass is `O(1)`. The boundary conversion is one call.
- **The refactor is gradual.** Migrate one entity per PR (album → figurita → publicacion → ...). Tests stay green because each step is local. The team practices the "swap implementation behind the protocol" muscle that is *exactly* what Entrega 3 needs.
