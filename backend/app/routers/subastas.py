from fastapi import APIRouter, Depends, Response
from app.schemas.subasta import SubastaCreate
from app.schemas.oferta import OfertaCreate, OfertaDecision
from app.services import subasta_service
from app.dependencies import get_current_user, page_params

router = APIRouter(prefix="/subastas", tags=["Subastas"], dependencies=[Depends(get_current_user)])


@router.get(
    "/",
    status_code=200,
    responses={
        200: {"description": "Lista de todas las subastas registradas"},
    },
)
def listar_subastas(page: dict = Depends(page_params)):
    return subasta_service.listar_subastas(limit=page["limit"], offset=page["offset"])


@router.post(
    "/",
    status_code=201,
    responses={
        201: {"description": "Subasta creada exitosamente"},
        400: {"description": "Publicación no configurada para subasta"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "La publicación no pertenece al usuario"},
        404: {"description": "Publicación inexistente"},
        409: {"description": "La figurita ya se encuentra en subasta"},
    },
)
def crear_subasta(subasta_data: SubastaCreate, usuario: dict = Depends(get_current_user)):
    return subasta_service.crear_subasta(subasta_data, usuario["id"])


@router.delete(
    "/{subasta_id}",
    status_code=204,
    responses={
        204: {"description": "Subasta cancelada exitosamente"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "No sos el creador de la subasta"},
        404: {"description": "Subasta no encontrada"},
        409: {"description": "La subasta ya está finalizada o tiene oferta aceptada"},
    },
)
def cancelar_subasta(subasta_id: str, usuario: dict = Depends(get_current_user)):
    subasta_service.cancelar_subasta(subasta_id, usuario["id"])


@router.patch(
    "/{subasta_id}/ofertas/{oferta_id}",
    responses={
        200: {"description": "Oferta aceptada; intercambio de figuritas realizado"},
        204: {"description": "Oferta rechazada"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "No tenés permiso para responder esta oferta"},
        404: {"description": "Subasta u oferta no encontrada"},
    },
)
def responder_oferta(
    subasta_id: str,
    oferta_id: str,
    decision: OfertaDecision,
    usuario: dict = Depends(get_current_user),
):
    resultado = subasta_service.responder_oferta(subasta_id, oferta_id, decision.estado, usuario["id"])
    if resultado is None:
        return Response(status_code=204)
    return resultado


@router.get(
    "/{subasta_id}/ofertas",
    status_code=200,
    responses={
        200: {"description": "Lista de ofertas recibidas para la subasta"},
        404: {"description": "Subasta no encontrada"},
    },
)
def listar_ofertas(subasta_id: str, page: dict = Depends(page_params)):
    return subasta_service.listar_ofertas(subasta_id, limit=page["limit"], offset=page["offset"])


@router.delete(
    "/{subasta_id}/ofertas/{oferta_id}",
    status_code=204,
    responses={
        204: {"description": "Oferta cancelada exitosamente"},
        400: {"description": "La subasta ya no está activa"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "La oferta no pertenece al usuario"},
        404: {"description": "Oferta no encontrada"},
    },
)
def cancelar_oferta(
    subasta_id: str,
    oferta_id: str,
    usuario: dict = Depends(get_current_user),
):
    subasta_service.cancelar_oferta(oferta_id, usuario["id"])


@router.post(
    "/{subasta_id}/ofertas",
    status_code=201,
    responses={
        201: {"description": "Oferta registrada exitosamente"},
        400: {"description": "Subasta inactiva / sin figuritas"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Es la propia subasta / figuritas no propias"},
        404: {"description": "Subasta o figuritas ofrecidas no encontradas"},
        409: {"description": "Ya enviaste una oferta a esta subasta"},
    },
)
def ofertar_en_subasta(
    subasta_id: str,
    oferta: OfertaCreate,
    usuario: dict = Depends(get_current_user),
):
    return subasta_service.ofertar(subasta_id, oferta, usuario["id"])
