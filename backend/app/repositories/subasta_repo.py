import datetime as dt
from bson import ObjectId
from pymongo import ReturnDocument

from app.core.database import get_db
from app.domain.subasta import Subasta
from app.schemas import EstadoSubasta


def _get_collection():
    return get_db()["subastas"]


def _ensure_utc(d: dt.datetime) -> dt.datetime:
    if d.tzinfo is None:
        return d.replace(tzinfo=dt.timezone.utc)
    return d


def _from_doc(doc: dict) -> Subasta:
    return Subasta(
        id=doc["id"],
        figurita_id=doc["figurita_id"],
        usuario_id=doc["usuario_id"],
        inicio=_ensure_utc(doc["inicio"]),
        fin=_ensure_utc(doc["fin"]),
        estado=EstadoSubasta(doc["estado"]),
        figurita_jugador=doc.get("figurita_jugador"),
        figurita_equipo=doc.get("figurita_equipo"),
        figurita_numero=doc.get("figurita_numero"),
        oferta_ganadora_id=doc.get("oferta_ganadora_id"),
    )


def create(
    figurita_id: str,
    usuario_id: int,
    inicio: dt.datetime,
    fin: dt.datetime,
    figurita_jugador: str | None = None,
    figurita_equipo: str | None = None,
    figurita_numero: int | None = None,
) -> Subasta:
    ahora = dt.datetime.now(dt.timezone.utc)
    estado = EstadoSubasta.ACTIVA if inicio <= ahora <= fin else EstadoSubasta.INACTIVA
    oid = ObjectId()
    doc = {
        "_id": oid,
        "id": str(oid),
        "figurita_id": figurita_id,
        "usuario_id": usuario_id,
        "inicio": inicio,
        "fin": fin,
        "estado": estado.value,
        "figurita_jugador": figurita_jugador,
        "figurita_equipo": figurita_equipo,
        "figurita_numero": figurita_numero,
    }
    _get_collection().insert_one(doc)
    del doc["_id"]
    return _from_doc(doc)


def _expirar_vencidas() -> None:
    ahora = dt.datetime.now(dt.timezone.utc)
    _get_collection().update_many(
        {"estado": EstadoSubasta.ACTIVA.value, "fin": {"$lt": ahora}},
        {"$set": {"estado": EstadoSubasta.FINALIZADA.value}},
    )


def get_all_en_periodo(
    desde: dt.datetime | None = None,
    hasta: dt.datetime | None = None,
) -> list[Subasta]:
    _expirar_vencidas()
    filtro: dict = {"estado": EstadoSubasta.ACTIVA.value}
    if desde or hasta:
        oid: dict = {}
        if desde:
            oid["$gte"] = ObjectId.from_datetime(desde)
        if hasta:
            oid["$lt"] = ObjectId.from_datetime(hasta + dt.timedelta(days=1))
        filtro["_id"] = oid
    return [_from_doc(doc) for doc in _get_collection().find(filtro, {"_id": 0})]


def count_by_estado(estado: EstadoSubasta) -> int:
    return _get_collection().count_documents({"estado": estado.value})


def count_finalizadas_desde(desde: dt.datetime) -> int:
    return _get_collection().count_documents({
        "estado": EstadoSubasta.FINALIZADA.value,
        "fin": {"$gte": desde},
    })


def get_all(limit: int = 50, offset: int = 0) -> list[Subasta]:
    _expirar_vencidas()
    return [_from_doc(doc) for doc in _get_collection().find({"estado": EstadoSubasta.ACTIVA.value}, {"_id": 0}).skip(offset).limit(limit)]


def get_by_id(subasta_id: str) -> Subasta | None:
    doc = _get_collection().find_one({"id": subasta_id}, {"_id": 0})
    return _from_doc(doc) if doc else None


def get_by_figurita(figurita_id: str) -> Subasta | None:
    _expirar_vencidas()
    doc = _get_collection().find_one(
        {"figurita_id": figurita_id, "estado": EstadoSubasta.ACTIVA.value},
        {"_id": 0},
    )
    return _from_doc(doc) if doc else None


def get_by_user(usuario_id: int) -> list[Subasta]:
    return [_from_doc(doc) for doc in _get_collection().find({"usuario_id": usuario_id}, {"_id": 0})]


def finalize(subasta_id: str, oferta_ganadora_id: str) -> Subasta | None:
    doc = _get_collection().find_one_and_update(
        {"id": subasta_id},
        {
            "$set": {
                "estado": EstadoSubasta.FINALIZADA.value,
                "oferta_ganadora_id": oferta_ganadora_id,
            }
        },
        return_document=ReturnDocument.AFTER,
        projection={"_id": 0},
    )
    return _from_doc(doc) if doc else None


def cancel(subasta_id: str) -> Subasta | None:
    doc = _get_collection().find_one_and_update(
        {"id": subasta_id},
        {"$set": {"estado": EstadoSubasta.CANCELADA.value}},
        return_document=ReturnDocument.AFTER,
        projection={"_id": 0},
    )
    return _from_doc(doc) if doc else None
