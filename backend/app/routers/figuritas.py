from _typeshed import importlib
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.schemas.figurita import FiguritaCreate
from app.schemas.oferta import OfertaCreate
from app.services import figurita_service
from app.dependencies import get_current_user
from app.repositories import oferta_repo, figurita_repo

router = APIRouter(prefix="/figuritas", tags=["Figuritas"])

@router.get("/")
def buscar_figuritas(
    numero: Optional[int] = Query(None, ge=1, description="Número exacto de la figurita"),
    equipo: Optional[str] = Query(None, min_length=1, description="Nombre del equipo o selección (búsqueda parcial)"),
    jugador: Optional[str] = Query(None, min_length=1, description="Nombre del jugador (búsqueda parcial)"),
):
    """
    Devuelve las figuritas disponibles. Permite filtrar opcionalmente por número, equipo y/o jugador.
    Si no se proporciona ningún filtro, devuelve todas las figuritas publicadas.
    """
    resultado = figurita_service.buscar(numero, equipo, jugador)
    return {"figuritasDisponibles": resultado}


# El usuario que publica se obtiene del token, no del body
@router.post("/", status_code=201)
def publicar_figurita(figu: FiguritaCreate, usuario: dict = Depends(get_current_user)):
    try:
        nueva = figurita_service.publicar(figu, usuario["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"mensaje": "Figurita a intercambiar publicada", "data": nueva}


@router.delete("/{figurita_id}")
def eliminar_figurita(figurita_id: int, usuario: dict = Depends(get_current_user)):
    if not figurita_service.eliminar(figurita_id):
        raise HTTPException(status_code=404, detail="Figurita no encontrada")
    return {"mensaje": "Figurita eliminada"}

@router.post("/{figurita_id}/ofertar", status_code=201)


def ofertar_figurita(
    figurita_id: int,
    oferta: OfertaCreate,
    usuario: dict = Depends(get_current_user)
):
    """
    Se permite ofertar una figurita, verificando que esta existe y que no es del usuario que oferta.
    """
    #se busca la figurita que está en la subasta
    todas = figurita_repo.get_all()
    subasta = next((f for f in todas if f["id"] == figurita_id), None)

    if not subasta:
        raise HTTPException(status_code=404, detail="Figurita inexistente")
    
    if subasta["tipo_intercambio"] != "subasta":
        raise HTTPException(status_code=400, detail="La figurita no acepta ofertas")
    
    #se busca la figurita que el usuario ofrece
    ofrecida = next((f for f in todas if f["id"] == oferta.figurita_ofrecida_id), None)

    if not ofrecida:
        raise HTTPException(status_code=404, detail="La figurita que estás ofreciendo no existe")

    #se verifica que la figurita sea de quien está logueado
    if ofrecida["usuario_id"] != usuario["id"]:
        raise HTTPException(status_code=403, detail="No podés ofrecer una figurita que no es tuya")

    #se evita que se oferte en su propia subasta
    if subasta["usuario_id"] == usuario["id"]:
        raise HTTPException(status_code=400, detail="No podés ofertar en tu propia subasta")

    
    #se guarda la oferta en el repo de ofertas
    nueva_oferta = oferta_repo.crear_oferta(subasta["id"], ofrecida["id"], usuario["id"])

    return {
        "mensaje": "Oferta realizada",
        "detalle": f"Ofreciste a {ofrecida['jugador']} por {subasta['jugador']}"
    }