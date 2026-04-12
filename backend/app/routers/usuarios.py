from fastapi import APIRouter, HTTPException
from app.schemas.faltante import FaltanteCreate
from app.services import usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# Registra una figurita faltante para un usuario específico.
@router.post("/{usuario_id}/faltantes")
def registrar_faltante(usuario_id: int, faltante: FaltanteCreate):
    resultado = usuario_service.registrar_faltante(usuario_id, faltante)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"mensaje": "Faltante registrado", "data": resultado}


# Devuelve todas las figuritas faltantes de un usuario específico.
@router.get("/{usuario_id}/faltantes")
def listar_faltantes(usuario_id: int):
    faltantes = usuario_service.listar_faltantes(usuario_id)
    if faltantes is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"usuario_id": usuario_id, "faltantes": faltantes}
