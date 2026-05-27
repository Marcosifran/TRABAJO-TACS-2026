from bson import ObjectId
from app.core.database import get_db

def _get_collection():
    return get_db()["calificaciones"]

def create(intercambio_id: str, calificador_id: int, calificado_id: int, puntuacion: int, comentario: str | None) -> dict:
    oid = ObjectId()
    nuevo = {
        "_id": oid,
        "id": str(oid),
        "intercambio_id": intercambio_id,
        "calificador_id": calificador_id,
        "calificado_id": calificado_id,
        "puntuacion": puntuacion,
        "comentario": comentario,
    }
    _get_collection().insert_one(nuevo)
    del nuevo["_id"]
    return nuevo

def find_by_exchange_and_qualifier(exchange_id: str, califier_id: int) -> dict | None:
    return _get_collection().find_one({"intercambio_id": exchange_id, "calificador_id": califier_id}, {"_id": 0})

def list_by_qualified(calificado_id: int) -> list[dict]:
    return list(_get_collection().find({"calificado_id": calificado_id}, {"_id": 0}))


# Spanish compatibility wrapper
def buscar_por_intercambio_y_calificador(intercambio_id: str, calificador_id: int) -> dict | None:
    return find_by_exchange_and_qualifier(intercambio_id, calificador_id)
