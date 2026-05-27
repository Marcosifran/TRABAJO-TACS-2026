from fastapi import APIRouter, Depends, HTTPException
from app.schemas.subasta import SubastaCreate, SubastaResponse
from app.schemas.oferta import OfertaCreate, OfertaDecision
from app.services import subasta_service
from app.dependencies import get_current_user
from app.repositories import oferta_repo

router = APIRouter(prefix="/subastas", tags=["Subastas"], dependencies=[Depends(get_current_user)])

@router.get(
    "/",
    responses={
        200: {"description": "Lista de todas las subastas registradas"},
    },
)
def listar_subastas():
    """
    Devuelve las subastas activas.
    """
    return {"subastas": subasta_service.listar_subastas()}

@router.post(
    "/",
    status_code=201,
    responses={
        201: {"description": "Subasta creada exitosamente"},
        400: {"description": "Figurita inexistente / no es del usuario / no configurada para subasta / ya en subasta"},
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Subasta u oferta no encontrada"},
    },
)

def crear_subasta(subasta_data: SubastaCreate, usuario: dict = Depends(get_current_user)):
    """
    Permite a un usuario poner una de sus figuritas en subasta.
    """
    nueva_subasta = subasta_service.crear_subasta(subasta_data, usuario["id"])
    return {"mensaje": "Subasta creada exitosamente", "subasta": nueva_subasta}

@router.patch(
    "/{subasta_id}/ofertas/{oferta_id}",
    status_code=200,
)
def responder_oferta(subasta_id: str, oferta_id: str, decision: OfertaDecision, usuario: dict = Depends(get_current_user)):
    """
    Responde una oferta: puede aceptarse o rechazarse usando el campo `estado`.
    """
    if decision.estado == "aceptada":
        resultado = subasta_service.aceptar_oferta(subasta_id, oferta_id, usuario["id"])
        return {"mensaje": "Oferta aceptada", "resultado": resultado}
    elif decision.estado == "rechazada":
        # Rechazar simplemente elimina la oferta
        deleted = oferta_repo.delete(oferta_id)
        if not deleted:
            raise ValueError("Oferta no encontrada")
        return {"mensaje": "Oferta rechazada"}
    else:
        raise ValueError("Estado desconocido")

        

@router.get(
    "/{subasta_id}/ofertas",
    responses={
        200: {"description": "Lista de ofertas recibidas para la subasta"},
        404: {"description": "Subasta no encontrada"},
    },
)
def listar_ofertas(subasta_id: str):
    """
    Devuelve todas las ofertas recibidas para una subasta.
    """
    ofertas = subasta_service.listar_ofertas(subasta_id)
    return {"ofertas": ofertas}

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
        400: {"description": "Subasta inactiva / es la propia subasta / sin figuritas / figuritas no propias"},
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Subasta o figuritas ofrecidas no encontradas"},
    },
)


def ofertar_en_subasta(
    subasta_id: str,
    oferta: OfertaCreate,
    usuario: dict = Depends(get_current_user)
):
    """
    Permite ofertar en una subasta especificada.
    """
    resultado = subasta_service.ofertar(subasta_id, oferta, usuario["id"])        
    return resultado


