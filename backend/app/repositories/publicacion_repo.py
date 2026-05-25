from bson import ObjectId
from app.schemas.publicacion_sch import PublicacionCreate
from app.core.database import get_db

"""Repositorio de publicaciones, maneja las operaciones relacionadas con las publicaciones de intercambio."""

def _get_collection():
    return get_db()["publicaciones"]

def get_all() -> list[dict]:
    """Obtiene todas las publicaciones de intercambio."""
    return list(_get_collection().find({}, {"_id": 0}))

def get_by_id(publicacion_id: str) -> dict | None:
    """Obtiene una publicación por su ID."""
    return _get_collection().find_one({"id": publicacion_id}, {"_id": 0})

def get_by_usuario(usuario_id: int) -> list[dict]:
    """Obtiene todas las publicaciones de un usuario específico."""
    return list(_get_collection().find({"usuario_id": usuario_id}, {"_id": 0}))

def get_by_figurita_personal(figurita_personal_id: str) -> dict | None:
    """Obtiene la publicación activa que ofrece una figurita personal específica."""
    return _get_collection().find_one({"figurita_personal_id": figurita_personal_id}, {"_id": 0})

def buscar(
        numero: int | None,
        equipo: str | None,
        jugador: str | None,
        tipo_intercambio: str | None = None,
        usuario_id: int | None = None,
) -> list[dict]:
    """Busca publicaciones por número, equipo, jugador o usuario."""
    query = {}
    if numero is not None: query["numero"] = numero
    if equipo is not None: query["equipo"] = {"$regex": equipo, "$options": "i"}
    if jugador is not None: query["jugador"] = {"$regex": jugador, "$options": "i"}
    if tipo_intercambio is not None: query["tipo_intercambio"] = {"$regex": f"^{tipo_intercambio}$", "$options": "i"}
    if usuario_id is not None: query["usuario_id"] = {"$ne": usuario_id}
    return list(_get_collection().find(query, {"_id": 0}))

def create(
        publicacion: PublicacionCreate,
        usuario_id: int,
        numero: int,
        equipo: str,
        jugador: str
) -> dict:
    """Crea una nueva publicación de intercambio."""
    oid = ObjectId()
    nueva = {
        "_id": oid,
        "id": str(oid),
        "usuario_id": usuario_id,
        "figurita_personal_id": publicacion.figurita_personal_id,
        "tipo_intercambio": publicacion.tipo_intercambio.value,
        "cantidad_disponible": publicacion.cantidad_disponible,
        "numero": numero,
        "equipo": equipo,
        "jugador": jugador
    }
    _get_collection().insert_one(nueva)
    del nueva["_id"]
    return nueva

def delete(publicacion_id: str) -> bool:
    """Elimina una publicación de intercambio."""
    res = _get_collection().delete_one({"id": publicacion_id})
    return res.deleted_count > 0
