# 🏆 TP TACS 2026-C1: Plataforma de Intercambio de Figuritas

![React](https://img.shields.io/badge/React_19-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python_3.12-14354C?style=for-the-badge&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)

WebApp para la materia Tecnologías Avanzadas en Construcción de Software (TACS). Permite que los usuarios puedan publicar figuritas repetidas, registrar faltantes, y gestionar intercambios.

## Estado de Entregas

- [x] **Entrega 1:** Esqueleto de aplicación, URLs REST definidas y estado en memoria mediante Docker.
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

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (o Docker Engine) activo y corriendo.

## Cómo ejecutar el proyecto (Modo Local)

1. Clonar el repositorio:
   ```bash
   git clone [https://github.com/Marcosifran/TRABAJO-TACS-2026.git](https://github.com/Marcosifran/TRABAJO-TACS-2026.git)
   cd TRABAJO-TACS-2026
   ```
2. Ejecutar el proyecto:
   ```bash
   docker compose up --build
   ```
3. Acceder a la aplicación:
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000
