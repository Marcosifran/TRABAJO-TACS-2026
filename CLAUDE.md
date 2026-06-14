# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

WebApp for the TACS course (UTN) for trading "figuritas" (collectible stickers): users register an album, mark missing stickers, publish duplicates, propose direct trades, and run auctions. Spanish is the working language for code identifiers, comments, commit messages, and user-facing strings.

## Stack & Layout

- **Backend** — FastAPI (Python 3.12), under `backend/app/`. All state is held in **in-memory Python lists** inside the `repositories/` modules — there is no database yet. Restarting the backend wipes everything.
- **Frontend** — React 19 + Vite + Tailwind, under `frontend/src/`. Router via `react-router-dom`. State via React Context (`ThemeContext`, `AuthContext`).
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

Tests don't need any auth env vars: the integration fixtures mint real JWTs for the two seed users (`backend/tests/integration/conftest.py`). They run against the **test** database — `TEST_MONGODB_URL` / `TEST_MONGODB_DB_NAME` from the root `.env`, falling back to `mongodb://localhost:27017` / `mundial_figuritas_db` (what CI uses). The suite drops that database on teardown, so never point it at the dev/prod DB.

**Frontend (inside `frontend/`):**

```bash
npm install
npm run dev          # vite dev server :5173 (also reads ../.env, see envDir in vite.config.js)
npm run build
npm run lint         # eslint
```

There are no frontend tests configured.

## Authentication model

Auth is **JWT-based**. `POST /auth/login` (email + password) and `POST /auth/register` are public and return `{access_token, token_type: "bearer", usuario}` (`app/routers/auth.py` → `app/services/auth_service.py`). Passwords are bcrypt-hashed (`app/core/security_passwords.py`). Tokens are signed/verified in `app/security.py` with `JWT_SECRET` from the env; the JWT subject (`sub`) is the integer user id.

`app/dependencies.py::get_current_user` is the FastAPI dependency every protected endpoint uses: it reads `Authorization: Bearer <jwt>`, verifies it, resolves the id via `usuario_repo.get_by_id`, and returns the user dict or raises 401 (422 if the header is missing). There is **no** legacy `X-User-Token` fallback anymore.

Two seed users live in memory (`backend/app/repositories/usuario_repo.py`): `marcos@utn` (id 1, admin) and `jeronimo@utn` (id 2), both with password `SEED_USER_PASSWORD` (default `figuswap123`). Registered users are persisted in the Mongo `usuarios` collection.

On the frontend, `AuthContext` holds `{ user, users, token }`, exposes `login` / `register` / `logout`, and stores the JWT in `sessionStorage` under `figuswap-token`. `api/client.js::apiFetch` reads that key and injects `Authorization: Bearer <jwt>` on every request; a 401 from a non-`/auth/` route dispatches a `figuswap:unauthorized` event that logs the user out.

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
JWT_SECRET=<long random secret>          # signs/verifies JWTs
SEED_USER_PASSWORD=figuswap123           # password for the two seed users
MONGODB_URL=<mongo connection string>
MONGODB_DB_NAME=mundial_figuritas_db
TEST_MONGODB_URL=<mongo for tests>       # optional; defaults to localhost
TEST_MONGODB_DB_NAME=mundial_figuritas_test_db
```

`.env.example` documents the format. There are no per-user token env vars anymore — users authenticate via `POST /auth/login`.
