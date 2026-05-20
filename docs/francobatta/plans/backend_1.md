 Backend Evaluation Plan — TP TACS 2026-C1

 Context

 The project is a fullstack web app for trading sticker collectibles ("figuritas") built by interns learning fullstack as part of the TACS 2026-C1
 course. Per the spec PDF, the team is currently between Entrega 2 (UI is live) and Entrega 3 (real persistence — the in-memory state is intentional
  for now). The user — acting as a senior reviewer — wants a thorough evaluation of the backend that will help the interns level up. The output is a
  set of per-finding reports that for each major issue describe what's wrong, how to fix it, and why it matters.

 This file plans the evaluation methodology and deliverables for the backend only. A separate plan will cover the frontend later. Three
 Explore-agent sweeps have already mapped the REST surface, layering, auth/error/test/Pythonic concerns down to file:line evidence — those findings
 drive the report inventory below.

 Scope

 In scope. Everything under backend/ (Python 3.12 / FastAPI). Specifically:
 - REST surface and HTTP semantics (Richardson Maturity, idempotency, safety, status codes, response shape).
 - Layered architecture (routers / services / repositories / schemas / core).
 - Authorization model and security posture (with the explicit caveat from the PDF that auth is not the focus, but users must be distinguishable —
 we evaluate against that bar plus a "what would Entrega 3 need" forward-look).
 - In-memory persistence as a stub for Entrega 3 (Repository pattern fidelity, not absolute DB performance).
 - Error handling consistency and Pythonic idiom.
 - Test hierarchy, isolation, and coverage.
 - Pythonic / idiomatic best practices beyond the seven listed (DI, enums, type hints, naming, datetime hygiene, magic strings, mutable globals).

 Out of scope (this round).
 - Frontend (separate plan).
 - Spanish naming conventions — the user said treat as OK.
 - Performance, load testing (PDF asks for it later; flagged but not measured here).
 - Deployment / cloud (Entrega 3 concern).

 Evaluation Framework

 For each dimension, the evaluator asks the questions below. Answers — backed by file:line evidence already gathered — feed the report inventory.

 REST maturity & HTTP semantics

 - Are resources nouns? Are state transitions modeled with proper verbs (POST/PUT/PATCH/DELETE) and sub-resources, not verbs in the URL?
 - Are GETs safe? Are PUT/DELETE idempotent?
 - Are status codes explicit and correct (201 on create, 204 on delete, 404 vs 400 vs 403 vs 422 discipline)?
 - Is the response shape consistent (raw resource vs envelope), and are errors structured (RFC 7807 or at least a stable shape)?
 - Where does the API sit on the Richardson scale (0 = single endpoint, 1 = resources, 2 = HTTP verbs+codes, 3 = HATEOAS)?
 - Cross-cutting: CORS, versioning, pagination, content negotiation, caching headers.

 Layered architecture

 - Does each layer have a single responsibility? Do routers stay thin (parse → call service → return)?
 - Do services own business rules and orchestrate repos — without importing FastAPI?
 - Do repos expose a uniform CRUD-like interface and own all state?
 - Are domain models distinct from API schemas?
 - Is dependency direction one-way (router → service → repo → schema)?
 - Is there any DI/seam that would allow swapping the in-memory repo for a real DB without touching services? (Forward-look to Entrega 3.)

 Authorization & security

 - Is auth stateless in the strict sense (signed/verifiable, expiring) or only "stateless by accident" (no session store, but also no verification)?
 - Are tokens rotatable, revocable, scoped, time-bound? Are they compared in constant time?
 - Are protected endpoints actually protected? Any leakage of user IDs / tokens / internal state?
 - Is the authenticated user pulled from the token only, never from the body/path (horizontal privilege check)?
 - CORS, input limits, secret handling (.env gitignore, never-in-repo), CSRF posture.

 Repository pattern fidelity (in-memory stub)

 - Uniform method names across repos? Consistent ID generation strategy? Consistent global naming?
 - Are repos truly hidden behind functions, or do other layers reach into module globals (including tests)?
 - Module-level mutable state under multiple uvicorn workers — race conditions?

 Error handling

 - One idiom or many (HTTPException vs ValueError vs PermissionError)?
 - Are domain exceptions translated to HTTP at the boundary, or do business functions know HTTP status codes?
 - Is there a global exception handler producing a stable error envelope?
 - Is Pydantic doing the validation it can, or are services duplicating Field constraints in if-checks?

 Tests

 - Is the unit/integration split meaningful, or is everything integration?
 - Are arrange/act/assert clear? Are happy paths and error paths both covered?
 - Do tests couple to private repo internals (_db, _next_id) or to a clean public reset API?
 - CI: does it lint, type-check, and report coverage — or only run pytest?

 Pythonic / idiomatic

 - dict[str, Any] vs typed objects (dataclass / Pydantic / NamedTuple).
 - Magic strings vs Enum / StrEnum for domain states.
 - Type-hint completeness; list[dict] vs list[SomeModel].
 - f-strings, comprehensions over manual loops, next(...) lookups, pathlib, naive vs aware datetime.
 - Import style consistency (from app.X import module vs from app.X.module import fn).
 - __init__.py re-exports, naming drift across repos, mutable default arguments, dead imports.

 Major Findings Inventory

 The Explore sweeps surfaced ~30 issues. The list below is the curated set that rises to "major finding" — each becomes one report. Minor findings
 get folded into the most relevant major as sub-points so the deliverable stays focused.

 Severity legend: C = critical (security or correctness), H = high (architectural debt that blocks Entrega 3), M = medium (consistency / hygiene), L
  = low (style / nit-but-worth-mentioning-for-interns). Severity also informs report ordering in the executive summary.

 ┌─────┬─────────┬───────────────────────────────────────────┬─────┬────────────────────────────────────────────────────────────────────────────┐
 │  #  │  Code   │                   Title                   │ Sev │                                Key evidence                                │
 ├─────┼─────────┼───────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────────┤
 │ 1   │ REST-01 │ Verbs in URLs and ad-hoc state-transition │ H   │ subastas.py:43 (/aceptar), subastas.py:107 (/ofertar), publicaciones.py:39 │
 │     │         │  endpoints                                │     │  (/mias)                                                                   │
 ├─────┼─────────┼───────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────────┤
 │ 2   │ REST-02 │ Unauthenticated endpoints leak data       │ C   │ admin.py:7, subastas.py:15, figuritas.py:10, usuarios.py:86 (/reputacion)  │
 ├─────┼─────────┼───────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────────┤
 │ 3   │ REST-03 │ Inconsistent response envelopes and       │ M   │ figuritas.py:49 (DELETE → 200), usuarios.py:24,62,75,99,114 (wrapped       │
 │     │         │ implicit/incorrect status codes           │     │ objects), missing status_code=200 across most GETs                         │
 ├─────┼─────────┼───────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────────┤
 │ 4   │ REST-04 │ CORS wildcard with credentials + no       │ M   │ main.py:10-16, all collection GETs (album, publicaciones, intercambios,    │
 │     │         │ versioning/pagination/caching strategy    │     │ subastas, figuritas)                                                       │
 ├─────┼─────────┼───────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────────┤
 │ 5   │ ARCH-01 │ Layer leakage: routers bypass services,   │ H   │ Router→repo: intercambios.py:29-50. Service→HTTP:                          │
 │     │         │ services raise HTTPException              │     │ intercambio_service.py:10,13,19,28,...                                     │
 ├─────┼─────────┼───────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────────┤
 │     │         │ Repository pattern inconsistencies        │     │ len(_db)+1 in figurita_repo.py:52, intercambio_repo.py:15,                 │
 │ 6   │ ARCH-02 │ (interface, ID gen, global names)         │ H   │ oferta_repo.py:5 vs _next_id in album_repo.py:41-43; crear vs create; _db  │
 │     │         │                                           │     │ vs _db_<entity>                                                            │
 ├─────┼─────────┼───────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────────┤
 │ 7   │ ARCH-03 │ Anemic dict-returning repos; no domain    │ H   │ All repos return list[dict] / dict; schemas/ doubles as domain; e.g.       │
 │     │         │ model layer                               │     │ usuario_repo.py:16-25                                                      │
 ├─────┼─────────┼───────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────────┤
 │ 8   │ ARCH-04 │ Schema package: file-name drift and       │ M   │ _sch.py suffix on 4 files, bare on 5; figurita.py:12-22 Response = Create  │
 │     │         │ conflated Create/Response                 │     │ + ids                                                                      │
 ├─────┼─────────┼───────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────────┤
 │ 9   │ SEC-01  │ Token model: timing-attack-comparable,    │ C   │ usuario_repo.py:24 u["token"] == token; no exp/iat/sub; no revocation;     │
 │     │         │ non-rotatable, unscoped, unsigned         │     │ documented in PDF as "minimal" but the comparison itself is fixable today  │
 ├─────┼─────────┼───────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────────┤
 │     │         │ Inconsistent error idiom + no global      │     │ intercambio_service.py raises HTTPException, subasta_service.py:31,34,...  │
 │ 10  │ ERR-01  │ handler + ad-hoc string-matching in       │ H   │ raises ValueError/PermissionError, then subastas.py:57-59 matches on       │
 │     │         │ routers                                   │     │ substring "no encontrada"                                                  │
 ├─────┼─────────┼───────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────────┤
 │     │         │ Tests couple to private repo internals;   │     │ tests/conftest.py:23-31 (album_repo._db.clear() etc.),                     │
 │ 11  │ TEST-01 │ CI lacks lint/type-check/coverage         │ M   │ tests/integration/conftest.py:23,28, .github/workflows/backend-tests.yml   │
 │     │         │                                           │     │ runs only pytest                                                           │
 ├─────┼─────────┼───────────────────────────────────────────┼─────┼────────────────────────────────────────────────────────────────────────────┤
 │     │         │ Magic strings for domain states; Pydantic │     │ intercambio_repo.py:20 stores "pendiente", intercambio_service.py:262,     │
 │ 12  │ PY-01   │  validation duplicated in services        │ M   │ admin_service.py:30; publicacion_service.py:15-16 re-validates a           │
 │     │         │                                           │     │ constraint already expressible in the schema                               │
 └─────┴─────────┴───────────────────────────────────────────┴─────┴────────────────────────────────────────────────────────────────────────────┘

 Sub-findings folded into the above (so they don't get lost):
 - Naive vs aware datetime — OK (subasta_service.py:12 uses datetime.now(timezone.utc)); mention as a positive in ARCH-02 or PY-01.
 - Dead import (usuarios.py:7 usuario_repo) — PY-01.
 - Duplicate obtener_sugerencias (publicaciones.py:49 and usuarios.py:73) — REST-01.
 - realizar_intercambio_aceptado god function (intercambio_service.py:149-233) — ARCH-01.
 - No repo.reset() API — TEST-01.
 - No global FastAPI exception handler — ERR-01.

 Report Template (Medium Depth)

 Each finding is one Markdown file under docs/francobatta/reports/backend/. Filename pattern: {CODE}-{kebab-title}.md, e.g.
 REST-01-verbs-in-urls.md. Each file follows this structure (~150-300 lines):

 # {CODE} — {Title}

 **Severity:** {C|H|M|L}  ·  **Area:** {REST | Architecture | Security | Errors | Tests | Python}  ·  **Effort:** {S|M|L}

 ## Diagnosis
 Two or three paragraphs. What is happening, with concrete file:line evidence (links or inline). Why it matters in terms an intern can act on —
 connect to a named principle (Richardson level, Repository pattern, OWASP item, PEP, etc.).

 ## Evidence
 A short list of file:line citations. One line each. No prose; this is the receipt.

 ## Recommendation
 One named approach. Not a menu — the recommendation. One short code sample showing the proposed shape (before/after fragment, ~10-20 lines). If the
  fix touches more than one file, note the others by path in a line under the sample.

 ## Why this approach
 Two or three bullets. The tradeoff against the obvious alternative (so the intern learns the reasoning, not just the rule). Connect to a
 longer-lived constraint (Entrega 3 swap, test stability, security posture).

 This matches the user's "Medium" depth choice: diagnosis + recommendation + 1 code sample, no exhaustive alternatives or step-by-step ticket
 breakdown.

 Deliverables

 docs/francobatta/reports/backend/
 ├── README.md                              ← executive summary / index
 ├── REST-01-verbs-in-urls.md
 ├── REST-02-unauth-endpoints.md
 ├── REST-03-response-envelopes-status-codes.md
 ├── REST-04-cors-versioning-pagination.md
 ├── ARCH-01-layer-leakage.md
 ├── ARCH-02-repository-pattern.md
 ├── ARCH-03-anemic-repos-no-domain-model.md
 ├── ARCH-04-schema-package.md
 ├── SEC-01-token-model.md
 ├── ERR-01-error-handling.md
 ├── TEST-01-tests-and-ci.md
 └── PY-01-magic-strings-and-validation.md

 README.md (executive summary) contains:
 - A 3-paragraph "state of the backend" preamble (what's good, what's the biggest debt, what to do first).
 - A table identical to the inventory above (#, code, title, severity, one-line synopsis, link to the report).
 - A "How to read these reports" note for the interns (severity legend, effort legend, the template structure).

 No remediation roadmap doc — the severity column in the index serves that purpose and the user opted out of the standalone roadmap.

 Execution Order

 When the user approves and we leave plan mode, the implementation will follow this order to keep the deliverable reviewable in chunks:

 1. Scaffold docs/francobatta/reports/backend/ with README.md (header + empty table) so the index grows as reports land.
 2. Write the four critical/high security & layering reports first — these are the ones most likely to shape Entrega 3 decisions: SEC-01, REST-02,
 ARCH-01, ARCH-02. Update the index row as each lands.
 3. Write the remaining HIGH reports: REST-01, ARCH-03, ERR-01.
 4. Write the MEDIUM reports: REST-03, REST-04, ARCH-04, TEST-01, PY-01.
 5. Polish the executive summary — once all rows are filled, write the preamble paragraphs.

 Critical files to keep referenced while writing (anchors that recur in many reports):
 - backend/app/main.py (CORS, router registration, no global error handler)
 - backend/app/dependencies.py (auth dependency)
 - backend/app/repositories/usuario_repo.py (token comparison)
 - backend/app/services/intercambio_service.py (HTTPException-in-business-logic exemplar, god function)
 - backend/app/services/subasta_service.py (domain-exception-but-leaky exemplar)
 - backend/app/routers/subastas.py (verbs in URL, string-matching error translation)
 - backend/tests/conftest.py + backend/tests/integration/conftest.py (private-globals coupling)
 - .github/workflows/backend-tests.yml (CI gaps)

 Verification

 The deliverable is documentation, not code, so verification is editorial:

 - Self-check, per report: every file:line citation resolves to the line claimed (open the file at that line and confirm); the code sample compiles
 in a Python REPL or as a Pydantic snippet; the "Why this approach" addresses at least one tradeoff explicitly (no "always do X").
 - Cross-report consistency: no two reports recommend conflicting fixes (e.g., if SEC-01 introduces an exception type, ERR-01's snippet uses it).
 One pass at the end to reconcile.
 - Index completeness: every report listed in the inventory exists and is linked from README.md; every report links back to README.md; severity in
 the file header matches severity in the index.
 - Intern-readability spot check: read REST-01 and SEC-01 cold, pretend you're a 2nd-year student — can you act on them without asking a question?
 If not, expand the "Why this approach" bullets.

 Optional but recommended after the reports are in: open a draft PR against the repo with the docs folder so the team can comment inline. The user
 has not asked for this — do not push without explicit approval.
 