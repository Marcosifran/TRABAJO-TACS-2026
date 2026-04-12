# 🏆 TP TACS 2026-C1: Plataforma de Intercambio de Figuritas

![React](https://img.shields.io/badge/React_19-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python_3.12-14354C?style=for-the-badge&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)
[![Backend Tests](https://github.com/Marcosifran/TRABAJO-TACS-2026/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/Marcosifran/TRABAJO-TACS-2026/actions/workflows/backend-tests.yml)

WebApp para la materia Tecnologías Avanzadas en Construcción de Software (TACS). Permite que los usuarios puedan publicar figuritas repetidas, registrar faltantes, y gestionar intercambios.

## Estado de Entregas

- [] **Entrega 1:** Esqueleto de aplicación, URLs REST definidas y estado en memoria mediante Docker.
- [ ] **Entrega 2:** (Próximamente)
- [ ] **Entrega 3:** (Próximamente)

## Arquitectura y Tecnologías

Proyecto diseñado bajo una arquitectura orientada a microservicios y completamente Dockerizada para asegurar portabilidad en cualquier entorno.

- **Frontend:** React 19 + Vite (Node 20 LTS)
- **Backend:** FastAPI (Python 3.12)
- **Persistencia:** Estado en memoria (Para la Entrega 1).
- **Orquestación:** Docker Compose V2

## Requisitos Previos

Para ejecutar este proyecto de forma local, es necesario tener instalado el motor de contenedores:

- [Docker Desktop o CLI](https://www.docker.com/products/docker-desktop/) (o Docker Engine) activo y corriendo.

## Cómo ejecutar el proyecto (Modo Local)

1. Clonar el repositorio:
   ```bash
   git clone [https://github.com/Marcosifran/TRABAJO-TACS-2026.git](https://github.com/Marcosifran/TRABAJO-TACS-2026.git)
   cd TRABAJO-TACS-2026
   ```

2. Crear el archivo `.env` a partir del ejemplo y completarlo con tokens reales (ver sección [Identificación de Usuarios](#identificación-de-usuarios)):
   ```bash
   cp .env.example .env
   # Editar .env y completar USER_1_TOKEN y USER_2_TOKEN
   ```

3. Ejecutar el proyecto:
   ```bash
   docker compose up --build
   ```

4. Acceder a la aplicación:
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000
   - Documentación interactiva (Swagger): http://localhost:8000/docs

## Modificar el código

```bash
git checkout -b feature/nombre-del-cambio
git push origin feature/nombre-del-cambio
```

---

## Identificación de Usuarios

El TP no requiere autenticación completa, pero los usuarios deben poder diferenciarse para atacar los casos de uso. La solución implementada usa **tokens fijos por usuario** distribuidos fuera del repositorio.

### Cómo funciona

Cada request a un endpoint protegido debe incluir el header `X-User-Token` con el token correspondiente al usuario. El backend resuelve la identidad a partir de ese token sin necesidad de login.

```
POST /api/v1/figuritas/
X-User-Token: <token-del-usuario>
```

Si el header está ausente o el token no corresponde a ningún usuario, el backend responde `401 Unauthorized`.

### Configuración del .env

Los tokens se definen en un archivo `.env` en la raíz del proyecto:

```env
USER_1_TOKEN=<uuid-del-usuario-1>
USER_2_TOKEN=<uuid-del-usuario-2>
```

**Cómo generar un token de ejemplo para el .env:**
```bash
# Python
python -c "import uuid; print(uuid.uuid4())"
