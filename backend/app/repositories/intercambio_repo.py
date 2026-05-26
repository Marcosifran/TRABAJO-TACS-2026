from bson import ObjectId
from app.schemas.intercambio_sch import IntercambioCreate
from app.core.database import get_db

def _get_collection():
    return get_db()["intercambios"]

def create_exchange(intercambio: IntercambioCreate, propuesto_por: int, solicitado_a: int) -> dict:
    oid = ObjectId()
    nuevo = {
        "_id": oid,
        "id": str(oid),
        "propuesto_por": propuesto_por,
        "solicitado_a": solicitado_a,
        "figuritas_ofrecidas": intercambio.figuritas_ofrecidas_numero,
        "figurita_solicitada": intercambio.figurita_solicitada_numero,
        "estado": "pendiente",
    }
    _get_collection().insert_one(nuevo)
    del nuevo["_id"]
    return nuevo

def list_exchanges() -> list[dict]:
    return list(_get_collection().find({}, {"_id": 0}))

def find_exchange_by_id(intercambio_id: str) -> dict | None:
    return _get_collection().find_one({"id": intercambio_id}, {"_id": 0})

def answer_exchange(intercambio_id: str, estado: str) -> dict | None:
    return _get_collection().find_one_and_update(
        {"id": intercambio_id},
        {"$set": {"estado": estado}},
        return_document=True,
        projection={"_id": 0}
    )

def find_exchanges_by_user(usuario_id: int) -> list[dict]:
    return list(_get_collection().find({"propuesto_por": usuario_id}, {"_id": 0}))

def find_exchanges_sent(usuario_id: int) -> list[dict]:
    return list(_get_collection().find({"propuesto_por": usuario_id}, {"_id": 0}))

def find_exchanges_received(usuario_id: int) -> list[dict]:
    return list(_get_collection().find({"solicitado_a": usuario_id}, {"_id": 0}))

def list_exchanges_by_user(usuario_id: int) -> dict[str, list[dict]]:
    enviados = find_exchanges_sent(usuario_id)
    recibidos = find_exchanges_received(usuario_id)
    return {"enviados": enviados, "recibidos": recibidos}
