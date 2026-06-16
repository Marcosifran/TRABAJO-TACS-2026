import datetime as dt
from bson import ObjectId
from pymongo import ReturnDocument

from app.core.database import get_db
from app.domain.intercambio import Intercambio
from app.schemas import IntercambioCreate, EstadoIntercambio


def _oid_range(desde: dt.datetime | None, hasta: dt.datetime | None) -> dict:
    if not desde and not hasta:
        return {}
    filtro: dict = {}
    if desde:
        filtro["$gte"] = ObjectId.from_datetime(desde)
    if hasta:
        filtro["$lt"] = ObjectId.from_datetime(hasta + dt.timedelta(days=1))
    return {"_id": filtro}


def _get_collection():
    return get_db()["intercambios"]


def _from_doc(doc: dict) -> Intercambio:
    return Intercambio(
        id=doc["id"],
        propuesto_por=doc["propuesto_por"],
        solicitado_a=doc["solicitado_a"],
        figuritas_ofrecidas=doc["figuritas_ofrecidas"],
        figurita_solicitada=doc["figurita_solicitada"],
        estado=EstadoIntercambio(doc["estado"]),
    )


def create_exchange(intercambio: IntercambioCreate, propuesto_por: int, solicitado_a: int) -> Intercambio:
    oid = ObjectId()
    doc = {
        "_id": oid,
        "id": str(oid),
        "propuesto_por": propuesto_por,
        "solicitado_a": solicitado_a,
        "figuritas_ofrecidas": intercambio.figuritas_ofrecidas_numero,
        "figurita_solicitada": intercambio.figurita_solicitada_numero,
        "estado": EstadoIntercambio.PENDIENTE.value,
    }
    _get_collection().insert_one(doc)
    del doc["_id"]
    return _from_doc(doc)


def list_exchanges() -> list[Intercambio]:
    return [_from_doc(doc) for doc in _get_collection().find({}, {"_id": 0})]


def list_exchanges_en_periodo(
    desde: dt.datetime | None = None,
    hasta: dt.datetime | None = None,
) -> list[Intercambio]:
    query = _oid_range(desde, hasta)
    return [_from_doc(doc) for doc in _get_collection().find(query, {"_id": 0})]


def find_exchange_by_id(intercambio_id: str) -> Intercambio | None:
    doc = _get_collection().find_one({"id": intercambio_id}, {"_id": 0})
    return _from_doc(doc) if doc else None


def answer_exchange(intercambio_id: str, estado: str) -> Intercambio | None:
    doc = _get_collection().find_one_and_update(
        {"id": intercambio_id},
        {"$set": {"estado": estado}},
        return_document=ReturnDocument.AFTER,
        projection={"_id": 0},
    )
    return _from_doc(doc) if doc else None


def find_exchanges_sent(usuario_id: int) -> list[Intercambio]:
    return [_from_doc(doc) for doc in _get_collection().find({"propuesto_por": usuario_id}, {"_id": 0})]


def find_exchanges_received(usuario_id: int) -> list[Intercambio]:
    return [_from_doc(doc) for doc in _get_collection().find({"solicitado_a": usuario_id}, {"_id": 0})]


def list_exchanges_by_user(usuario_id: int) -> dict[str, list[Intercambio]]:
    return {
        "enviados": find_exchanges_sent(usuario_id),
        "recibidos": find_exchanges_received(usuario_id),
    }


def crear_intercambio(intercambio: IntercambioCreate, propuesto_por: int, solicitado_a: int) -> Intercambio:
    return create_exchange(intercambio, propuesto_por, solicitado_a)


def listar_intercambios_por_usuario(usuario_id: int) -> dict[str, list[Intercambio]]:
    return list_exchanges_by_user(usuario_id)
