import datetime as dt
from typing import Any

from app.repositories import subasta_repo, publicacion_repo, oferta_repo, album_repo
from app.schemas import SubastaCreate, EstadoSubasta, TipoIntercambio
from app.schemas import OfertaCreate
from app.domain.subasta import Subasta
from app.domain.oferta import Oferta
from app.domain.album import FiguritaAlbum
from app.domain.errors import (
    DomainNotFoundError,
    DomainValidationError,
    DomainPermissionError,
    DomainConflictError,
)


def _esta_activa(subasta: Subasta) -> bool:
    if subasta.estado != EstadoSubasta.ACTIVA:
        return False
    ahora = dt.datetime.now(dt.timezone.utc)
    fin = subasta.fin
    if isinstance(fin, str):
        fin = dt.datetime.fromisoformat(fin)
    if fin.tzinfo is None:
        fin = fin.replace(tzinfo=dt.timezone.utc)
    return ahora <= fin


def _figurita_detalle(fig: FiguritaAlbum) -> dict[str, Any]:
    return {
        "id": fig.id,
        "numero": fig.numero,
        "equipo": fig.equipo,
        "jugador": fig.jugador,
    }


def _subasta_a_dict(subasta: Subasta) -> dict[str, Any]:
    return {
        "id": subasta.id,
        "figurita_id": subasta.figurita_id,
        "usuario_id": subasta.usuario_id,
        "inicio": subasta.inicio,
        "fin": subasta.fin,
        "estado": subasta.estado.value,
        "figurita_jugador": subasta.figurita_jugador,
        "figurita_equipo": subasta.figurita_equipo,
        "figurita_numero": subasta.figurita_numero,
        "oferta_ganadora_id": subasta.oferta_ganadora_id,
    }


def _oferta_a_dict(oferta: Oferta) -> dict[str, Any]:
    return {
        "id": oferta.id,
        "subasta_id": oferta.subasta_id,
        "usuario_id": oferta.usuario_id,
        "ofrecidas": oferta.ofrecidas,
    }


def crear_subasta(subasta_data: SubastaCreate, usuario_id: int) -> dict:
    publicacion = publicacion_repo.get_by_id(subasta_data.figurita_id)

    if not publicacion:
        raise DomainNotFoundError("Publicación inexistente")

    if publicacion.usuario_id != usuario_id:
        raise DomainPermissionError("No podés subastar una publicación que no es tuya")

    if publicacion.tipo_intercambio != TipoIntercambio.SUBASTA:
        raise DomainValidationError("Esta publicación no está configurada para subasta")

    if subasta_repo.get_by_figurita(subasta_data.figurita_id):
        raise DomainConflictError("Esta figurita ya se encuentra en subasta")

    creada = subasta_repo.create(
        subasta_data.figurita_id,
        usuario_id,
        subasta_data.inicio,
        subasta_data.fin,
        figurita_jugador=publicacion.jugador,
        figurita_equipo=publicacion.equipo,
        figurita_numero=publicacion.numero,
    )
    return _subasta_a_dict(creada)


def listar_subastas(limit: int = 50, offset: int = 0) -> list[dict]:
    return [_subasta_a_dict(s) for s in subasta_repo.get_all(limit=limit, offset=offset)]


