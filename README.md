# 🏆 TP TACS 2026-C1: Plataforma de Intercambio de Figuritas

![React](https://img.shields.io/badge/React_19-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python_3.12-14354C?style=for-the-badge&logo=python&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)
[![Backend Tests](https://github.com/Marcosifran/TRABAJO-TACS-2026/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/Marcosifran/TRABAJO-TACS-2026/actions/workflows/backend-tests.yml)

WebApp para la materia Tecnologías Avanzadas en Construcción de Software (TACS). Permite que los usuarios puedan publicar figuritas repetidas, registrar faltantes, y gestionar intercambios.

## Arquitectura y Tecnologías

Proyecto diseñado bajo una arquitectura orientada a microservicios y completamente Dockerizada para asegurar portabilidad en cualquier entorno.

- **Frontend:** React 19 + Vite (Node 20 LTS)
- **Backend:** FastAPI (Python 3.12)
- **Persistencia:** MongoDB (PyMongo)
- **Orquestación:** Docker Compose V2

## Requisitos Previos

Para ejecutar este proyecto de forma local, es necesario tener instalado el motor de contenedores:

- [Docker Desktop o CLI](https://www.docker.com/products/docker-desktop/) (o Docker Engine) activo y corriendo.

## Cómo ejecutar el proyecto (Modo Local)

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/Marcosifran/TRABAJO-TACS-2026.git
   cd TRABAJO-TACS-2026
   ```

2. Crear el archivo `.env` a partir del ejemplo y completarlo (ver secciones siguientes):
   ```bash
   cp .env.example .env
   ```

3. Ejecutar el proyecto:
   ```bash
   docker compose up --build
   ```
   Este comando levanta el backend (puerto 8000), el frontend (puerto 5173) **y MongoDB** (puerto 27017) en contenedores. No se requiere ninguna instalación adicional.

4. Acceder a la aplicación:
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000
   - Documentación interactiva (Swagger): http://localhost:8000/docs

---

## Autenticación

La app usa **autenticación JWT**. Los usuarios se registran (`POST /api/v1/auth/register`) o
inician sesión (`POST /api/v1/auth/login`) con email y contraseña, y reciben un `access_token`.

### Cómo funciona

Cada request a un endpoint protegido debe incluir el header `Authorization: Bearer <jwt>` con el
token devuelto por el login. El backend verifica la firma del JWT y resuelve la identidad del
usuario a partir del `sub` (id) del token.

```
POST /api/v1/auth/login        →  { "access_token": "<jwt>", "token_type": "bearer", "usuario": {...} }

POST /api/v1/figuritas/
Authorization: Bearer <jwt>
```

Si el header está ausente el backend responde `422`; si el token es inválido o expiró, `401 Unauthorized`.

### Usuarios sembrados (para login rápido)

Para no tener que registrarse, la app trae dos usuarios demo ya cargados. Ambos usan la contraseña
definida en `SEED_USER_PASSWORD` (por defecto `figuswap123`):

| Email          | Contraseña    | Rol            |
| -------------- | ------------- | -------------- |
| `marcos@utn`   | `figuswap123` | Admin          |
| `jeronimo@utn` | `figuswap123` | Usuario normal |

Ejemplo de login:

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"marcos@utn","password":"figuswap123"}'
```

---

## Configuración del archivo `.env`

Copiar `.env.example` como `.env` en la raíz del proyecto y completar los valores:

```env
# Autenticación JWT
JWT_SECRET=<secreto-aleatorio-largo>
SEED_USER_PASSWORD=figuswap123

# MongoDB
MONGODB_URL=<connection-string>
MONGODB_DB_NAME=mundial_figuritas_db

# Base de datos para tests (opcional; por defecto localhost)
TEST_MONGODB_URL=<connection-string>
TEST_MONGODB_DB_NAME=mundial_figuritas_test_db
```

**Cómo generar el `JWT_SECRET`:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Opción A — MongoDB local con Docker (recomendado para desarrollo)

Al ejecutar `docker compose up`, el servicio `mongodb` se levanta automáticamente. Solo hace falta dejar la variable con el nombre del servicio como host:

```env
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DB_NAME=mundial_figuritas_db
```

> Si corrés el backend **fuera** de Docker (ej: `uvicorn` directo), usá `localhost` en vez de `mongodb`:
> ```env
> MONGODB_URL=mongodb://localhost:27017
> ```

### Opción B — MongoDB Atlas (nube)

1. Crear un cluster en [MongoDB Atlas](https://www.mongodb.com/atlas).
2. En **Database Access**, crear un usuario con contraseña.
3. En **Network Access**, agregar tu IP (o `0.0.0.0/0` para pruebas).
4. En el cluster, hacer click en **Connect → Drivers**, copiar el connection string y pegarlo en el `.env`:

```env
MONGODB_URL=mongodb+srv://<usuario>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=mundial_figuritas_db
```

> Al usar Atlas, el servicio `mongodb` del docker-compose no se usa. Solo es necesario el contenedor del backend.

---

## Ejecución de Tests

Los tests usan una base de datos dedicada (`mundial_figuritas_test`) que se crea y destruye automáticamente durante la sesión. La URL de Mongo se resuelve así:

- Si definís `TEST_MONGODB_URL` en el entorno, pytest usa ese valor.
- Si corrés dentro de Docker Compose, usa `mongodb://mongodb:27017`.
- Si corrés en el host y `mongodb` no resuelve, cae a `mongodb://localhost:27017`.

Requisito: tener MongoDB corriendo en el host o en Docker Compose. Si querés ejecutar pytest en la máquina local con el contenedor de Mongo levantado, podés usar el override explícito.

```bash
# Levantar solo MongoDB (si no se quiere correr el stack completo)
docker compose up mongodb -d

cd backend
pip install -r requeriments.txt
TEST_MONGODB_URL=mongodb://localhost:27017 pytest
```

---

## Distribución de claves al equipo

Las claves **nunca deben subirse al repositorio**. El `.env` está en `.gitignore`. Para compartirlas con el equipo:

- Compartir el archivo `.env` por un canal seguro fuera del repo (mensaje directo, vault, etc.).
- En CI/CD (GitHub Actions), cargarlas como **Repository Secrets** y referenciarlas en el workflow.

---

## Uso de Inteligencia Artificial

Durante el desarrollo se utilizaron herramientas de IA (Claude Code / Claude API de Anthropic) principalmente para:

- **Exploración y revisión de código:** análisis del estado de la migración a MongoDB, detección de issues en la capa de repositorios y tests.
- **Implementación asistida:** migración del sistema de IDs a ObjectId de MongoDB, corrección de fixtures de tests, configuración del docker-compose.
- **Consultas de diseño:** validación de decisiones de arquitectura (estrategia de IDs, aislamiento de base de datos en tests, etc.).

Todo el código producido fue revisado, validado y es responsabilidad del equipo.
