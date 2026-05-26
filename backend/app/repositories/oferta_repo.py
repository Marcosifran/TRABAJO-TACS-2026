from bson import ObjectId
from app.core.database import get_db

def _get_collection():
    return get_db()["ofertas"]

def create_offer(subasta_id: str, ofrecidas: list[str], usuario_id: int) -> dict:
    oid = ObjectId()
    nueva_oferta = {
        "_id": oid,
        "id": str(oid),
        "subasta_id": subasta_id,
        "ofrecidas": ofrecidas,
        "usuario_id": usuario_id
    }
    _get_collection().insert_one(nueva_oferta)
    del nueva_oferta["_id"]
    return nueva_oferta

def get_all() -> list[dict]:
    return list(_get_collection().find({}, {"_id": 0}))

def get_by_auction(subasta_id: str) -> list[dict]:
    return list(_get_collection().find({"subasta_id": subasta_id}, {"_id": 0}))

def get_by_user(usuario_id: int) -> list[dict]:
    return list(_get_collection().find({"usuario_id": usuario_id}, {"_id": 0}))

def get_by_id(oferta_id: str) -> dict | None:
    return _get_collection().find_one({"id": oferta_id}, {"_id": 0})

def delete(oferta_id: str) -> bool:
    res = _get_collection().delete_one({"id": oferta_id})
    return res.deleted_count > 0
