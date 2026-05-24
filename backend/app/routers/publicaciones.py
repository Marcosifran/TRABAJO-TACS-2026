from fastapi import APIRouter, Depends, Query, HTTPException
from app.dependencies import get_current_user
from app.services import publicacion_service
from app.schemas.publicacion_sch import(
    PublicacionCreate,
    PublicacionResponse,
    SugerenciaResponse,
    SugerenciasEnvelope,
)

router = APIRouter(prefix="/publicaciones", tags=["Publicaciones"])

@router.post("/", response_model=PublicacionResponse, status_code=201)
def publicar_figurita(
    publicacion: PublicacionCreate,
    usuario: dict = Depends(get_current_user)
):
    """Pone una figurita del album personal en oferta publica para intercambio"""

    return publicacion_service.publicar_figurita(publicacion, usuario["id"])

@router.get("/", response_model=list[PublicacionResponse])
def listar_publicaciones(
    numero: int | None = Query(default=None, description="Número de la figurita"),
    equipo: str | None = Query(default=None, description="Equipo de la figurita"),
    jugador: str | None = Query(default=None, description="Jugador de la figurita"),
    tipo_intercambio: str | None = Query(default=None, description="intercambio directo o subasta"),
    incluir_propias: bool = Query(default=False, description="Incluir las propias publicaciones del usuario autenticado"),
    usuario: dict = Depends(get_current_user)
):
    """Retorna las figuritas disponibles poara intercambio aplicando filtros"""
    excluir_usuario_id = None if incluir_propias else usuario["id"]
    return publicacion_service.listar_publicaciones(
        numero=numero,
        equipo=equipo,
        jugador=jugador,
        tipo_intercambio=tipo_intercambio,
        excluir_usuario_id=excluir_usuario_id,
    )

# Note: `/publicaciones/mias` removed in favor of `GET /publicaciones?incluir_propias=true`

@router.get("/sugerencias", response_model=SugerenciasEnvelope)
def obtener_sugerencias(
    usuario: dict = Depends(get_current_user)
):
    """Genera sugerencias automaticas de intercambio para el usuario, desde faltantes del usuario con publicaciones de otros"""
    sugerencias = publicacion_service.obtener_sugerencias(usuario["id"])
    return {"usuario_id": usuario["id"], "sugerencias": sugerencias}

@router.delete("/{publicacion_id}", status_code=204)
def retirar_publicacion(
    publicacion_id: int,
    usuario: dict = Depends(get_current_user)
):
    """Retira una figurita de la oferta publica"""
    resultado = publicacion_service.retirar_publicacion(publicacion_id, usuario["id"])

    if resultado is False:
        raise HTTPException(status_code = 404, detail = "Publiacacion no encontrada")
    if resultado is None:
        raise HTTPException(status_code = 403, detail = "No tiene permiso para retirar")
