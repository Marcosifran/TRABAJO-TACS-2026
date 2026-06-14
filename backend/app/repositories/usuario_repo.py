from bson import ObjectId
from app.core.config import settings
from app.core.security_passwords import hash_password
from app.core.database import get_db


def _get_usuarios_collection():
    return get_db()["usuarios"]


def _get_faltantes_collection():
    return get_db()["faltantes"]


# Hash de la contraseña demo, compartida por los dos usuarios sembrados.
# Se calcula una sola vez al importar el módulo.
_seed_password_hash = hash_password(settings.seed_user_password)

_db_usuarios: list[dict] = [
    {"id": 1, "nombre": "marcos", "email": "marcos@utn", "password_hash": _seed_password_hash, "es_admin": True},
    {"id": 2, "nombre": "jeronimo", "email": "jeronimo@utn", "password_hash": _seed_password_hash, "es_admin": False},
]


def get_all() -> list[dict]:
    db_users = list(_get_usuarios_collection().find({}, {"_id": 0}))
    return _db_usuarios + db_users


def get_by_id(usuario_id: int) -> dict | None:
    user = next((u for u in _db_usuarios if u["id"] == usuario_id), None)
    if user:
        return user
    return _get_usuarios_collection().find_one({"id": usuario_id}, {"_id": 0})


def get_by_email(email: str) -> dict | None:
    """Busca usuario por email entre los sembrados en memoria y los creados en MongoDB."""
    if not email:
        return None

    user = next((u for u in _db_usuarios if u["email"] == email), None)
    if user:
        return user

    return _get_usuarios_collection().find_one({"email": email}, {"_id": 0})


def _next_id() -> int:
    """Calcula el próximo id entero considerando usuarios en memoria y en MongoDB."""
    max_seed = max((u["id"] for u in _db_usuarios), default=0)
    ultimo = _get_usuarios_collection().find_one(sort=[("id", -1)], projection={"_id": 0, "id": 1})
    max_db = ultimo["id"] if ultimo else 0
    return max(max_seed, max_db) + 1


def create_usuario(nombre: str, email: str, password_hash: str, es_admin: bool = False) -> dict:
    """Crea un usuario nuevo en MongoDB y devuelve el documento (sin el _id de Mongo)."""
    usuario = {
        "id": _next_id(),
        "nombre": nombre,
        "email": email,
        "password_hash": password_hash,
        "es_admin": es_admin,
    }
    _get_usuarios_collection().insert_one(usuario)
    usuario.pop("_id", None)
    return usuario


def get_faltantes(usuario_id: int) -> list[dict]:
    return list(_get_faltantes_collection().find({"usuario_id": usuario_id}, {"_id": 0}))


def create_faltante(faltante_data: dict) -> dict:
    oid = ObjectId()
    faltante_data["_id"] = oid
    faltante_data["id"] = str(oid)
    _get_faltantes_collection().insert_one(faltante_data)
    del faltante_data["_id"]
    return faltante_data


def remove_faltante(usuario_id: int, numero_figurita: int) -> bool:
    resultado = _get_faltantes_collection().delete_one({
        "usuario_id": usuario_id,
        "numero_figurita": numero_figurita,
    })
    return resultado.deleted_count > 0
