import datetime as dt
from bson import ObjectId
from app.core.database import get_db
from app.schemas.subasta import EstadoSubasta

def _get_collection():
    return get_db()["subastas"]

def create(figurita_id: str, usuario_id: int, inicio: dt.datetime, fin: dt.datetime) -> dict:
    ahora = dt.datetime.now(dt.timezone.utc)
    estado = EstadoSubasta.ACTIVA.value if inicio <= ahora <= fin else EstadoSubasta.INACTIVA.value
    oid = ObjectId()
    nueva_subasta = {
        "_id": oid,
        "id": str(oid),
        "figurita_id": figurita_id,
        "usuario_id": usuario_id,
        "inicio": inicio,
        "fin": fin,
        "estado": estado
    }
    _get_collection().insert_one(nueva_subasta)
    del nueva_subasta["_id"]
    return nueva_subasta

def get_all() -> list[dict]:
    return list(_get_collection().find({"estado": EstadoSubasta.ACTIVA.value}, {"_id": 0}))

def get_by_id(subasta_id: str) -> dict | None:
    return _get_collection().find_one({"id": subasta_id}, {"_id": 0})

def get_by_figurita(figurita_id: str) -> dict | None:
    return _get_collection().find_one(
        {"figurita_id": figurita_id, "estado": EstadoSubasta.ACTIVA.value}, {"_id": 0}
    )

def get_by_user(usuario_id: int) -> list[dict]:
    return list(_get_collection().find({"usuario_id": usuario_id}, {"_id": 0}))

def update(subasta_actualizada: dict) -> dict:
    res = _get_collection().find_one_and_update(
        {"id": subasta_actualizada["id"]},
        {"$set": subasta_actualizada},
        return_document=True,
        projection={"_id": 0}
    )
    if not res:
        raise ValueError(f"No se encontro la subasta de id {subasta_actualizada['id']}")
    return res
