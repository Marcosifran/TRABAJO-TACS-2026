from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import settings
from app.core.exceptions import register_exceptions_handlers
from app.core.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, album, publicaciones, usuarios, intercambios, subastas, admin, maestro
from app.services import maestro_service, stats_service

_scheduler = None


def _inicializar_scheduler():
    """Inicia el scheduler de actualización de estadísticas"""
    global _scheduler
    _scheduler = BackgroundScheduler()

    # Actualizar métricas globales cada 5 minutos
    _scheduler.add_job(
        stats_service.actualizar_global,
        "interval",
        minutes=5,
        id="stats_global",
        replace_existing=True,
    )

    # Actualizar tendencias cada 30 minutos
    _scheduler.add_job(
        stats_service.actualizar_tendencias,
        "interval",
        minutes=30,
        id="stats_tendencias",
        replace_existing=True,
    )

    # Actualizar figuritas cada 30 minutos
    _scheduler.add_job(
        stats_service.actualizar_figuritas,
        "interval",
        minutes=30,
        id="stats_figuritas",
        replace_existing=True,
    )

    # Actualizar usuarios cada 30 minutos
    _scheduler.add_job(
        stats_service.actualizar_usuarios,
        "interval",
        minutes=30,
        id="stats_usuarios",
        replace_existing=True,
    )

    # Actualizar mercado cada hora
    _scheduler.add_job(
        stats_service.actualizar_mercado,
        "interval",
        hours=1,
        id="stats_mercado",
        replace_existing=True,
    )

    # Actualizar reputación cada 30 minutos
    _scheduler.add_job(
        stats_service.actualizar_reputacion,
        "interval",
        minutes=30,
        id="stats_reputacion",
        replace_existing=True,
    )

    # Actualizar performance cada hora
    _scheduler.add_job(
        stats_service.actualizar_performance,
        "interval",
        hours=1,
        id="stats_performance",
        replace_existing=True,
    )

    # Actualizar histórico cada hora
    _scheduler.add_job(
        stats_service.actualizar_historico,
        "interval",
        hours=1,
        id="stats_historico",
        replace_existing=True,
    )

    # Guardar snapshot diario a medianoche
    _scheduler.add_job(
        stats_service.guardar_snapshot_diario,
        "cron",
        hour=0,
        minute=0,
        id="stats_snapshot_daily",
        replace_existing=True,
    )

    _scheduler.start()


def _detener_scheduler():
    """Detiene el scheduler"""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown()


@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_to_mongo()
    maestro_service.inicializar()
    _inicializar_scheduler()
    # Realizar una actualización inicial
    stats_service.actualizar_global()
    stats_service.actualizar_tendencias()
    stats_service.actualizar_figuritas()
    stats_service.actualizar_usuarios()
    stats_service.actualizar_reputacion()
    stats_service.actualizar_performance()
    yield
    _detener_scheduler()
    close_mongo_connection()

# Creamos la aplicación FastAPI. El título y versión los toma desde config.py
app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

# Excepciones
register_exceptions_handlers(app)

# Seteamos CORS como middleware para permitir solicitudes desde cualquier origen.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registramos los routers con el prefijo /api/v1.
app.include_router(auth.router, prefix="/api/v1")
app.include_router(album.router, prefix="/api/v1")
app.include_router(publicaciones.router, prefix="/api/v1")
app.include_router(usuarios.router, prefix="/api/v1")
app.include_router(intercambios.router, prefix="/api/v1")
app.include_router(subastas.router, prefix="/api/v1")
app.include_router(admin.router,    prefix="/api/v1")
app.include_router(maestro.router,  prefix="/api/v1")

# Endpoint root para chequear estado del server.
@app.get("/")
def read_root():
    return {"Hello": "World"}
