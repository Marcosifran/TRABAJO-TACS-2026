from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.schemas.figurita import FiguritaCreate
from app.services import figurita_service
from app.dependencies import get_current_user

router = APIRouter(prefix="/figuritas", tags=["Figuritas"], dependencies=[Depends(get_current_user)])


@router.get(
    "/",
    status_code=200,
    responses={
        200: {"description": "Lista de figuritas que coinciden con los filtros aplicados"},
    },
)
def buscar_figuritas(
    numero: Optional[int] = Query(None, ge=1, description="Número exacto de la figurita"),
    equipo: Optional[str] = Query(None, min_length=1, description="Nombre del equipo o selección (búsqueda parcial)"),
    jugador: Optional[str] = Query(None, min_length=1, description="Nombre del jugador (búsqueda parcial)"),
):
    return figurita_service.buscar(numero, equipo, jugador)


@router.post(
    "/",
    status_code=201,
    responses={
        201: {"description": "Figurita publicada exitosamente"},
        400: {"description": "Datos inválidos para la figurita"},
        401: {"description": "Token ausente o inválido"},
    },
)
def publicar_figurita(figu: FiguritaCreate, usuario: dict = Depends(get_current_user)):
    return figurita_service.publicar(figu, usuario["id"])


@router.delete(
    "/{figurita_id}",
    status_code=204,
    responses={
        204: {"description": "Figurita eliminada exitosamente"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "No tenés permiso para eliminar esta figurita"},
        404: {"description": "Figurita no encontrada"},
    },
)
def eliminar_figurita(figurita_id: str, usuario: dict = Depends(get_current_user)):
    figurita_service.eliminar(figurita_id, usuario["id"])
