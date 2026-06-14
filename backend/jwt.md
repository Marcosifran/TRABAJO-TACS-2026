# Plan: Login con JWT y soporte multi-usuario

## Estado actual

- `backend/app/security.py` ya tiene `create_access_token` / `verify_access_token` (PyJWT, `settings.jwt_secret`/`jwt_algorithm`/`jwt_exp_minutes`), pero **nada las usa todavía**.
- `backend/app/dependencies.py::get_current_user` ya acepta `Authorization: Bearer <jwt>` (resuelve `sub` contra `usuario_repo.get_by_id`) y mantiene `X-User-Token` como fallback temporal.
- `usuario_repo._db_usuarios` tiene 2 usuarios hardcodeados con `token` = UUID fijo desde `.env` (`USER_1_TOKEN`/`USER_2_TOKEN`). No hay contraseña ni endpoint de login.
- Frontend: `UserContext` define un array fijo `USERS` (2 usuarios) con los UUID de Vite, y un "switcher" que escribe el token en `sessionStorage['figuswap-token']`. `apiFetch` siempre manda `X-User-Token`. No hay página de login ni rutas protegidas.

## Objetivo

Reemplazar el esquema de "token UUID fijo + selector de usuario" por login real:
- Usuarios con email + contraseña (hash), guardados en Mongo.
- `POST /auth/login` devuelve un JWT (usa `create_access_token` ya existente).
- Frontend con página de Login, `AuthContext` que guarda el JWT, manda `Authorization: Bearer`, y rutas protegidas redirigen a `/login` si no hay sesión.
- Soporte para registrar nuevos usuarios (no solo los 2 seed).

---

## Fase 1 — Backend: usuarios con password + endpoint de login

1. **`backend/requeriments.txt`**: agregar `passlib[bcrypt]` (o `bcrypt` directo) para hashing de contraseñas.

2. **`backend/app/repositories/usuario_repo.py`**:
   - Agregar campo `password_hash` a `_db_usuarios` (los 2 seed users, hash de una password de desarrollo, ej. leída de `.env` como `SEED_USER_PASSWORD`).
   - Nueva función `get_by_email(email: str) -> dict | None` (busca en `_db_usuarios` + colección `usuarios` de Mongo).
   - Nueva función `create_usuario(nombre, email, password_hash) -> dict` que inserta en la colección Mongo `usuarios` con un `id` autoincremental (similar a otros repos con `_next_id`, ver convención de `tests/conftest.py::limpiar_db` para registrar el reset).
   - Mantener `get_by_token` solo como soporte legacy (ver Fase 4).

3. **`backend/app/core/security_passwords.py`** (nuevo, o agregar a `security.py`):
   - `hash_password(plain: str) -> str` y `verify_password(plain: str, hashed: str) -> bool` usando passlib/bcrypt.

4. **`backend/app/schemas/auth_sch.py`** (nuevo):
   - `LoginRequest { email: str, password: str }`
   - `RegisterRequest { nombre: str, email: str, password: str }`
   - `TokenResponse { access_token: str, token_type: str = "bearer", usuario: UsuarioResponse }`

5. **`backend/app/services/auth_service.py`** (nuevo):
   - `login(data: LoginRequest) -> TokenResponse`: busca por email, verifica password con `verify_password`, si falla → `HTTPException(401, "Credenciales inválidas")`. Si ok, `create_access_token(subject=usuario["id"], email=usuario["email"])`.
   - `register(data: RegisterRequest) -> TokenResponse`: valida que el email no exista (`DomainConflictError`/409 si existe), crea usuario con `hash_password`, devuelve token igual que login.

6. **`backend/app/routers/auth.py`** (nuevo):
   - `router = APIRouter(prefix="/auth", tags=["Auth"])` (sin `Depends(get_current_user)`).
   - `POST /auth/login` → `auth_service.login`.
   - `POST /auth/register` → `auth_service.register`, 201.

7. **`backend/app/main.py`**: registrar `auth.router` en `include_router`.

8. **`backend/app/schemas/usuario.py`**: sin cambios (sigue sin exponer password/token).

9. **`tests/conftest.py`**: agregar reset de la nueva colección/lista de usuarios creados dinámicamente (si se usa lista en memoria) o limpiar la colección Mongo `usuarios` en `limpiar_db`.

10. **Tests nuevos** (`tests/integration/test_auth.py`):
    - login con credenciales válidas devuelve JWT y `usuario`.
    - login con password incorrecta → 401.
    - register crea usuario y permite login posterior.
    - register con email duplicado → 409.
    - acceso a endpoint protegido con el JWT obtenido funciona (`Authorization: Bearer`).

---

## Fase 2 — Backend: limpiar `dependencies.py` (JWT como único mecanismo)

- Quitar el branch de `X-User-Token` de `get_current_user` (o dejarlo solo detrás de un flag de test, ver Fase 4).
- Actualizar docstring/comentario que dice "Mantiene compatibilidad temporal con X-User-Token".
- Revisar todos los routers: ya usan `Depends(get_current_user)`, no requieren cambios de firma.

---

