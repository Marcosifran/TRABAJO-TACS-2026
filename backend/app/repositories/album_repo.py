from bson import ObjectId
from app.core.database import get_db
from app.schemas.album_sch import FiguritaAlbumCreate

def _get_collection():
    return get_db()["album"]

def get_all() -> list[dict]:
    return list(_get_collection().find({}, {"_id": 0}))

def get_by_id(figurita_id: str) -> dict | None:
    return _get_collection().find_one({"id": figurita_id}, {"_id": 0})

def get_by_usuario(usuario_id: int) -> list[dict]:
    return list(_get_collection().find({"usuario_id": usuario_id}, {"_id": 0}))

def buscar(numero: int | None, equipo: str | None, jugador: str | None, usuario_id: int | None = None) -> list[dict]:
    query = {}
    if usuario_id is not None: query["usuario_id"] = usuario_id
    if numero is not None: query["numero"] = numero
    if equipo is not None: query["equipo"] = {"$regex": equipo, "$options": "i"}
    if jugador is not None: query["jugador"] = {"$regex": jugador, "$options": "i"}
    return list(_get_collection().find(query, {"_id": 0}))

def create(figurita: FiguritaAlbumCreate, usuario_id: int) -> dict:
    oid = ObjectId()
    nueva = figurita.model_dump()
    nueva["_id"] = oid
    nueva["id"] = str(oid)
    nueva["usuario_id"] = usuario_id
    _get_collection().insert_one(nueva)
    del nueva["_id"]
    return nueva

def update_cantidad(figurita_id: str, cantidad: int) -> dict | None:
    """Actualiza la cantidad de una figurita en el album personal de un usuario.
    Retorna la figurita actualizada o None si no se encuentra."""
    return _get_collection().find_one_and_update(
        {"id": figurita_id},
        {"$set": {"cantidad": cantidad}},
        return_document=True,
        projection={"_id": 0}
    )

def delete(figurita_id: str) -> bool:
    """Elimina una figurita del album personal de un usuario."""
    res = _get_collection().delete_one({"id": figurita_id})
    return res.deleted_count > 0

def get_por_numero_y_usuario(numero: int, usuario_id: int) -> dict | None:
    return _get_collection().find_one({"numero": numero, "usuario_id": usuario_id}, {"_id": 0})

def update(figurita_actualizada: dict) -> dict:
    """Busca la figurita por id y actualiza los datos en la bd."""
    res = _get_collection().find_one_and_update(
        {"id": figurita_actualizada["id"]},
        {"$set": figurita_actualizada},
        return_document=True,
        projection={"_id": 0}
    )
    if not res:
        raise ValueError("No se pudo actualizar. Figurita no encontrada")
    return res
