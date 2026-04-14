from fastapi import APIRouter, Depends, HTTPException
from app.schemas.subasta import SubastaCreate, SubastaResponse
from app.schemas.oferta import OfertaCreate
from app.services import subasta_service
from app.dependencies import get_current_user

router = APIRouter(prefix="/subastas", tags=["Subastas"])

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
    },
)
def crear_subasta(subasta_data: SubastaCreate, usuario: dict = Depends(get_current_user)):
    """
    Permite a un usuario poner una de sus figuritas en subasta.
    """
    try:
        nueva_subasta = subasta_service.crear_subasta(subasta_data, usuario["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"mensaje": "Subasta creada exitosamente", "subasta": nueva_subasta}

@router.get(
    "/{subasta_id}/ofertas",
    responses={
        200: {"description": "Lista de ofertas recibidas para la subasta"},
        404: {"description": "Subasta no encontrada"},
    },
)
def listar_ofertas(subasta_id: int):
    """
    Devuelve todas las ofertas recibidas para una subasta.
    """
    try:
        ofertas = subasta_service.listar_ofertas(subasta_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"ofertas": ofertas}

@router.post(
    "/{subasta_id}/ofertar",
    status_code=201,
    responses={
        201: {"description": "Oferta registrada exitosamente"},
        400: {"description": "Subasta inactiva / es la propia subasta / sin figuritas / figuritas no propias"},
        401: {"description": "Token ausente o inválido"},
        404: {"description": "Subasta o figuritas ofrecidas no encontradas"},
    },
)
def ofertar_en_subasta(
    subasta_id: int,
    oferta: OfertaCreate,
    usuario: dict = Depends(get_current_user)
):
    """
    Permite ofertar en una subasta especificada.
    """
    try:
        resultado = subasta_service.ofertar(subasta_id, oferta, usuario["id"])
    except ValueError as e:
        if "inexistente" in str(e).lower() or "no existe" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
        
    return resultado
