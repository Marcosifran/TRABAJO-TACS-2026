from bson import ObjectId

from app.core.database import get_db
from app.domain.oferta import Oferta


def _get_collection():
    return get_db()["ofertas"]


def _from_doc(doc: dict) -> Oferta:
    return Oferta(
        id=doc["id"],
        subasta_id=doc["subasta_id"],
        usuario_id=doc["usuario_id"],
        ofrecidas=doc["ofrecidas"],
    )


def create_offer(subasta_id: str, ofrecidas: list[str], usuario_id: int) -> Oferta:
    oid = ObjectId()
    doc = {
        "_id": oid,
        "id": str(oid),
        "subasta_id": subasta_id,
        "ofrecidas": ofrecidas,
        "usuario_id": usuario_id,
    }
    _get_collection().insert_one(doc)
    del doc["_id"]
    return _from_doc(doc)


def get_all() -> list[Oferta]:
    return [_from_doc(doc) for doc in _get_collection().find({}, {"_id": 0})]


def get_by_auction(subasta_id: str) -> list[Oferta]:
    return [_from_doc(doc) for doc in _get_collection().find({"subasta_id": subasta_id}, {"_id": 0})]


def get_by_user(usuario_id: int) -> list[Oferta]:
    return [_from_doc(doc) for doc in _get_collection().find({"usuario_id": usuario_id}, {"_id": 0})]


def get_by_id(oferta_id: str) -> Oferta | None:
    doc = _get_collection().find_one({"id": oferta_id}, {"_id": 0})
    return _from_doc(doc) if doc else None


def delete(oferta_id: str) -> bool:
    res = _get_collection().delete_one({"id": oferta_id})
    return res.deleted_count > 0
