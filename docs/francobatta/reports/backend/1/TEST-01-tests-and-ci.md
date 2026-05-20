# TEST-01 — Tests couple to private repo globals; CI lacks lint/type/coverage

**Severity:** M  ·  **Area:** Tests / CI  ·  **Effort:** S

## Diagnosis

The test suite is in better shape than most early-stage projects of this size — there are real integration tests covering happy paths and several error paths, the unit-vs-integration split is meaningful, and there's a CI workflow that runs on every push and PR. The problems below are all about *robustness over time* and the gap between "the tests pass today" and "the tests still pass after a refactor."

**1. Tests reach into private module globals.** `tests/conftest.py:17-32` defines an autouse fixture that resets state before and after every test by calling:

```python
album_repo._db.clear()
album_repo._next_id = 1
publicacion_repo._db.clear()
publicacion_repo._next_id = 1
usuario_repo._db_faltantes.clear()
intercambio_repo._db.clear()
calificacion_repo._db.clear()
subasta_repo._db_subastas.clear()
oferta_repo._db_ofertas.clear()
```

Every line is a private-attribute access (`_db`, `_db_faltantes`, `_db_subastas`, `_db_ofertas`). If a repo renames its global — and [ARCH-02](./ARCH-02-repository-pattern.md) recommends exactly that as part of the consistency cleanup — every test file that imports `conftest` breaks at collection time. The implicit contract is "test infrastructure knows the implementation of every repo." This is the same kind of coupling the Repository Pattern is supposed to *prevent*.

A related instance is `tests/integration/conftest.py:21-29`:

```python
@pytest.fixture
def token_user1():
    return usuario_repo._db_usuarios[0]["token"]
```

If `_db_usuarios` becomes a dict-by-id, becomes a property, becomes a thin shim over a DB, every integration test starts failing on import. The "two seeded users" fact is real and stable; the *access path* to those tokens shouldn't have to be.

**2. Integration tests cover happy paths well; error paths are spotty.** `test_proponer_intercambio.py` is a good example: `TestProponerIntercambio` has 10 tests covering empty list, self-proposal, same-number, non-existent user, subasta-vs-direct, etc. — that's solid. But:

- No test asserts 401 when `X-User-Token` is missing or wrong. There's a single happy-path proof in some files (`test_autenticacion.py` exists, but the assumption can't be that one file covers auth for every route).
- The `responder_intercambio` 404 fallback at `intercambios.py:73-74` is unreachable (the service already raises 403 at line 257 for the same condition) — no test asserts the 403, only one asserts the 200/400 split. Dead code stays alive because it isn't tested.
- Some helpers (`test_proponer_intercambio.py:19-43 agregar_y_publicar`) use hardcoded payloads. A factory fixture would let tests vary inputs more cheaply and surface boundary cases that today require copy-paste.

**3. CI runs pytest, nothing else.** `.github/workflows/backend-tests.yml` is 6 lines of meaningful CI:

```yaml
- name: Run tests
  run: pytest tests/ -v
```

That's the floor. The next three steps for a senior-team CI are all cheap:

- **Linting / formatting** with `ruff` (it's a single fast binary, replaces flake8 + isort + black-as-checker).
- **Type checking** with `mypy` or `pyright`. The codebase has type hints; mypy would already flag a few mismatched returns (`publicacion_service.py:42` returns `bool | None`, callers treat as `bool`).
- **Coverage** with `pytest --cov=app --cov-fail-under=70`. The TP spec says "a use case without tests is incomplete" — coverage is the mechanical proof.

None of these need to be perfect from day one. A `pytest --cov=app --cov-report=term-missing` step plus a generous threshold (60%-ish) catches the regression where a new endpoint ships with no test. `ruff check .` and `mypy app/` with `--ignore-missing-imports` are similarly low-friction.

**4. The unit suite is thin.** `tests/unit/` has one file (`test_figurita.py`). Most of the testable logic lives in `services/` and would benefit from unit tests that don't pay the cost of spinning up `TestClient`. Once [ARCH-01](./ARCH-01-layer-leakage.md) is done (services stop raising `HTTPException`), unit-testing them is a one-line `pytest.raises(NotFound)` instead of an integration round-trip — and the team gets the test-pyramid shape for free.

## Evidence

- `backend/tests/conftest.py:17-32` — autouse fixture reaches into 8 private module globals across 6 repos
- `backend/tests/integration/conftest.py:21-29` — token fixtures index into `usuario_repo._db_usuarios`
- `backend/tests/integration/test_proponer_intercambio.py:19-43` — hardcoded payloads in `agregar_y_publicar` helper
- `backend/tests/integration/test_proponer_intercambio.py` — covers 9 business-rule cases, but no 401 case for the route
- `backend/app/routers/intercambios.py:73-74` — dead 404 fallback (unreachable; not exercised by any test)
- `.github/workflows/backend-tests.yml:23-30` — CI runs only `pytest -v`; no ruff/mypy/coverage

## Recommendation

A small `reset()` API on each repo plus a CI step that runs ruff, mypy, and coverage. Both are tiny PRs.

### Add a `reset()` per repo, route tests through it

```python
# backend/app/repositories/album_repo.py
def reset() -> None:
    """Clear in-memory state. Test infrastructure use only."""
    global _ids
    _db.clear()
    _ids = id_seq()       # see ARCH-02

# backend/app/repositories/usuario_repo.py
def reset() -> None:
    """Re-seed the two demo users; clear faltantes."""
    _db_faltantes.clear()
    _db_usuarios[:] = [
        {"id": 1, "nombre": "marcos", "email": "marcos@utn", "token": settings.user_1_token},
        {"id": 2, "nombre": "jeronimo", "email": "jeronimo@utn", "token": settings.user_2_token},
    ]
```

```python
# backend/tests/conftest.py
import pytest
from app.repositories import (
    album_repo, publicacion_repo, usuario_repo, intercambio_repo,
    subasta_repo, oferta_repo, calificacion_repo, figurita_repo,
)

_REPOS = (
    album_repo, publicacion_repo, usuario_repo, intercambio_repo,
    subasta_repo, oferta_repo, calificacion_repo, figurita_repo,
)

@pytest.fixture(autouse=True)
def limpiar_db():
    for repo in _REPOS:
        repo.reset()
    yield
```

The test infrastructure now depends on a *named* public-by-convention method, not a *private* attribute name. A repo that changes its internal storage (a dict, a sorted list, a real DB session) reimplements `reset()` and the tests don't notice. The `token_user1` fixture similarly becomes `usuario_repo.get_by_id(1)["token"]` (or, after [ARCH-03](./ARCH-03-anemic-repos-no-domain-model.md), `usuario_repo.get_by_id(1).token`).

### Upgrade CI

```yaml
# .github/workflows/backend-tests.yml
- name: Lint
  run: ruff check .
- name: Type check
  run: mypy app/ --ignore-missing-imports
- name: Tests with coverage
  run: pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=70
```

Add `ruff`, `mypy`, and `pytest-cov` to `requeriments.txt` (the misspelled file — fixing the filename is a separate, larger change). Start the coverage threshold low; raise it one entrega at a time.

Files that change: every `backend/app/repositories/*.py` (add `reset()`), `backend/tests/conftest.py`, `backend/tests/integration/conftest.py`, `.github/workflows/backend-tests.yml`, `backend/requeriments.txt`.

## Why this approach

- **A `reset()` method is the smallest possible Repository-Pattern-compliant API change that solves the right problem.** It doesn't require Protocol adoption, it doesn't require dataclasses, it doesn't require renaming. Each repo grows one function and the test harness becomes refactor-proof. The fix is forward-compatible with every other ARCH report.
- **CI guardrails are a *teaching* mechanism for interns.** A failing `ruff check` on a PR is a hands-off way to catch unused imports (`usuarios.py:7` `from app.repositories import usuario_repo` — never used) and inconsistent style. A failing `mypy` is how the team learns where their type hints lied. Coverage with a low floor catches the "I added a route, forgot the test" case without ever needing to be tuned.
- **The test pyramid will fix itself if you let it.** Once services don't raise `HTTPException`, unit tests on services become natural. The team doesn't need to be told to write more unit tests — they'll write them because they're suddenly cheaper than the integration alternative. The CI guardrails just measure the result.