def listar_ofertas(subasta_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
    subasta = subasta_repo.get_by_id(subasta_id)
    if not subasta:
        raise DomainNotFoundError("Subasta no encontrada")
    result = []
    for oferta in oferta_repo.get_by_auction(subasta_id, limit=limit, offset=offset):
        enriquecida = _oferta_a_dict(oferta)
        enriquecida["ofrecidas_detalle"] = [
            _figurita_detalle(fig)
            for album_id in oferta.ofrecidas
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

    if subasta.usuario_id == usuario_id:
        raise DomainPermissionError("No podés ofertar en tu propia subasta")

    ofertas_existentes = oferta_repo.get_by_auction(subasta_id)
    if any(o.usuario_id == usuario_id for o in ofertas_existentes):
        raise DomainConflictError("Ya enviaste una oferta a esta subasta")

    if not oferta_data.figuritas_ofrecidas:
        raise DomainValidationError("Debés ofrecer al menos una figurita")

    todas = album_repo.get_all()
    ofrecidas = [f for f in todas if f.id in oferta_data.figuritas_ofrecidas]

    ids_no_encontrados = set(oferta_data.figuritas_ofrecidas) - {f.id for f in ofrecidas}
    if ids_no_encontrados:
        raise DomainNotFoundError(f"Las figuritas {list(ids_no_encontrados)} no existen")

    if any(f.usuario_id != usuario_id for f in ofrecidas):
        raise DomainPermissionError("No podés ofrecer una figurita que no es tuya")

    creada = oferta_repo.create_offer(subasta_id, [f.id for f in ofrecidas], usuario_id)
    return _oferta_a_dict(creada)


def cancelar_oferta(oferta_id: str, usuario_id: int) -> None:
    oferta = oferta_repo.get_by_id(oferta_id)
    if not oferta:
        raise DomainNotFoundError("Oferta no encontrada")
    if oferta.usuario_id != usuario_id:
        raise DomainPermissionError("No podés cancelar una oferta que no es tuya")
    subasta = subasta_repo.get_by_id(oferta.subasta_id)
    if not subasta or not _esta_activa(subasta):
        raise DomainValidationError("Solo podés cancelar ofertas de subastas activas")
    oferta_repo.delete(oferta_id)


def _rechazar_oferta(oferta_id: str, subasta_id: str, usuario_id: int) -> None:
    oferta = oferta_repo.get_by_id(oferta_id)
    if not oferta:
        raise DomainNotFoundError("Oferta no encontrada")
    if oferta.subasta_id != subasta_id:
        raise DomainValidationError("La oferta no pertenece a esta subasta")
    subasta = subasta_repo.get_by_id(subasta_id)
    if not subasta:
        raise DomainNotFoundError("Subasta no encontrada")
    if subasta.usuario_id != usuario_id:
        raise DomainPermissionError("Solo el creador de la subasta puede rechazar ofertas")
    oferta_repo.delete(oferta_id)


def _aceptar_oferta(subasta_id: str, oferta_id: str, usuario_id: int) -> dict:
    subasta = subasta_repo.get_by_id(subasta_id)
    if not subasta:
        raise DomainNotFoundError("Subasta no encontrada")

    if subasta.usuario_id != usuario_id:
        raise DomainPermissionError("No podés aceptar una oferta que no es tuya")

    if subasta.estado == EstadoSubasta.INACTIVA:
        raise DomainValidationError("La subasta aún no comenzó")

    if subasta.oferta_ganadora_id:
        raise DomainValidationError("Esta subasta ya tiene una oferta ganadora")

    oferta = oferta_repo.get_by_id(oferta_id)
    if not oferta:
        raise DomainNotFoundError("Oferta no encontrada")

    if oferta.subasta_id != subasta_id:
        raise DomainValidationError("La oferta no pertenece a esta subasta")

    ofertante_id = oferta.usuario_id
    figurita_subastada_id = subasta.figurita_id
    figuritas_ofrecidas_ids = oferta.ofrecidas

    publicacion = publicacion_repo.get_by_id(figurita_subastada_id)
    if not publicacion:
        raise DomainNotFoundError("Publicación no encontrada")

    album_repo.transfer_to(publicacion.figurita_personal_id, ofertante_id)

    for fig_id in figuritas_ofrecidas_ids:
        album_repo.transfer_to(fig_id, usuario_id)
        pub_fantasma = publicacion_repo.get_by_personal_figurita(fig_id)
        if pub_fantasma:
            publicacion_repo.delete(pub_fantasma.id)

    subasta_repo.finalize(subasta_id, oferta_id)
    publicacion_repo.delete(figurita_subastada_id)

    return {
        "subasta_id": subasta_id,
        "estado": EstadoSubasta.FINALIZADA.value,
        "ganador_id": ofertante_id,
    }


def responder_oferta(subasta_id: str, oferta_id: str, estado: str, usuario_id: int) -> dict | None:
    if estado == "aceptada":
        return _aceptar_oferta(subasta_id, oferta_id, usuario_id)
    if estado == "rechazada":
        _rechazar_oferta(oferta_id, subasta_id, usuario_id)
        return None
    raise DomainValidationError(f"Estado de oferta inválido: {estado}")


def cancelar_subasta(subasta_id: str, usuario_id: int) -> None:
    subasta = subasta_repo.get_by_id(subasta_id)
    if not subasta:
        raise DomainNotFoundError("Subasta no encontrada")
    if subasta.usuario_id != usuario_id:
        raise DomainPermissionError("Solo el creador puede cancelar la subasta")
    if subasta.oferta_ganadora_id:
        raise DomainValidationError("No podés cancelar una subasta que ya tiene oferta aceptada")
    if subasta.estado in (EstadoSubasta.FINALIZADA, EstadoSubasta.CANCELADA):
        raise DomainValidationError("La subasta ya está finalizada o cancelada")
    for oferta in oferta_repo.get_by_auction(subasta_id):
        oferta_repo.delete(oferta.id)
    subasta_repo.cancel(subasta_id)


def listar_subastas_usuario(usuario_id: int) -> list[dict]:
    return [_subasta_a_dict(s) for s in subasta_repo.get_by_user(usuario_id)]


def listar_mis_ofertas(usuario_id: int) -> list[dict]:
    ofertas = oferta_repo.get_by_user(usuario_id)
    result = []
    for oferta in ofertas:
        enriquecida = _oferta_a_dict(oferta)
        subasta = subasta_repo.get_by_id(oferta.subasta_id)
        enriquecida["subasta"] = _subasta_a_dict(subasta) if subasta else None
        if subasta:
            pub = publicacion_repo.get_by_id(subasta.figurita_id)
            if pub:
                enriquecida["figurita_subastada"] = {
                    "jugador": pub.jugador,
                    "equipo": pub.equipo,
                    "numero": pub.numero,
                }
            elif subasta.figurita_jugador:
                enriquecida["figurita_subastada"] = {
                    "jugador": subasta.figurita_jugador,
                    "equipo": subasta.figurita_equipo,
                    "numero": subasta.figurita_numero,
                }
            else:
                enriquecida["figurita_subastada"] = None
        enriquecida["ofrecidas_detalle"] = [
            _figurita_detalle(fig)
            for album_id in oferta.ofrecidas
            if (fig := album_repo.get_by_id(album_id))
        ]
        result.append(enriquecida)
    return result
