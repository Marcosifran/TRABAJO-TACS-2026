from bson import ObjectId
from app.schemas.intercambio_sch import IntercambioCreate
from app.core.database import get_db

def _get_collection():
    return get_db()["intercambios"]

def crear_intercambio(intercambio: IntercambioCreate, propuesto_por: int, solicitado_a: int) -> dict:
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

def listar_intercambios() -> list[dict]:
    return list(_get_collection().find({}, {"_id": 0}))

def buscar_intercambio_por_id(intercambio_id: str) -> dict | None:
    return _get_collection().find_one({"id": intercambio_id}, {"_id": 0})

def responder_intercambio(intercambio_id: str, estado: str) -> dict | None:
    return _get_collection().find_one_and_update(
        {"id": intercambio_id},
        {"$set": {"estado": estado}},
        return_document=True,
        projection={"_id": 0}
    )

def buscar_intercambios_por_usuario(usuario_id: int) -> list[dict]:
    return list(_get_collection().find({"propuesto_por": usuario_id}, {"_id": 0}))

def buscar_intercambios_enviados(usuario_id: int) -> list[dict]:
    return list(_get_collection().find({"propuesto_por": usuario_id}, {"_id": 0}))

def buscar_intercambios_recibidos(usuario_id: int) -> list[dict]:
    return list(_get_collection().find({"solicitado_a": usuario_id}, {"_id": 0}))

def listar_intercambios_por_usuario(usuario_id: int) -> dict[str, list[dict]]:
    enviados = buscar_intercambios_enviados(usuario_id)
    recibidos = buscar_intercambios_recibidos(usuario_id)
    return {"enviados": enviados, "recibidos": recibidos}
