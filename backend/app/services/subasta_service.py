import datetime as dt
from fastapi import HTTPException
from app.repositories import subasta_repo, publicacion_repo, oferta_repo, album_repo
from app.schemas.subasta import SubastaCreate
from app.schemas.oferta import OfertaCreate


def _esta_activa(subasta: dict) -> bool:
    """Verifica en tiempo real si la subasta está dentro del rango activo."""
    if subasta.get("estado") != "activa":
        return False
    ahora = dt.datetime.now(dt.timezone.utc)
    fin = subasta.get("fin")
    if fin is None:
        return False
    if isinstance(fin, str):
        fin = dt.datetime.fromisoformat(fin)
    if fin.tzinfo is None:
        fin = fin.replace(tzinfo=dt.timezone.utc)
    return ahora <= fin


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


def listar_ofertas(subasta_id: str) -> list[dict]:
    subasta = subasta_repo.get_by_id(subasta_id)
    if not subasta:
        raise ValueError("Subasta inexistente")
    ofertas = oferta_repo.get_by_auction(subasta_id)
    result = []
    for oferta in ofertas:
        enriquecida = dict(oferta)
        enriquecida["ofrecidas_detalle"] = [
            {
                "id": fig["id"],
                "numero": fig["numero"],
                "equipo": fig["equipo"],
                "jugador": fig["jugador"],
            }
            for album_id in oferta["ofrecidas"]
            if (fig := album_repo.get_by_id(album_id))
        ]
        result.append(enriquecida)
    return result


def ofertar(subasta_id: str, oferta_data: OfertaCreate, usuario_id: int) -> dict:
    """
    Registra una oferta en una subasta activa.
    Las figuritas ofrecidas se buscan en album_repo (son figuritas del álbum del ofertante).
    """
    subasta = subasta_repo.get_by_id(subasta_id)

    if not subasta:
        raise ValueError("Subasta inexistente")

    if not _esta_activa(subasta):
        raise ValueError("La subasta no está activa o ya finalizó")

    if subasta["usuario_id"] == usuario_id:
        raise ValueError("No podés ofertar en tu propia subasta")

    ofertas_existentes = oferta_repo.get_by_auction(subasta_id)
    if any(o["usuario_id"] == usuario_id for o in ofertas_existentes):
        raise ValueError("Ya enviaste una oferta a esta subasta")

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
    nueva_oferta = oferta_repo.create_offer(subasta_id, [f["id"] for f in ofrecidas], usuario_id)

    return {
        "oferta": nueva_oferta,
        "mensaje": "Oferta realizada",
        "detalle": f"Ofreciste {[f['jugador'] for f in ofrecidas]} por {subastada['jugador'] if subastada else 'la figurita subastada'}",
    }


def listar_subastas_usuario(usuario_id: int) -> list[dict]:
    return subasta_repo.get_by_user(usuario_id)


def listar_mis_ofertas(usuario_id: int) -> list[dict]:
    ofertas = oferta_repo.get_by_user(usuario_id)
    result = []
    for oferta in ofertas:
        enriquecida = dict(oferta)
        subasta = subasta_repo.get_by_id(oferta["subasta_id"])
        enriquecida["subasta"] = subasta
        if subasta:
            pub = publicacion_repo.get_by_id(subasta["figurita_id"])
            enriquecida["figurita_subastada"] = {
                "jugador": pub["jugador"],
                "equipo": pub["equipo"],
                "numero": pub["numero"],
            } if pub else None
        enriquecida["ofrecidas_detalle"] = [
            {"id": fig["id"], "numero": fig["numero"], "equipo": fig["equipo"], "jugador": fig["jugador"]}
            for album_id in oferta["ofrecidas"]
            if (fig := album_repo.get_by_id(album_id))
        ]
        result.append(enriquecida)
    return result

def cancelar_oferta(oferta_id: str, usuario_id: int) -> str:
    oferta = oferta_repo.get_by_id(oferta_id)
    if not oferta:
        raise ValueError("Oferta no encontrada")
    if oferta["usuario_id"] != usuario_id:
        raise PermissionError("No podés cancelar una oferta que no es tuya")
    subasta = subasta_repo.get_by_id(oferta["subasta_id"])
    if not subasta or not _esta_activa(subasta):
        raise ValueError("Solo podés cancelar ofertas de subastas activas")
    oferta_repo.delete(oferta_id)
    return "Oferta cancelada"

def aceptar_oferta(subasta_id: str, oferta_id: str, usuario_id: int) -> dict:
    """
    Aceptar oferta en una subasta y limpiar publicaciones huérfanas
    """
    subasta = subasta_repo.get_by_id(subasta_id)
    if not subasta:
        raise ValueError("Subasta no encontrada")
    
    if subasta["usuario_id"] != usuario_id:
        raise PermissionError("No podés aceptar una oferta que no es tuya")

    if not _esta_activa(subasta):
        raise ValueError("La subasta no está activa o ya finalizó")
    
    oferta = oferta_repo.get_by_id(oferta_id)
    if not oferta:
        raise ValueError("Oferta no encontrada")

    if oferta["subasta_id"] != subasta_id:
        raise ValueError("La oferta no pertenece a esta subasta")

    ofertante_id = oferta["usuario_id"]
    figurita_subastada_id = subasta["figurita_id"]
    figuritas_ofrecidas_ids = oferta["ofrecidas"]

    publicacion = publicacion_repo.get_by_id(figurita_subastada_id)
    if not publicacion:
        raise ValueError("Publicacion no encontrada")
    
    # transferir la figurita subastada al ofertante (ganador)
    figurita_album = album_repo.get_by_id(publicacion["figurita_personal_id"])
    if figurita_album:
        figurita_album["usuario_id"] = ofertante_id
        album_repo.update(figurita_album)

    # transferir las figuritas ofrecidas al creador Y limpiar publicaciones
    for fig_id in figuritas_ofrecidas_ids:
        fig_ofrecida = album_repo.get_by_id(fig_id)
        if fig_ofrecida:
            fig_ofrecida["usuario_id"] = usuario_id
            album_repo.update(fig_ofrecida)

            pub_fantasma = publicacion_repo.get_by_personal_figurita(fig_id)
            if pub_fantasma:
                publicacion_repo.delete(pub_fantasma["id"])

    # finalizar la subasta y eliminar la publicación original
    subasta["estado"] = "finalizada"
    subasta["oferta_ganadora_id"] = oferta_id
    subasta_repo.update(subasta)

    publicacion_repo.delete(figurita_subastada_id)

    return {
        "mensaje": "Oferta aceptada y figuritas intercambiadas",
        "subasta_id": subasta_id,
        "ganador_id": ofertante_id
    }
    