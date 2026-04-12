from fastapi import APIRouter, Depends, HTTPException
from app.schemas.faltante import FaltanteCreate
from app.schemas.usuario import UsuarioResponse
from app.services import usuario_service, figurita_service
from app.dependencies import get_current_user
from app.repositories import usuario_repo

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# Registra una figurita faltante para el usuario autenticado vía token
@router.post("/faltantes", status_code=201)
def registrar_faltante(faltante: FaltanteCreate, usuario: dict = Depends(get_current_user)):
    try:
        resultado = usuario_service.registrar_faltante(usuario["id"], faltante)
    except ValueError as e:
        # Si el error es por datos duplicados, informamos con 409.
        raise HTTPException(status_code=409, detail=str(e))
    if resultado is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"mensaje": "Faltante registrado", "data": resultado}


# Devuelve los faltantes del usuario que hace el request
@router.get("/faltantes")
def listar_faltantes(usuario: dict = Depends(get_current_user)):
    faltantes = usuario_service.listar_faltantes(usuario["id"])
    if faltantes is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"usuario_id": usuario["id"], "faltantes": faltantes}


# Devuelve sugerencias de intercambio: figuritas de otros usuarios que cubren los faltantes del usuario autenticado
@router.get("/sugerencias")
def obtener_sugerencias(usuario: dict = Depends(get_current_user)):
    sugerencias = figurita_service.sugerir_intercambios(usuario["id"])
    return {"usuario_id": usuario["id"], "sugerencias": sugerencias}
