from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.schemas.figurita import FiguritaCreate
from app.services import figurita_service
from app.dependencies import get_current_user
from app.repositories import figurita_repo

router = APIRouter(prefix="/figuritas", tags=["Figuritas"])

@router.get("/")
def buscar_figuritas(
    numero: Optional[int] = Query(None, ge=1, description="Número exacto de la figurita"),
    equipo: Optional[str] = Query(None, min_length=1, description="Nombre del equipo o selección (búsqueda parcial)"),
    jugador: Optional[str] = Query(None, min_length=1, description="Nombre del jugador (búsqueda parcial)"),
):
    """
    Devuelve las figuritas disponibles. Permite filtrar opcionalmente por número, equipo y/o jugador.
    Si no se proporciona ningún filtro, devuelve todas las figuritas publicadas.
    """
    resultado = figurita_service.buscar(numero, equipo, jugador)
    return {"figuritasDisponibles": resultado}


# El usuario que publica se obtiene del token, no del body
@router.post("/", status_code=201)
def publicar_figurita(figu: FiguritaCreate, usuario: dict = Depends(get_current_user)):
    try:
        nueva = figurita_service.publicar(figu, usuario["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"mensaje": "Figurita a intercambiar publicada", "data": nueva}


@router.delete("/{figurita_id}")
def eliminar_figurita(figurita_id: int, usuario: dict = Depends(get_current_user)):
    if not figurita_service.eliminar(figurita_id):
        raise HTTPException(status_code=404, detail="Figurita no encontrada")
    return {"mensaje": "Figurita eliminada"}

