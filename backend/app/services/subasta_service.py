import datetime as dt
from app.repositories import subasta_repo, publicacion_repo, oferta_repo, album_repo
from app.schemas.subasta import SubastaCreate
from app.schemas.oferta import OfertaCreate
from app.domain.errors import (
    DomainNotFoundError,
    DomainValidationError,
    DomainPermissionError,
    DomainConflictError,
)


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
    publicacion = publicacion_repo.get_by_id(subasta_data.figurita_id)

    if not publicacion:
        raise DomainNotFoundError("Publicación inexistente")

    if publicacion["usuario_id"] != usuario_id:
        raise DomainPermissionError("No podés subastar una publicación que no es tuya")

    if publicacion.get("tipo_intercambio") != "subasta":
        raise DomainValidationError("Esta publicación no está configurada para subasta")

    if subasta_repo.get_by_figurita(subasta_data.figurita_id):
        raise DomainConflictError("Esta figurita ya se encuentra en subasta")

    return subasta_repo.create(
        subasta_data.figurita_id, usuario_id, subasta_data.inicio, subasta_data.fin
    )


def listar_subastas() -> list[dict]:
    return subasta_repo.get_all()


def listar_ofertas(subasta_id: str) -> list[dict]:
    subasta = subasta_repo.get_by_id(subasta_id)
    if not subasta:
        raise DomainNotFoundError("Subasta no encontrada")
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
    subasta = subasta_repo.get_by_id(subasta_id)

    if not subasta:
        raise DomainNotFoundError("Subasta no encontrada")

    if not _esta_activa(subasta):
        raise DomainValidationError("La subasta no está activa o ya finalizó")

    if subasta["usuario_id"] == usuario_id:
        raise DomainPermissionError("No podés ofertar en tu propia subasta")

    ofertas_existentes = oferta_repo.get_by_auction(subasta_id)
    if any(o["usuario_id"] == usuario_id for o in ofertas_existentes):
        raise DomainConflictError("Ya enviaste una oferta a esta subasta")

    if not oferta_data.figuritas_ofrecidas:
        raise DomainValidationError("Debés ofrecer al menos una figurita")

    todas = album_repo.get_all()
    ofrecidas = [f for f in todas if f["id"] in oferta_data.figuritas_ofrecidas]

    ids_no_encontrados = set(oferta_data.figuritas_ofrecidas) - {f["id"] for f in ofrecidas}
    if ids_no_encontrados:
        raise DomainNotFoundError(f"Las figuritas {list(ids_no_encontrados)} no existen")

    if any(f["usuario_id"] != usuario_id for f in ofrecidas):
        raise DomainPermissionError("No podés ofrecer una figurita que no es tuya")

    return oferta_repo.create_offer(subasta_id, [f["id"] for f in ofrecidas], usuario_id)


def cancelar_oferta(oferta_id: str, usuario_id: int) -> None:
    oferta = oferta_repo.get_by_id(oferta_id)
    if not oferta:
        raise DomainNotFoundError("Oferta no encontrada")
    if oferta["usuario_id"] != usuario_id:
        raise DomainPermissionError("No podés cancelar una oferta que no es tuya")
    subasta = subasta_repo.get_by_id(oferta["subasta_id"])
    if not subasta or not _esta_activa(subasta):
        raise DomainValidationError("Solo podés cancelar ofertas de subastas activas")
    oferta_repo.delete(oferta_id)


def _rechazar_oferta(oferta_id: str, subasta_id: str, usuario_id: int) -> None:
    oferta = oferta_repo.get_by_id(oferta_id)
    if not oferta:
        raise DomainNotFoundError("Oferta no encontrada")
    if oferta["subasta_id"] != subasta_id:
        raise DomainValidationError("La oferta no pertenece a esta subasta")
    subasta = subasta_repo.get_by_id(subasta_id)
    if not subasta:
        raise DomainNotFoundError("Subasta no encontrada")
    if subasta["usuario_id"] != usuario_id:
        raise DomainPermissionError("Solo el creador de la subasta puede rechazar ofertas")
    oferta_repo.delete(oferta_id)


def _aceptar_oferta(subasta_id: str, oferta_id: str, usuario_id: int) -> dict:
    subasta = subasta_repo.get_by_id(subasta_id)
    if not subasta:
        raise DomainNotFoundError("Subasta no encontrada")

    if subasta["usuario_id"] != usuario_id:
        raise DomainPermissionError("No podés aceptar una oferta que no es tuya")

    if not _esta_activa(subasta):
        raise DomainValidationError("La subasta no está activa o ya finalizó")

    oferta = oferta_repo.get_by_id(oferta_id)
    if not oferta:
        raise DomainNotFoundError("Oferta no encontrada")

    if oferta["subasta_id"] != subasta_id:
        raise DomainValidationError("La oferta no pertenece a esta subasta")

    ofertante_id = oferta["usuario_id"]
    figurita_subastada_id = subasta["figurita_id"]
    figuritas_ofrecidas_ids = oferta["ofrecidas"]

    publicacion = publicacion_repo.get_by_id(figurita_subastada_id)
    if not publicacion:
        raise DomainNotFoundError("Publicación no encontrada")

    figurita_album = album_repo.get_by_id(publicacion["figurita_personal_id"])
    if figurita_album:
        figurita_album["usuario_id"] = ofertante_id
        album_repo.update(figurita_album)

    for fig_id in figuritas_ofrecidas_ids:
        fig_ofrecida = album_repo.get_by_id(fig_id)
        if fig_ofrecida:
            fig_ofrecida["usuario_id"] = usuario_id
            album_repo.update(fig_ofrecida)
            pub_fantasma = publicacion_repo.get_by_personal_figurita(fig_id)
            if pub_fantasma:
                publicacion_repo.delete(pub_fantasma["id"])

    subasta["estado"] = "finalizada"
    subasta["oferta_ganadora_id"] = oferta_id
    subasta_repo.update(subasta)
    publicacion_repo.delete(figurita_subastada_id)

    return {
        "subasta_id": subasta_id,
        "estado": "finalizada",
        "ganador_id": ofertante_id,
    }


def responder_oferta(subasta_id: str, oferta_id: str, estado: str, usuario_id: int) -> dict | None:
    """Acepta o rechaza una oferta. Devuelve el resultado en aceptación, None en rechazo (204)."""
    if estado == "aceptada":
        return _aceptar_oferta(subasta_id, oferta_id, usuario_id)
    if estado == "rechazada":
        _rechazar_oferta(oferta_id, subasta_id, usuario_id)
        return None
    raise DomainValidationError(f"Estado de oferta inválido: {estado}")


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
