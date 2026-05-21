# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

WebApp for the TACS course (UTN) for trading "figuritas" (collectible stickers): users register an album, mark missing stickers, publish duplicates, propose direct trades, and run auctions. Spanish is the working language for code identifiers, comments, commit messages, and user-facing strings.

## Stack & Layout

- **Backend** — FastAPI (Python 3.12), under `backend/app/`. All state is held in **in-memory Python lists** inside the `repositories/` modules — there is no database yet. Restarting the backend wipes everything.
- **Frontend** — React 19 + Vite + Tailwind, under `frontend/src/`. Router via `react-router-dom`. State via React Context (`ThemeContext`, `UserContext`).
- **Orchestration** — Docker Compose. Both services bind-mount the source for hot reload; the frontend container has an anonymous volume on `/app/node_modules` so the host's missing/different `node_modules` doesn't shadow the container's.
- **`seed.py`** — standalone script at the repo root that pumps demo data into a running backend via HTTP (reads tokens from `.env`).

## Commands

Run everything via Docker Compose from the repo root:

```bash
docker compose up --build              # full stack: backend :8000, frontend :5173
docker compose up backend              # backend only
python seed.py                         # populate demo data (requires running backend + .env)
python seed.py --url http://localhost:8000
```

**Backend (inside `backend/`):**

```bash
pip install -r requeriments.txt        # note misspelling — file is "requeriments.txt"
uvicorn app.main:app --reload          # local run without docker
pytest tests/ -v                       # all tests
pytest tests/integration/test_subastas.py -v          # single file
pytest tests/integration/test_subastas.py::test_xxx   # single test
```

Tests require `USER_1_TOKEN` and `USER_2_TOKEN` in the environment (CI sets them to `test-token-user1` / `test-token-user2`). Locally they're read from the root `.env`.

**Frontend (inside `frontend/`):**

```bash
npm install
npm run dev          # vite dev server :5173 (also reads ../.env, see envDir in vite.config.js)
npm run build
npm run lint         # eslint
```

There are no frontend tests configured.

## Authentication model

There is **no login**. The backend identifies users by a fixed `X-User-Token` header resolved against the seeded list in `backend/app/repositories/usuario_repo.py` (two hardcoded users whose tokens come from `USER_1_TOKEN` / `USER_2_TOKEN` env vars). `app/dependencies.py::get_current_user` is the FastAPI dependency that all protected endpoints use; it returns the user dict or raises 401.

On the frontend, `UserContext` holds the active user and writes the corresponding token into `sessionStorage` under `figuswap-token`. `api/client.js::apiFetch` reads that key and injects it as `X-User-Token` on every request. Switching the active user from the UI updates `sessionStorage` and re-renders. The frontend reads tokens from Vite env vars `VITE_USER_1_TOKEN` / `VITE_USER_2_TOKEN` (which must match the backend `USER_*_TOKEN` values — both halves live in the same root `.env`).

When adding a new protected endpoint, declare `usuario: dict = Depends(get_current_user)` and trust `usuario["id"]` — do not accept a user id from the request body.

## Backend architecture

Strict 4-layer split — keep responsibilities in their own files:

- `routers/` — FastAPI route declarations. Parse request bodies into Pydantic schemas, call a service, return the result. No business logic here. Routers are registered in `app/main.py` with the `/api/v1` prefix.
- `services/` — Business rules, validation, cross-repo coordination. Raise `HTTPException` for user-facing errors with Spanish `detail` messages (see `intercambio_service.py` for the established style).
- `repositories/` — In-memory CRUD. Each repo owns a module-level list (e.g. `_db`, `_db_subastas`) and a `_next_id` counter where applicable. **Tests reach into these module globals to reset state** (see `tests/conftest.py`), so any new repo must follow the same naming convention or the autouse fixture won't clean it.
- `schemas/` — Pydantic models for request/response shapes. Files end in `_sch.py` for the newer ones; older ones use the entity name only (`figurita.py`, `oferta.py`).

When adding a new resource (e.g. `comentarios`), create one file in each of the four layers plus an entry in `main.py`'s `include_router` list, and add the repo's reset calls to `tests/conftest.py::limpiar_db`.

## Testing conventions

- `tests/conftest.py` defines an `autouse=True` fixture that clears every in-memory repo before and after each test. New repos must be added there or tests will leak state.
- `tests/integration/conftest.py` provides `client` (a `TestClient`), `token_user1`, `token_user2`, and sample payload fixtures. Integration tests hit the real FastAPI app via `TestClient` — no mocking.
- Unit tests go in `tests/unit/`, integration in `tests/integration/`. The CI workflow (`.github/workflows/backend-tests.yml`) runs the full `pytest tests/` on every push and PR.

## Frontend architecture

- API calls are grouped by domain in `src/api/*.js`, all built on top of `apiFetch` from `api/client.js`. The base URL is `VITE_API_URL` or `http://localhost:8000/api/v1`.
- `vite.config.js` sets `envDir: '../'` so Vite reads the **root** `.env` (not `frontend/.env`). When adding a frontend-visible env var, prefix it with `VITE_` and put it in the root `.env` / `.env.example`.
- Routes are declared in `App.jsx`; pages live in `src/pages/`, reusable building blocks in `src/components/` (with a `components/ui/` subfolder for primitives).

## Environment variables

The root `.env` is shared by both services (see `docker-compose.yml` `env_file: .env` on both). It needs:

```
USER_1_TOKEN=<uuid>
USER_2_TOKEN=<uuid>
VITE_USER_1_TOKEN=<same uuid as USER_1_TOKEN>
VITE_USER_2_TOKEN=<same uuid as USER_2_TOKEN>
```

The backend/frontend halves must match or auth requests will 401. `.env.example` documents the format.
