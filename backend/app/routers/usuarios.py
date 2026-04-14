from fastapi import APIRouter, Depends, HTTPException
from app.schemas.faltante import FaltanteCreate
from app.schemas.usuario import UsuarioResponse
from app.schemas.calificacion_sch import ReputacionResponse
from app.services import usuario_service, figurita_service, calificacion_service, subasta_service
from app.dependencies import get_current_user
from app.repositories import usuario_repo

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get(
    "/figuritas",
    responses={
        200: {"description": "Figuritas publicadas por el usuario autenticado"},
        401: {"description": "Token ausente o inválido"},
    },
)
def listar_figuritas_usuario(usuario: dict = Depends(get_current_user)):
    """
    Devuelve las figuritas publicadas por el usuario autenticado.
    """
    figuritas = figurita_service.buscar_por_usuario(usuario["id"])
    return {"usuario_id": usuario["id"], "figuritas": figuritas}


# Registra una figurita faltante para el usuario autenticado vía token
@router.post(
    "/faltantes",
    status_code=201,
    responses={
        201: {"description": "Faltante registrado exitosamente"},
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Usuario no encontrado"},
        409: {"description": "La figurita ya está registrada como faltante"},
    },
)
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
@router.get(
    "/faltantes",
    responses={
        200: {"description": "Lista de figuritas faltantes del usuario autenticado"},
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Usuario no encontrado"},
    },
)
def listar_faltantes(usuario: dict = Depends(get_current_user)):
    faltantes = usuario_service.listar_faltantes(usuario["id"])
    if faltantes is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"usuario_id": usuario["id"], "faltantes": faltantes}


# Devuelve sugerencias de intercambio: figuritas de otros usuarios que cubren los faltantes del usuario autenticado
@router.get(
    "/sugerencias",
    responses={
        200: {"description": "Sugerencias de intercambio basadas en los faltantes del usuario"},
        401: {"description": "Token ausente o inválido"},
    },
)
def obtener_sugerencias(usuario: dict = Depends(get_current_user)):
    sugerencias = figurita_service.sugerir_intercambios(usuario["id"])
    return {"usuario_id": usuario["id"], "sugerencias": sugerencias}


@router.get(
    "/{usuario_id}/reputacion",
    response_model=ReputacionResponse,
    responses={
        200: {"description": "Reputación del usuario con promedio y cantidad de calificaciones recibidas"},
        404: {"description": "Usuario no encontrado"},
    },
)
def obtener_reputacion(usuario_id: int):
    return calificacion_service.obtener_reputacion(usuario_id)

@router.get(
    "/subastas",
    responses={
        200: {"description": "Subastas creadas por el usuario autenticado"},
        401: {"description": "Token ausente o inválido"},
    },
)
def listar_subastas_usuario(usuario: dict = Depends(get_current_user)):
    """
    Devuelve las subastas creadas de forma activa por el usuario autenticado.
    """
    subastas = subasta_service.listar_subastas_usuario(usuario["id"])
    return {"usuario_id": usuario["id"], "subastas": subastas}
