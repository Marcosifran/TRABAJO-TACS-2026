from fastapi import APIRouter, Depends, Query
from app.dependencies import get_current_user
from app.services import publicacion_service
from app.schemas.publicacion_sch import (
    PublicacionCreate,
    PublicacionResponse,
    SugerenciaResponse,
)

router = APIRouter(prefix="/publicaciones", tags=["Publicaciones"])


@router.post("/", response_model=PublicacionResponse, status_code=201)
def publicar_figurita(
    publicacion: PublicacionCreate,
    usuario: dict = Depends(get_current_user),
):
    return publicacion_service.publicar_figurita(publicacion, usuario["id"])


@router.get("/", response_model=list[PublicacionResponse], status_code=200)
def listar_publicaciones(
    numero: int | None = Query(default=None, description="Número de la figurita"),
    equipo: str | None = Query(default=None, description="Equipo de la figurita"),
    jugador: str | None = Query(default=None, description="Jugador de la figurita"),
    tipo_intercambio: str | None = Query(default=None, description="intercambio directo o subasta"),
    incluir_propias: bool = Query(default=False, description="Incluir las propias publicaciones del usuario autenticado"),
    usuario: dict = Depends(get_current_user),
):
    excluir_usuario_id = None if incluir_propias else usuario["id"]
    return publicacion_service.listar_publicaciones(
        numero=numero,
        equipo=equipo,
        jugador=jugador,
        tipo_intercambio=tipo_intercambio,
        excluir_usuario_id=excluir_usuario_id,
    )


# Note: `/publicaciones/mias` removed in favor of `GET /publicaciones?incluir_propias=true`

@router.get("/sugerencias", response_model=list[SugerenciaResponse], status_code=200)
def obtener_sugerencias(
    usuario: dict = Depends(get_current_user),
):
    return publicacion_service.obtener_sugerencias(usuario["id"])


@router.delete("/{publicacion_id}", status_code=204)
def retirar_publicacion(
    publicacion_id: str,
    usuario: dict = Depends(get_current_user),
):
    publicacion_service.retirar_publicacion(publicacion_id, usuario["id"])
