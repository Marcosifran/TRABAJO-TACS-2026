from fastapi import APIRouter, Depends, HTTPException
from app.schemas.figurita import FiguitaCreate
from app.services import figurita_service
from app.dependencies import get_current_user

router = APIRouter(prefix="/figuritas", tags=["Figuritas"])

@router.get("/")
def obtener_figuritas():
    return {"disponibles": figurita_service.listar()}


# El usuario que publica se obtiene del token, no del body
@router.post("/")
def publicar_figurita(figu: FiguitaCreate, usuario: dict = Depends(get_current_user)):
    nueva = figurita_service.publicar(figu, usuario["id"])
    return {"mensaje": "Figurita publicada", "data": nueva}


@router.delete("/{figurita_id}")
def eliminar_figurita(figurita_id: int, usuario: dict = Depends(get_current_user)):
    if not figurita_service.eliminar(figurita_id):
        raise HTTPException(status_code=404, detail="Figurita no encontrada")
    return {"mensaje": "Figurita eliminada"}
