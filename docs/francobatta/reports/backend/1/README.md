# Backend Evaluation — TP TACS 2026-C1

Senior code review of the FastAPI backend at the boundary between Entrega 2 (UI complete) and Entrega 3 (real persistence). Each row below links to a per-finding report. Reports describe the problem, cite file:line evidence, recommend one concrete fix with a short code sample, and explain the tradeoff so the team learns the reasoning, not just the rule.

## State of the backend

The backend is in a good shape *for its stage*. The layered split (routers / services / repositories / schemas) is real, not aspirational. Pydantic is used for input contracts, status codes are explicit on most write endpoints, the integration test suite covers happy paths for every major user story, datetimes are timezone-aware, and the CI workflow runs on every push. The team has clearly read FastAPI's conventions and applied them. Several patterns to copy from internally already exist — `intercambios.py`'s `PATCH /{id}/estado` for state transitions, `album.py`'s `204 No Content` on DELETE, `subasta_service.py`'s domain-style exceptions raised separately from the router — they just haven't been generalized.

The biggest debt is **layering discipline** and **the contract between services and routers**. Two services use different exception idioms (`HTTPException` directly vs. `ValueError`/`PermissionError`), and the translation between them is done by substring-matching error messages in the router. This is the single change with the highest leverage — it shows up in three reports (ARCH-01, ERR-01, REST-01) and unblocks most of the others. Adjacent to it: every repository returns `dict[str, Any]`, which means the type system is effectively turned off at the layer where it matters most, and ID generation uses two incompatible strategies (one of which reuses IDs after deletes — a dormant correctness bug, ARCH-02).

The critical findings are smaller but important. Four endpoints (admin stats, public auction listing, figurita search, user reputación) skip auth entirely (REST-02) — including the admin endpoint by name. The token comparison is timing-attack vulnerable (SEC-01). Both fix in under an hour. Start with those, then take the highs (REST-01, ARCH-01, ARCH-02, ARCH-03, ERR-01) — they shape Entrega 3 and the team should make them before the database lands. The medium hygiene items (REST-03, REST-04, ARCH-04, TEST-01, PY-01) are short and educational; they can be done in any order, by whoever has spare time during an entrega.

## How to read these reports

Each report has the same shape:

- **Diagnosis** — what's happening, with file:line evidence, anchored to a named principle (Richardson Maturity, Repository pattern, OWASP item, PEP).
- **Evidence** — file:line bullets. No prose, just receipts.
- **Recommendation** — one named approach plus a short code sample (~10-20 lines).
- **Why this approach** — 2-3 bullets covering the tradeoff against the obvious alternative.

**Severity legend.** **C** critical (security or correctness), **H** high (debt that blocks Entrega 3), **M** medium (consistency / hygiene), **L** low (style / nit).
**Effort legend.** **S** small (under an hour), **M** medium (one session), **L** large (a sprint slice).

## Findings

| # | Code | Title | Sev | Effort | One-line synopsis |
|---|------|-------|-----|--------|-------------------|
| 1 | [SEC-01](./SEC-01-token-model.md) | Token model: non-constant-time, non-rotatable, unsigned | **C** | S → L | `==` token compare leaks timing; the model itself is opaque-but-unverifiable. |
| 2 | [REST-02](./REST-02-unauth-endpoints.md) | Unauthenticated endpoints leak data | **C** | S | Admin stats, public subastas/figuritas listings, and `/usuarios/{id}/reputacion` skip the auth dependency. |
| 3 | [ARCH-01](./ARCH-01-layer-leakage.md) | Layer leakage: routers call repos, services raise `HTTPException` | **H** | M | Two layering violations meet in the middle and erase the boundary. |
| 4 | [ARCH-02](./ARCH-02-repository-pattern.md) | Repository pattern inconsistencies | **H** | M | `len(_db)+1` vs `_next_id`, `crear` vs `create`, `_db` vs `_db_<entity>`. ID collisions waiting to happen. |
| 5 | [REST-01](./REST-01-verbs-in-urls.md) | Verbs in URLs and ad-hoc state transitions | **H** | M | `/subastas/{id}/ofertas/{id}/aceptar`, `/ofertar`, `/publicaciones/mias` — RPC dressed up as REST. |
| 6 | [ARCH-03](./ARCH-03-anemic-repos-no-domain-model.md) | Anemic dict-returning repos; no domain model | **H** | L | Every repo returns `dict[str, Any]`; schemas double as domain. Type system disabled by convention. |
| 7 | [ERR-01](./ERR-01-error-handling.md) | Inconsistent error idiom; routers do substring-matching | **H** | M | Two services, two exception languages, then the router decodes errors by `"no encontrada" in detail.lower()`. |
| 8 | [REST-03](./REST-03-response-envelopes-status-codes.md) | Inconsistent response envelopes & implicit status codes | **M** | S | DELETE returns 200; some endpoints wrap with `mensaje`/`usuario_id`, others return raw. |
| 9 | [REST-04](./REST-04-cors-versioning-pagination.md) | CORS wildcard with credentials; no pagination/versioning strategy | **M** | S | `allow_origins=["*"] + allow_credentials=True` is invalid; collection GETs are unbounded. |
| 10 | [ARCH-04](./ARCH-04-schema-package.md) | Schemas package: name drift and conflated Create/Response | **M** | S | `_sch.py` on 4 files, bare on 5; `class XxxResponse(XxxCreate): ...` everywhere. |
| 11 | [TEST-01](./TEST-01-tests-and-ci.md) | Tests couple to private repo globals; CI lacks lint/type/coverage | **M** | S | `tests/conftest.py` calls `album_repo._db.clear()`; CI runs only `pytest -v`. |
| 12 | [PY-01](./PY-01-magic-strings-and-validation.md) | Magic strings for domain states; Pydantic validation duplicated | **M** | S | `"pendiente"` lives in 3 files; `cantidad_disponible > figurita["cantidad"]` is re-checked in a service after Pydantic could express it. |

The reports above are numbered roughly in **execution order**: criticals and architectural foundations first (they shape the rest), then high-debt cleanup, then medium hygiene. The severity column is the source of truth — pick what to do next from there.
