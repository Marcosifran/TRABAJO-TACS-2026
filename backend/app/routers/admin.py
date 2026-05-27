from fastapi import APIRouter, Depends, HTTPException
from app.services import admin_service
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
def obtener_estadisticas():
    """Devuelve estadísticas globales: usuarios, figuritas, intercambios y subastas."""
    return admin_service.obtener_estadisticas()