## Fase 3 — Frontend: AuthContext + página de Login

1. **`frontend/src/context/AuthContext.jsx`** (nuevo, reemplaza `UserContext`):
   - Estado: `{ token, usuario }`, persistido en `sessionStorage` (`figuswap-token`, `figuswap-usuario`).
   - `login(email, password)`: llama `POST /auth/login`, guarda token + usuario.
   - `register(nombre, email, password)`: llama `POST /auth/register`, guarda token + usuario (auto-login).
   - `logout()`: limpia `sessionStorage` y estado.
   - Exporta `useAuth()`.

2. **`frontend/src/api/client.js`**:
   - Cambiar `token()` para leer `figuswap-token` (mismo key, sin problema) y enviar header `Authorization: Bearer ${token}` en vez de `X-User-Token`.
   - En 401, opcional: disparar `logout()` global (vía evento o callback) para forzar vuelta a `/login`.

3. **`frontend/src/api/auth.js`** (nuevo): wrappers `loginRequest`, `registerRequest` sobre `apiFetch('/auth/login' | '/auth/register', { method: 'POST', body })`.

4. **`frontend/src/pages/LoginPage.jsx`** (nuevo):
   - Form email/password, botón "Ingresar", link a registro.
   - Usa `useAuth().login`, en éxito navega a `/`.

5. **`frontend/src/pages/RegisterPage.jsx`** (nuevo):
   - Form nombre/email/password, usa `useAuth().register`, en éxito navega a `/`.

6. **`frontend/src/App.jsx`**:
   - Reemplazar `UserProvider` por `AuthProvider`.
   - Agregar rutas `/login` y `/registro` (sin layout protegido).
   - Nuevo wrapper `RequireAuth`: si `!token`, `<Navigate to="/login" replace />`.
   - Envolver todas las rutas existentes (excepto `/login`, `/registro`) con `RequireAuth`.
   - `RequireAdmin` sigue igual pero lee `usuario.es_admin` desde `AuthContext`.

7. **Componentes que usan `useUser()`** (buscar todos los usos): `AppShell`, `ProfilePage`, header con selector de usuario, etc. Migrar a `useAuth()` y:
   - Quitar el selector "Usuario 1 / Usuario 2" (ya no aplica, login real).
   - Mostrar `usuario.nombre` / botón "Cerrar sesión" (llama `logout()` y navega a `/login`).

8. **`frontend/.env` / `.env.example`**: quitar `VITE_USER_1_TOKEN` / `VITE_USER_2_TOKEN` (ya no se usan). Documentar `SEED_USER_PASSWORD` para los usuarios demo si se mantiene Fase 1.3.

---

## Fase 4 — Migración de datos / compatibilidad

- Los 2 usuarios seed (`marcos`, `jeronimo`) necesitan email+password para poder loguearse: definir password de desarrollo fija (ej. `figuswap123`) documentada en `.env.example` como `SEED_USER_PASSWORD`, hasheada al construir `_db_usuarios`.
- **`seed.py`**: actualizar para hacer `POST /auth/login` con esas credenciales en vez de leer `USER_1_TOKEN`/`USER_2_TOKEN` directamente, y usar el JWT devuelto para las requests subsiguientes.
- **`tests/integration/conftest.py`**: los fixtures `token_user1`/`token_user2` deben obtenerse vía login (`POST /auth/login` con las credenciales seed) en lugar de leer `USER_1_TOKEN`/`USER_2_TOKEN` env vars — o, si se prioriza no romper ~100 tests existentes, generar el JWT directamente con `create_access_token(subject=1)` / `create_access_token(subject=2)` (sin pasar por HTTP), evitando reescribir cada test.
- Eliminar `USER_1_TOKEN`/`USER_2_TOKEN`/`VITE_USER_1_TOKEN`/`VITE_USER_2_TOKEN` de `.env`, `.env.example`, `docker-compose.yml` y `CLAUDE.md` (sección "Authentication model" y "Environment variables") una vez todo lo anterior esté migrado.

---

## Orden de ejecución sugerido

1. Fase 1 (backend login/register) + tests → mergeable solo, no rompe nada existente (JWT es adicional).
2. Fase 3 puntos 1-5 (AuthContext, LoginPage, RegisterPage, api/auth.js, client.js header) en paralelo, sin tocar rutas todavía.
3. Fase 3 puntos 6-7 (rutear, proteger, quitar selector) — rompe el flujo viejo, hacerlo en un solo PR.
4. Fase 4 (seed.py, conftest, limpieza de env vars) y Fase 2 (quitar `X-User-Token` del backend) al final, cuando frontend y tests ya no dependan de él.

## Riesgos / decisiones a confirmar

- ¿Se permite auto-registro abierto (`/auth/register` público) o solo admin puede crear usuarios? — el enunciado pide "login page para múltiples usuarios", se asume registro abierto.
- ¿Mantener `es_admin` asignable solo manualmente (no vía register)? Sí — `register` siempre crea `es_admin: false`.
- Password de los 2 usuarios seed: necesaria para no perder los datos de demo ya cargados por `seed.py` bajo esos `id`s 1 y 2.
