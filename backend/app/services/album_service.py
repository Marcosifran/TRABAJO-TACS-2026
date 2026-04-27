from fastapi import HTTPException
from app.repositories import album_repo, publicacion_repo, usuario_repo
from app.schemas.album_sch import FiguritaAlbumCreate

def agregar_al_album(figurita: FiguritaAlbumCreate, usuario_id: int) -> dict:  
    """ Agrega una figurita al album personas, no la pone para intercambio, eso se hace desdde publicacion_service. Si estaba faltante la elimina"""
    resultado= album_repo.create(figurita, usuario_id)

    usuario_repo.remove_faltante(usuario_id, figurita.numero)
    
    return resultado

def listar_album(usuario_id: int) -> list[dict]:
    """Retorna las figuritas del album personal del usuario"""
    figuritas = album_repo.get_by_usuario(usuario_id)
    return [_enriquecer(f) for f in figuritas]

def buscar_en_album(
        usuario_id: int,
        numero: int | None,
        equipo: str | None,
        jugador: str | None
) -> list[dict]:
    """Busca figuritas en el album personal del usuario según los criterios dados"""
    figuritas = album_repo.buscar(numero, equipo, jugador, usuario_id=usuario_id)
    return [_enriquecer(f) for f in figuritas]

def eliminar_del_album (figurita_id: int, usuario_id: int) -> bool | None: 
    """ Elimina una figurita del album personal"""
    figurita = album_repo.get_by_id(figurita_id)

    if figurita is None:
        return False
    
    if figurita["usuario_id"] != usuario_id:
        return None

    if publicacion_repo.get_by_figurita_personal(figurita["id"]):
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar la figurita porque está en una publicación activa"
        )
    album_repo.delete(figurita_id)
    return True

def _enriquecer(figurita:dict) -> dict:
    """ Agrega el campo en intercambio a una figurita del album, para ver si tiene publicacion activa"""
    tiene_publicacion = publicacion_repo.get_by_figurita_personal(figurita["id"]) is not None
    return {**figurita, "en_intercambio": tiene_publicacion}

