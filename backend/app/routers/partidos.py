from fastapi import APIRouter, Depends, HTTPException
from app.services import partidos_service
from app.dependencies import get_current_user

router = APIRouter(prefix="/partidos", tags=["Partidos"])


@router.get(
    "/",
    summary="Listar partidos del Mundial 2026",
    description=(
        "Devuelve todos los partidos del Mundial 2026 ordenados por fecha. "
        "Los datos provienen de football-data.org y se cachean en MongoDB. "
        "Incluye resultado (goles_local / goles_visitante) para los partidos ya jugados."
    ),
)
def listar_partidos():
    return {"partidos": partidos_service.get_todos()}


@router.post(
    "/refresh",
    summary="Actualizar partidos desde football-data.org",
    description=(
        "Vuelve a consultar la API de football-data.org y reemplaza los datos en MongoDB. "
        "Útil para traer resultados actualizados durante el torneo. Solo administradores."
    ),
    responses={
        200: {"description": "Partidos actualizados correctamente"},
        403: {"description": "Solo administradores"},
        503: {"description": "Error al contactar football-data.org"},
    },
)
def refresh_partidos(usuario: dict = Depends(get_current_user)):
    if not usuario.get("es_admin"):
        raise HTTPException(status_code=403, detail="Solo administradores pueden actualizar los partidos")
    try:
        total = partidos_service.refresh()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Error al obtener partidos: {exc}")
    return {"mensaje": "Partidos actualizados", "total": total}
