from fastapi import APIRouter, Depends, HTTPException
from app.schemas.subasta import SubastaCreate, SubastaResponse
from app.schemas.oferta import OfertaCreate
from app.services import subasta_service
from app.dependencies import get_current_user

router = APIRouter(prefix="/subastas", tags=["Subastas"])

@router.get("/")
def listar_subastas():
    """
    Devuelve las subastas activas.
    """
    return {"subastas": subasta_service.listar_subastas()}

@router.post("/", status_code=201)
def crear_subasta(subasta_data: SubastaCreate, usuario: dict = Depends(get_current_user)):
    """
    Permite a un usuario poner una de sus figuritas en subasta.
    """
    try:
        nueva_subasta = subasta_service.crear_subasta(subasta_data, usuario["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"mensaje": "Subasta creada exitosamente", "subasta": nueva_subasta}

@router.get("/{subasta_id}/ofertas")
def listar_ofertas(subasta_id: int):
    """
    Devuelve todas las ofertas recibidas para una subasta.
    """
    try:
        ofertas = subasta_service.listar_ofertas(subasta_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"ofertas": ofertas}

@router.post("/{subasta_id}/ofertar", status_code=201)
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
