from fastapi import HTTPException
from app.repositories import subasta_repo, publicacion_repo, oferta_repo, album_repo
from app.schemas.subasta import SubastaCreate
from app.schemas.oferta import OfertaCreate


def crear_subasta(subasta_data: SubastaCreate, usuario_id: int) -> dict:
    """
    Crea una nueva subasta para una figurita publicada como 'subasta'.
    Busca en publicacion_repo porque tipo_intercambio vive ahí.
    """
    publicacion = publicacion_repo.get_by_id(subasta_data.figurita_id)

    if not publicacion:
        raise ValueError("Publicación inexistente")

    if publicacion["usuario_id"] != usuario_id:
        raise ValueError("No podés subastar una publicación que no es tuya")

    if publicacion.get("tipo_intercambio") != "subasta":
        raise ValueError("Esta publicación no está configurada para subasta")

    subasta_activa = subasta_repo.get_by_figurita(subasta_data.figurita_id)
    if subasta_activa:
        raise ValueError("Esta figurita ya se encuentra en subasta")

    return subasta_repo.create(
        subasta_data.figurita_id, usuario_id, subasta_data.inicio, subasta_data.fin
    )


def listar_subastas() -> list[dict]:
    return subasta_repo.get_all()


def listar_ofertas(subasta_id: int) -> list[dict]:
    subasta = subasta_repo.get_by_id(subasta_id)
    if not subasta:
        raise ValueError("Subasta inexistente")
    return oferta_repo.get_by_subasta(subasta_id)


def ofertar(subasta_id: int, oferta_data: OfertaCreate, usuario_id: int) -> dict:
    """
    Registra una oferta en una subasta activa.
    Las figuritas ofrecidas se buscan en album_repo (son figuritas del álbum del ofertante).
    """
    subasta = subasta_repo.get_by_id(subasta_id)

    if not subasta:
        raise ValueError("Subasta inexistente")

    if subasta["estado"] != "activa":
        raise ValueError("La subasta no está activa")

    if subasta["usuario_id"] == usuario_id:
        raise ValueError("No podés ofertar en tu propia subasta")

    if not oferta_data.figuritas_ofrecidas:
        raise ValueError("Debés ofrecer al menos una figurita")

    todas = album_repo.get_all()
    ofrecidas = [f for f in todas if f["id"] in oferta_data.figuritas_ofrecidas]

    ids_no_encontrados = set(oferta_data.figuritas_ofrecidas) - {f["id"] for f in ofrecidas}
    if ids_no_encontrados:
        raise ValueError(f"Las figuritas {list(ids_no_encontrados)} no existen")

    if any(f["usuario_id"] != usuario_id for f in ofrecidas):
        raise ValueError("No podés ofrecer una figurita que no es tuya")

    subastada = publicacion_repo.get_by_id(subasta["figurita_id"])
    nueva_oferta = oferta_repo.crear_oferta(subasta_id, [f["id"] for f in ofrecidas], usuario_id)

    return {
        "oferta": nueva_oferta,
        "mensaje": "Oferta realizada",
        "detalle": f"Ofreciste {[f['jugador'] for f in ofrecidas]} por {subastada['jugador'] if subastada else 'la figurita subastada'}",
    }


def listar_subastas_usuario(usuario_id: int) -> list[dict]:
    return subasta_repo.get_by_usuario(usuario_id)