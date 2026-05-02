from fastapi import APIRouter, Depends, Query, HTTPException
from app.dependencies import get_current_user
from app.services import publicacion_service
from app.schemas.publicacion_sch import(
    PublicacionCreate,
    PublicacionResponse,
    SugerenciaResponse,
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
    usuario: dict = Depends(get_current_user)
):
    """Retorna las figuritas disponibles poara intercambio aplicando filtros"""

    return publicacion_service.listar_publicaciones(
        numero=numero,
        equipo=equipo,
        jugador=jugador,
        tipo_intercambio=tipo_intercambio,
        excluir_usuario_id=usuario["id"],
    )

@router.get("/mias", response_model=list[PublicacionResponse])
def mis_publicaciones(
    usuario: dict = Depends(get_current_user),
):
    """
    Retorna las publicaciones activas del usuario autenticado.
    A diferencia de GET /, este endpoint SÍ incluye las propias.
    """
    return publicacion_service.mis_publicaciones(usuario["id"])

@router.get("/sugerencias", response_model=list[SugerenciaResponse])
def obtener_sugerencias(
    usuario: dict = Depends(get_current_user)
):
    """Genera sugerencias automaticas de intercambio para el usuario, desde faltantes del usuario con publicaciones de otros"""

    return publicacion_service.obtener_sugerencias(usuario["id"])

@router.delete("/{publicacion_id}", status_code=204)
def retirar_publicacion(
    publicacion_id: int,
    usuario: dict = Depends(get_current_user)
):
    """Retira una figurita de la oferta publica"""

    resultado = publicacion_service.retirar_publicacion(publicacion_id, usuario["id"])

    if resultado is False:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    if resultado is None:
        raise HTTPException(status_code=403, detail="No tenés permiso para retirar esta publicación")
    
