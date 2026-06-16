from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from app.services import admin_service, stats_service
from app.dependencies import get_current_user


def require_admin(usuario: dict = Depends(get_current_user)) -> dict:
    if not usuario.get("es_admin"):
        raise HTTPException(status_code=403, detail="Requiere rol de administrador")
    return usuario


router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


@router.get(
    "/estadisticas",
    responses={
        200: {"description": "Estadísticas globales de uso y actividad de la plataforma"},
    },
)
def obtener_estadisticas(
    desde: date | None = Query(None, description="Fecha inicio del período (YYYY-MM-DD)"),
    hasta: date | None = Query(None, description="Fecha fin del período (YYYY-MM-DD)"),
):
    """
    Devuelve estadísticas globales: usuarios, figuritas, intercambios y subastas.

    Sin parámetros: retorna el caché actualizado en background.
    Con desde/hasta: filtra datos crudos por fecha de creación del documento.
    """
    desde_dt = datetime(desde.year, desde.month, desde.day, tzinfo=timezone.utc) if desde else None
    hasta_dt = datetime(hasta.year, hasta.month, hasta.day, tzinfo=timezone.utc) if hasta else None
    return stats_service.obtener_estadisticas(desde=desde_dt, hasta=hasta_dt)


@router.get(
    "/estadisticas/todas",
    responses={
        200: {"description": "Todas las métricas disponibles en caché"},
    },
)
def obtener_todas_estadisticas():
    """Devuelve todas las métricas: globales, tendencias, figuritas, usuarios, mercado, reputación y performance."""
    return stats_service.obtener_todas_estadisticas()


@router.get(
    "/estadisticas/tendencias",
    responses={
        200: {"description": "Tendencias de actividad últimas 24 horas"},
    },
)
def obtener_tendencias():
    """Devuelve tendencias de actividad: nuevos usuarios, intercambios, velocidad, tasa de éxito."""
    return {
        **stats_service._stats_cache["tendencias"],
    }


@router.get(
    "/estadisticas/figuritas",
    responses={
        200: {"description": "Estadísticas de figuritas más demandadas y publicadas"},
    },
)
def obtener_estadisticas_figuritas():
    """Devuelve figuritas más demandadas y más publicadas con análisis de demanda."""
    return {
        **stats_service._stats_cache["figuritas"],
    }


@router.get(
    "/estadisticas/usuarios",
    responses={
        200: {"description": "Estadísticas de actividad de usuarios"},
    },
)
def obtener_estadisticas_usuarios():
    """Devuelve usuarios más activos e inactivos, con información de reputación."""
    return {
        **stats_service._stats_cache["usuarios"],
    }


@router.get(
    "/estadisticas/mercado",
    responses={
        200: {"description": "Métricas de salud y movimiento del mercado"},
    },
)
def obtener_estadisticas_mercado():
    """Devuelve salud del mercado, volumen de transacciones y equipos con más movimiento."""
    return {
        **stats_service._stats_cache["mercado"],
    }


@router.get(
    "/estadisticas/reputacion",
    responses={
        200: {"description": "Estadísticas de reputación global"},
    },
)
def obtener_estadisticas_reputacion():
    """Devuelve promedio global de reputación, distribución por nivel y top usuarios."""
    return {
        **stats_service._stats_cache["reputacion"],
    }


@router.get(
    "/estadisticas/performance",
    responses={
        200: {"description": "Métricas de performance del sistema"},
    },
)
def obtener_estadisticas_performance():
    """Devuelve tiempos promedio y tasas de abandono."""
    return {
        **stats_service._stats_cache["performance"],
    }


@router.get(
    "/estadisticas/historico",
    responses={
        200: {"description": "Estadísticas históricas filtradas por período"},
    },
)
def obtener_estadisticas_historico(
    periodo: str = Query("ultimos_7d", pattern="^(ultimas_24h|ultimos_7d|ultimos_30d|ultimos_90d)$")
):
    """
    Devuelve métricas históricas agregadas por período.

    Períodos disponibles:
    - ultimas_24h: Últimas 24 horas
    - ultimos_7d: Últimos 7 días
    - ultimos_30d: Últimos 30 días
    - ultimos_90d: Últimos 90 días
    """
    return stats_service.obtener_estadisticas_historico(periodo)


@router.get(
    "/calificaciones",
    responses={
        200: {"description": "Listado de todas las calificaciones con sus comentarios"},
    },
)
def listar_calificaciones():
    """Devuelve todas las calificaciones registradas en la plataforma."""
    return admin_service.listar_calificaciones()
