# ARCH-02 — Repository pattern inconsistencies

**Severity:** H  ·  **Area:** Architecture  ·  **Effort:** M

## Diagnosis

The `repositories/` package is a Repository Pattern in shape: each entity has a module that owns a module-level list and exposes functions for CRUD. That's a defensible choice for an in-memory stub and is friendly to the Entrega-3 swap. The problem is that there is no shared *contract* — every repo invents its own. The inconsistencies don't break anything individually, but together they make the package feel like five small dialects, and one of them has a correctness bug.

**1. Two ID-generation strategies coexist, and one of them is wrong.** The repos using `_next_id` (`album_repo.py:4,41-43`, `publicacion_repo.py:4,53-64`) generate IDs that survive deletes — once an ID has been used, the counter never goes back. The repos using `len(_db) + 1` (`figurita_repo.py:52`, `intercambio_repo.py:15`, `oferta_repo.py:5`, `calificacion_repo.py:17`, `subasta_repo.py:8`, `usuario_repo.py:32` for faltantes) **reuse IDs on delete**: delete record 3 from a list of length 3, create a new record → `len(_db) + 1 = 3` again. In the in-memory model this can already cause references to break (an oferta whose `subasta_id` pointed to the old #3 now points to the new #3 owned by a different user). In Entrega 3 under any DB worth its salt, the same flaw will be silently caught by a unique constraint and surface as a 500. **Fix this now**; the cost is identical to fixing it later, and the bug is dormant today.

**2. Method names are inconsistent across repos.** Some use English (`create`, `delete`, `get_by_id`), some use Spanish (`crear`, `crear_intercambio`, `crear_oferta`, `buscar_intercambio_por_id`). The mix is not by file — `intercambio_repo.py` has both `crear_intercambio` and `listar_intercambios_por_usuario`. `figurita_repo.py` has both `get_by_id` and `buscar_por_numero_y_usuario`. The TP CLAUDE.md note says Spanish naming is acceptable, but consistency within the language is not the same question. Pick one of "English verbs" or "Spanish verbs" for the CRUD primitives, and use entity-suffixed names only for non-CRUD helpers. Right now a caller can't predict whether `oferta_repo` has `create` or `crear` without opening the file.

**3. Module-global names drift.** `album_repo.py`, `publicacion_repo.py`, `figurita_repo.py`, `intercambio_repo.py`, `calificacion_repo.py` all have a `_db` (singular). `subasta_repo.py` has `_db_subastas`. `oferta_repo.py` has `_db_ofertas`. `usuario_repo.py` has `_db_usuarios` *and* `_db_faltantes` (one repo owning two domains, see point 5). This isn't only cosmetics — `tests/conftest.py:23-31` resets these globals by name, so any new repo that picks a different name needs the test harness updated in lockstep. (See [TEST-01](./TEST-01-tests-and-ci.md) for the broader test-coupling problem; the cure for both is the same `reset()` API.)

**4. The interface is not uniform.** `album_repo` has `update()`, `update_cantidad()`, `delete()`. `figurita_repo` has no `update()` at all. `intercambio_repo` has `crear_intercambio` and `responder_intercambio` (a domain-specific mutator named like a service method) but no `delete()`. `subasta_repo` has `update(subasta_actualizada: dict)` that takes the whole dict back — which means a caller must read the dict, mutate it, and write it; partial updates aren't expressible. None of this is "wrong"; it's just not a *pattern*. The point of the Repository Pattern is that the caller can predict the surface.

**5. `usuario_repo` is two repositories pretending to be one.** It owns `_db_usuarios` and `_db_faltantes`. Faltantes are not a property of a user — they are a separate entity (`numero_figurita` belongs-to user, with their own lifecycle). The `tests/conftest.py:27` line only resets `_db_faltantes`, never the users (because users are seeded from env). Splitting `faltante_repo.py` off would make both halves cleaner and would let the user "repo" focus on auth.

**6. Module-level mutable state is invisible until uvicorn workers > 1.** Today the team runs uvicorn with a single worker in Docker. The moment Entrega 3 introduces gunicorn or `--workers 2`, every write race becomes a data corruption. This is the most under-appreciated risk in the package. The Recommendation below is the right place to call it out, because the protocol-based seam makes the future swap-to-DB the natural fix.

## Evidence

- `backend/app/repositories/album_repo.py:4,41-43` — `_next_id` counter
- `backend/app/repositories/publicacion_repo.py:4,53-64` — `_next_id` counter
- `backend/app/repositories/figurita_repo.py:52` — `nueva["id"] = len(_db) + 1` (reuses on delete)
- `backend/app/repositories/intercambio_repo.py:15` — `"id": len(_db) + 1`
- `backend/app/repositories/oferta_repo.py:5` — `"id": len(_db_ofertas) + 1`
- `backend/app/repositories/calificacion_repo.py:17` — `"id": len(_db) + 1`
- `backend/app/repositories/subasta_repo.py:8` — `"id": len(_db_subastas) + 1`
- `backend/app/repositories/usuario_repo.py:32` — `faltante_data["id"] = len(_db_faltantes) + 1`
- `backend/app/repositories/intercambio_repo.py:13,36` — `crear_intercambio` / `responder_intercambio` (Spanish verbs)
- `backend/app/repositories/oferta_repo.py:3` — `crear_oferta` (Spanish)
- `backend/app/repositories/album_repo.py:37,55,69` — `create` / `delete` / `update` (English)
- `backend/app/repositories/usuario_repo.py:4,8` — `_db_usuarios` + `_db_faltantes` in one file
- `backend/tests/conftest.py:23-31` — reset code that names every global directly

## Recommendation

Two coordinated moves: a tiny shared "next id" helper that fixes the correctness bug everywhere, and a `Protocol` that documents the intended interface and prepares the Entrega-3 swap. Renaming is a follow-up.

### Centralize ID generation

```python
# backend/app/repositories/_id.py  (new file)
from itertools import count
from collections.abc import Iterator

def id_seq(start: int = 1) -> Iterator[int]:
    return count(start)

# in any repo
from app.repositories._id import id_seq

_ids = id_seq()
_db: list[dict] = []

def create(data) -> dict:
    nuevo = {**data.model_dump(), "id": next(_ids)}
    _db.append(nuevo)
    return nuevo
```

`itertools.count` is monotonic and never reuses an id, even across deletes. Replace every `len(_db) + 1` with `next(_ids)`. The CI / `tests/conftest.py` will need a reset hook — see Recommendation in [TEST-01](./TEST-01-tests-and-ci.md), where `repo.reset()` resets *both* `_db` and the id sequence. **This is the single highest-leverage repo fix.**

### Document the interface with a Protocol

```python
# backend/app/repositories/_interface.py
from typing import Protocol, TypeVar
from collections.abc import Iterable

T = TypeVar("T")
ID = TypeVar("ID")

class Repository(Protocol[T, ID]):
    def get_all(self) -> Iterable[T]: ...
    def get_by_id(self, id_: ID) -> T | None: ...
    def create(self, data) -> T: ...
    def update(self, entity: T) -> T: ...
    def delete(self, id_: ID) -> bool: ...
    def reset(self) -> None: ...
```

Each repo module satisfies the `Protocol` structurally — Python doesn't require an explicit `class FigurinRepository(Repository): ...`. The benefit is that mypy/pyright will *flag* a repo that drifts (`crear` not matching `create`), and the service layer can declare its repo dependency as `Repository[Figurita, int]` for Entrega-3 swap. Domain-specific helpers (`get_by_usuario`, `buscar_por_numero_y_usuario`) stay on the concrete module — the Protocol describes the *core*, not the surface.

Files that change: every file in `backend/app/repositories/`. Migrate the names in waves so reviews stay small: ID fix first, then rename `crear*` → `create*` repo by repo, then split `usuario_repo` into `usuario_repo` + `faltante_repo`.

## Why this approach

- **The `_next_id` pattern is already in the codebase.** The fix is "do what `album_repo` does, everywhere," not a novel design. The reason to wrap it in `itertools.count` is so that the `reset()` hook (see [TEST-01](./TEST-01-tests-and-ci.md)) can rebind the iterator without reaching into a module-level int.
- **A `Protocol` is the cheapest way to lock in the contract without forcing OOP.** The alternative — abstract base classes — would require every repo to become a class, which is heavier than the current module style and would surface the singleton problem (single instance? injected?). `Protocol` keeps the module style and only enforces *shape*.
- **Splitting `usuario_repo` doesn't change behavior; it changes future code reviews.** A PR that adds a "faltantes-by-equipo" filter today touches `usuario_repo.py` and lights up the auth-tests reviewer for no reason. Tomorrow it touches `faltante_repo.py` and the right people are paged. This is the cheap form of Conway's Law.
