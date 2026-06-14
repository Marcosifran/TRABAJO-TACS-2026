from app.repositories import album_repo, publicacion_repo, faltante_repo
from app.schemas import FiguritaAlbumCreate, FiguritaAlbumResponse
from app.domain.album import FiguritaAlbum
from app.domain.errors import DomainNotFoundError, DomainPermissionError, DomainConflictError


def agregar_al_album(figurita: FiguritaAlbumCreate, usuario_id: int) -> FiguritaAlbumResponse:
    resultado = album_repo.create(figurita, usuario_id)
    faltante_repo.remove_missing(usuario_id, figurita.numero)
    return _enriquecer(resultado)


def listar_album(usuario_id: int) -> list[FiguritaAlbumResponse]:
    figuritas = album_repo.get_by_user(usuario_id)
    return [_enriquecer(f) for f in figuritas]


def buscar_en_album(
    usuario_id: int,
    numero: int | None,
    equipo: str | None,
    jugador: str | None,
    limit: int = 50,
    offset: int = 0,
) -> list[FiguritaAlbumResponse]:
    figuritas = album_repo.find(numero, equipo, jugador, usuario_id=usuario_id, limit=limit, offset=offset)
    return [_enriquecer(f) for f in figuritas]


def eliminar_del_album(figurita_id: str, usuario_id: int) -> None:
    figurita = album_repo.get_by_id(figurita_id)
    if figurita is None:
        raise DomainNotFoundError("Figurita no encontrada en el álbum del usuario")
    if figurita.usuario_id != usuario_id:
        raise DomainPermissionError("La figurita no pertenece al usuario")
    if publicacion_repo.get_by_personal_figurita(figurita.id):
        raise DomainConflictError("No se puede eliminar la figurita porque está en una publicación activa")
    album_repo.delete(figurita_id)


def _enriquecer(figurita: FiguritaAlbum) -> FiguritaAlbumResponse:
    tiene_publicacion = publicacion_repo.get_by_personal_figurita(figurita.id) is not None
    response = FiguritaAlbumResponse.model_validate(figurita, from_attributes=True)
    return response.model_copy(update={"en_intercambio": tiene_publicacion})
