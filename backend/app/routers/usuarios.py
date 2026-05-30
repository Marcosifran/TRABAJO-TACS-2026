from fastapi import APIRouter, Depends, HTTPException
from app.schemas.faltante import FaltanteCreate
from app.schemas.usuario import UsuarioResponse
from app.schemas.calificacion_sch import ReputacionResponse
from app.services import usuario_service, album_service,publicacion_service, calificacion_service, subasta_service
from app.dependencies import get_current_user

router = APIRouter(prefix="/usuarios", tags=["Usuarios"], dependencies=[Depends(get_current_user)])


@router.get(
    "/figuritas",
    status_code=200,
    responses={
        200: {"description": "Figuritas publicadas por el usuario autenticado"},
        401: {"description": "Token ausente o inválido"},
    },
)
def listar_figuritas_usuario(usuario: dict = Depends(get_current_user)):
    """
    Devuelve las figuritas publicadas por el usuario autenticado.
    """
    figuritas = album_service.listar_album(usuario["id"])
    return figuritas


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

    return usuario_service.registrar_faltante(usuario["id"], faltante)


# Devuelve los faltantes del usuario que hace el request
@router.get(
    "/faltantes",
    status_code=200,
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
    return faltantes


# Note: `/usuarios/sugerencias` removed; keep `/publicaciones/sugerencias` as canonical route
@router.get(
    "/sugerencias",
    status_code=200,
    responses={
        200: {"description": "Sugerencias de intercambio basadas en los faltantes del usuario"},
        401: {"description": "Token ausente o inválido"},
    },
)
def obtener_sugerencias_compat(usuario: dict = Depends(get_current_user)):
    """
    Estas sugerencias estaban doblemente disponibles en `/usuarios/sugerencias` y `/publicaciones/sugerencias`. Se mantiene esta ruta por compatibilidad, 
    pero utilizaremos la ruta de publicaciones para obtener sugerencias.
    """
    sugerencias = publicacion_service.obtener_sugerencias(usuario["id"])
    return sugerencias


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
    "/ofertas",
    status_code=200,
    responses={
        200: {"description": "Ofertas enviadas por el usuario autenticado a subastas"},
        401: {"description": "Token ausente o inválido"},
    },
)
def listar_mis_ofertas(usuario: dict = Depends(get_current_user)):
    """Devuelve las ofertas enviadas por el usuario autenticado a subastas de otros."""
    ofertas = subasta_service.listar_mis_ofertas(usuario["id"])
    return ofertas


@router.get(
    "/subastas",
    status_code=200,
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
    return subastas
