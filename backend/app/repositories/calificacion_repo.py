from app.core.database import get_db

def _get_collection():
    return get_db()["calificaciones"]

def crear(intercambio_id: int, calificador_id: int, calificado_id: int, puntuacion: int, comentario: str | None) -> dict:
    total = _get_collection().count_documents({})
    nuevo = {
        "id": total + 1,
        "intercambio_id": intercambio_id,
        "calificador_id": calificador_id,
        "calificado_id": calificado_id,
        "puntuacion": puntuacion,
        "comentario": comentario,
    }
    _get_collection().insert_one(nuevo)
    if "_id" in nuevo: del nuevo["_id"]
    return nuevo

def buscar_por_intercambio_y_calificador(intercambio_id: int, calificador_id: int) -> dict | None:
    return _get_collection().find_one({"intercambio_id": intercambio_id, "calificador_id": calificador_id}, {"_id": 0})

def listar_por_calificado(calificado_id: int) -> list[dict]:
    return list(_get_collection().find({"calificado_id": calificado_id}, {"_id": 0}))
