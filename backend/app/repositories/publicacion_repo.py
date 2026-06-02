from typing import Any
from bson import ObjectId
from pymongo import ReturnDocument

from app.core.database import get_db
from app.domain.publicacion import Publicacion
from app.schemas import PublicacionCreate, TipoIntercambio


def _get_collection():
    return get_db()["publicaciones"]


def _from_doc(doc: dict) -> Publicacion:
    return Publicacion(
        id=doc["id"],
        usuario_id=doc["usuario_id"],
        figurita_personal_id=doc["figurita_personal_id"],
        tipo_intercambio=TipoIntercambio(doc["tipo_intercambio"]),
        cantidad_disponible=doc["cantidad_disponible"],
        numero=doc["numero"],
        equipo=doc["equipo"],
        jugador=doc["jugador"],
    )


def get_all() -> list[Publicacion]:
    return [_from_doc(doc) for doc in _get_collection().find({}, {"_id": 0})]


def get_by_id(publicacion_id: str) -> Publicacion | None:
    doc = _get_collection().find_one({"id": publicacion_id}, {"_id": 0})
    return _from_doc(doc) if doc else None


def get_by_user(usuario_id: int) -> list[Publicacion]:
    return [_from_doc(doc) for doc in _get_collection().find({"usuario_id": usuario_id}, {"_id": 0})]


def get_by_personal_figurita(figurita_personal_id: str) -> Publicacion | None:
    doc = _get_collection().find_one({"figurita_personal_id": figurita_personal_id}, {"_id": 0})
    return _from_doc(doc) if doc else None


def find(
    numero: int | None,
    equipo: str | None,
    jugador: str | None,
    tipo_intercambio: str | None = None,
    usuario_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Publicacion]:
    query: dict[str, Any] = {}
    if numero is not None:
        query["numero"] = numero
    if equipo is not None:
        query["equipo"] = {"$regex": equipo, "$options": "i"}
    if jugador is not None:
        query["jugador"] = {"$regex": jugador, "$options": "i"}
    if tipo_intercambio is not None:
        query["tipo_intercambio"] = {"$regex": f"^{tipo_intercambio}$", "$options": "i"}
    if usuario_id is not None:
        query["usuario_id"] = {"$ne": usuario_id}
    return [_from_doc(doc) for doc in _get_collection().find(query, {"_id": 0}).skip(offset).limit(limit)]


def create(
    publicacion: PublicacionCreate,
    usuario_id: int,
    numero: int,
    equipo: str,
    jugador: str,
) -> Publicacion:
    oid = ObjectId()
    doc = {
        "_id": oid,
        "id": str(oid),
        "usuario_id": usuario_id,
        "figurita_personal_id": publicacion.figurita_personal_id,
        "tipo_intercambio": publicacion.tipo_intercambio.value,
        "cantidad_disponible": publicacion.cantidad_disponible,
        "numero": numero,
        "equipo": equipo,
        "jugador": jugador,
    }
    _get_collection().insert_one(doc)
    del doc["_id"]
    return _from_doc(doc)


def adjust_cantidad(publicacion_id: str, delta: int) -> Publicacion | None:
    pub = get_by_id(publicacion_id)
    if pub is None:
        return None
    nueva_cantidad = pub.cantidad_disponible + delta
    if nueva_cantidad <= 0:
        delete(publicacion_id)
        return None
    doc = _get_collection().find_one_and_update(
        {"id": publicacion_id},
        {"$set": {"cantidad_disponible": nueva_cantidad}},
        return_document=ReturnDocument.AFTER,
        projection={"_id": 0},
    )
    return _from_doc(doc) if doc else None


def delete(publicacion_id: str) -> bool:
    res = _get_collection().delete_one({"id": publicacion_id})
    return res.deleted_count > 0
