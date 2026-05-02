from fastapi import APIRouter, Depends, Query
from app.dependencies import get_current_user
from app.services import album_service
from app.schemas.album_sch import FiguritaAlbumCreate, FiguritaAlbumResponse

router = APIRouter(prefix="/album", tags=["Album"])

@router.post("/", response_model=FiguritaAlbumResponse, status_code=201)
def agregar_al_album(
    figurita: FiguritaAlbumCreate, 
    usuario: dict = Depends(get_current_user)
):
    """Agrega una figurita al album personal del usuario"""

    return album_service.agregar_al_album(figurita, usuario["id"])   

@router.get("/", response_model=list[FiguritaAlbumResponse])
def listar_album(
    numero: int | None = Query(default=None),
    equipo: str | None = Query(default=None),
    jugador: str | None = Query(default=None),
    usuario: dict = Depends(get_current_user)
):
    return album_service.buscar_en_album(
        usuario_id=usuario["id"],
        numero=numero,
        equipo=equipo,
        jugador=jugador
    )


@router.delete("/{figurita_id}", status_code=204)
def eliminar_del_album(
    figurita_id: int,
    usuario: dict = Depends(get_current_user)
):
    """Elimina una figurita del album personal del usuario"""

    resultado = album_service.eliminar_del_album(figurita_id, usuario["id"])

    if resultado is False:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Figurita no encontrada en el álbum del usuario")
    if resultado is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="La figurita no pertenece al usuario")