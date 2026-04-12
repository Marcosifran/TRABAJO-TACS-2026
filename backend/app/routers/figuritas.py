from fastapi import APIRouter, HTTPException
from app.schemas.figurita import FiguitaCreate
from app.services import figurita_service

router = APIRouter(prefix="/figuritas", tags=["Figuritas"])

@router.get("/")
def obtener_figuritas():
    return {"disponibles": figurita_service.listar()}


@router.post("/")
def publicar_figurita(figu: FiguitaCreate):
    nueva = figurita_service.publicar(figu)
    return {"mensaje": "Figurita publicada", "data": nueva}


@router.delete("/{figurita_id}")
def eliminar_figurita(figurita_id: int):
    if not figurita_service.eliminar(figurita_id):
        raise HTTPException(status_code=404, detail="Figurita no encontrada")
    return {"mensaje": "Figurita eliminada"}
