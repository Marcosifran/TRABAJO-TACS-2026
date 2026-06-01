from typing import Any
from bson import ObjectId
from pymongo import ReturnDocument

from app.core.database import get_db
from app.domain.album import FiguritaAlbum
from app.schemas import FiguritaAlbumCreate


def _get_collection():
    return get_db()["album"]


def _from_doc(doc: dict) -> FiguritaAlbum:
    return FiguritaAlbum(
        id=doc["id"],
        usuario_id=doc["usuario_id"],
        numero=doc["numero"],
        equipo=doc["equipo"],
        jugador=doc["jugador"],
        cantidad=doc["cantidad"],
    )


def get_all() -> list[FiguritaAlbum]:
    return [_from_doc(doc) for doc in _get_collection().find({}, {"_id": 0})]


def get_by_id(figurita_id: str) -> FiguritaAlbum | None:
    doc = _get_collection().find_one({"id": figurita_id}, {"_id": 0})
    return _from_doc(doc) if doc else None


def get_by_user(usuario_id: int) -> list[FiguritaAlbum]:
    return [_from_doc(doc) for doc in _get_collection().find({"usuario_id": usuario_id}, {"_id": 0})]


def find(
    numero: int | None,
    equipo: str | None,
    jugador: str | None,
    usuario_id: int | None = None,
) -> list[FiguritaAlbum]:
    query: dict[str, Any] = {}
    if usuario_id is not None:
        query["usuario_id"] = usuario_id
    if numero is not None:
        query["numero"] = numero
    if equipo is not None:
        query["equipo"] = {"$regex": equipo, "$options": "i"}
    if jugador is not None:
        query["jugador"] = {"$regex": jugador, "$options": "i"}
    return [_from_doc(doc) for doc in _get_collection().find(query, {"_id": 0})]


def create(figurita: FiguritaAlbumCreate, usuario_id: int) -> FiguritaAlbum:
    oid = ObjectId()
    doc = figurita.model_dump()
    doc["_id"] = oid
    doc["id"] = str(oid)
    doc["usuario_id"] = usuario_id
    _get_collection().insert_one(doc)
    del doc["_id"]
    return _from_doc(doc)


def adjust_cantidad(figurita_id: str, delta: int) -> FiguritaAlbum | None:
    """Ajusta la cantidad en `delta`. Elimina la fila si llega a 0 o menos."""
    fig = get_by_id(figurita_id)
    if fig is None:
        return None
    nueva_cantidad = fig.cantidad + delta
    if nueva_cantidad <= 0:
        delete(figurita_id)
        return None
    doc = _get_collection().find_one_and_update(
        {"id": figurita_id},
        {"$set": {"cantidad": nueva_cantidad}},
        return_document=ReturnDocument.AFTER,
        projection={"_id": 0},
    )
    return _from_doc(doc) if doc else None


def transfer_to(figurita_id: str, new_usuario_id: int) -> FiguritaAlbum | None:
    doc = _get_collection().find_one_and_update(
        {"id": figurita_id},
        {"$set": {"usuario_id": new_usuario_id}},
        return_document=ReturnDocument.AFTER,
        projection={"_id": 0},
    )
    return _from_doc(doc) if doc else None


def delete(figurita_id: str) -> bool:
    res = _get_collection().delete_one({"id": figurita_id})
    return res.deleted_count > 0


def get_by_number_and_user(numero: int, usuario_id: int) -> FiguritaAlbum | None:
    doc = _get_collection().find_one({"numero": numero, "usuario_id": usuario_id}, {"_id": 0})
    return _from_doc(doc) if doc else None
