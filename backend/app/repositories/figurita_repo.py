from typing import Any
from bson import ObjectId
from app.schemas.figurita import FiguritaCreate
from app.core.database import get_db

def _get_collection():
    return get_db()["figuritas"]

def get_all() -> list[dict]:
    return list(_get_collection().find({}, {"_id": 0}))

def get_by_id(figurita_id: str) -> dict | None:
    return _get_collection().find_one({"id": figurita_id}, {"_id": 0})

def find_by_number_and_user(numero: int, usuario_id: int) -> dict | None:
    return _get_collection().find_one({"numero": numero, "usuario_id": usuario_id}, {"_id": 0})

def find(numero: int | None, equipo: str | None, jugador: str | None) -> list[dict]:
    """Filtra las figuritas disponibles según criterios opcionales."""
    query: dict[str, Any] = {}
    if numero is not None:
        query["numero"] = numero
    if equipo is not None:
        query["equipo"] = {"$regex": equipo, "$options": "i"}
    if jugador is not None:
        query["jugador"] = {"$regex": jugador, "$options": "i"}
    return list(_get_collection().find(query, {"_id": 0}))

def get_by_user_id(usuario_id: int) -> list[dict]:
    return list(_get_collection().find({"usuario_id": usuario_id}, {"_id": 0}))

def get_suggestions(numeros_faltantes: list[int], usuario_id: int) -> list[dict]:
    return list(_get_collection().find({
        "numero": {"$in": numeros_faltantes},
        "usuario_id": {"$ne": usuario_id}
    }, {"_id": 0}))

def create(figurita: FiguritaCreate, usuario_id: int) -> dict:
    oid = ObjectId()
    nueva = figurita.model_dump()
    nueva["_id"] = oid
    nueva["id"] = str(oid)
    nueva["usuario_id"] = usuario_id
    _get_collection().insert_one(nueva)
    del nueva["_id"]
    return nueva

def delete(figurita_id: str) -> bool:
    res = _get_collection().delete_one({"id": figurita_id})
    return res.deleted_count > 0
