from fastapi import APIRouter
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/estadisticas",
    responses={
        200: {"description": "Estadísticas globales de uso y actividad de la plataforma"},
    },
)
def obtener_estadisticas():
    """Devuelve estadísticas globales: usuarios, figuritas, intercambios y subastas."""
    return admin_service.obtener_estadisticas()
