from fastapi import APIRouter, Depends
from app.schemas.faltante import FaltanteCreate
from app.schemas.calificacion_sch import ReputacionResponse
from app.services import usuario_service, album_service, calificacion_service, subasta_service
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
    return album_service.listar_album(usuario["id"])


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
    return usuario_service.listar_faltantes(usuario["id"])



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
    return subasta_service.listar_mis_ofertas(usuario["id"])


@router.get(
    "/subastas",
    status_code=200,
    responses={
        200: {"description": "Subastas creadas por el usuario autenticado"},
        401: {"description": "Token ausente o inválido"},
    },
)
def listar_subastas_usuario(usuario: dict = Depends(get_current_user)):
    return subasta_service.listar_subastas_usuario(usuario["id"])
