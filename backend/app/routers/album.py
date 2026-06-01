from fastapi import APIRouter, Depends, Query
from app.dependencies import get_current_user
from app.services import album_service
from app.schemas import FiguritaAlbumCreate, FiguritaAlbumResponse

router = APIRouter(prefix="/album", tags=["Album"])


@router.post("/", response_model=FiguritaAlbumResponse, status_code=201)
def agregar_al_album(
    figurita: FiguritaAlbumCreate,
    usuario: dict = Depends(get_current_user),
):
    return album_service.agregar_al_album(figurita, usuario["id"])


@router.get("/", response_model=list[FiguritaAlbumResponse], status_code=200)
def listar_album(
    numero: int | None = Query(default=None),
    equipo: str | None = Query(default=None),
    jugador: str | None = Query(default=None),
    usuario: dict = Depends(get_current_user),
):
    return album_service.buscar_en_album(
        usuario_id=usuario["id"],
        numero=numero,
        equipo=equipo,
        jugador=jugador,
    )


@router.delete(
    "/{figurita_id}",
    status_code=204,
    responses={
        204: {"description": "Figurita eliminada del álbum"},
        403: {"description": "La figurita no pertenece al usuario"},
        404: {"description": "Figurita no encontrada en el álbum"},
        409: {"description": "La figurita está en una publicación activa"},
    },
)
def eliminar_del_album(
    figurita_id: str,
    usuario: dict = Depends(get_current_user),
):
    album_service.eliminar_del_album(figurita_id, usuario["id"])
