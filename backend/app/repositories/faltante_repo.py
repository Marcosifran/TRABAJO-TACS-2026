from bson import ObjectId
from app.core.config import settings
from app.core.database import get_db

def _get_faltantes_collection():
    return get_db()["faltantes"]


def get_missing(usuario_id: int) -> list[dict]:
    return list(_get_faltantes_collection().find({"usuario_id": usuario_id}, {"_id": 0}))

def create_missing(faltante_data: dict) -> dict:
    oid = ObjectId()
    faltante_data["_id"] = oid
    faltante_data["id"] = str(oid)
    _get_faltantes_collection().insert_one(faltante_data)
    del faltante_data["_id"]
    return faltante_data

def remove_missing(usuario_id: int, numero_figurita: int) -> bool:
    resultado = _get_faltantes_collection().delete_one({
        "usuario_id": usuario_id, 
        "numero_figurita": numero_figurita
    })
    return resultado.deleted_count > 0
