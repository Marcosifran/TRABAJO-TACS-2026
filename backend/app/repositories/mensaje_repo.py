import datetime as dt
from bson import ObjectId
from app.core.database import get_db

def _get_collection():
    return get_db()["mensajes"]

def crear_mensaje(intercambio_id: str, remitente_id: int, contenido: str) -> dict:
    oid = ObjectId()
    nuevo = {
        "_id": oid,
        "id": str(oid),
        "intercambio_id": intercambio_id,
        "remitente_id": remitente_id,
        "contenido": contenido,
        "fecha_envio": dt.datetime.now()
    }
    _get_collection().insert_one(nuevo)
    del nuevo["_id"]
    return nuevo

def listar_mensajes_por_intercambio(intercambio_id: str) -> list[dict]:
    return list(_get_collection().find({"intercambio_id": intercambio_id}, {"_id": 0}).sort("fecha_envio", 1))
