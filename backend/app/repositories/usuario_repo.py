from app.core.config import settings
from app.core.database import get_db

def _get_usuarios_collection():
    return get_db()["usuarios"]

def _get_faltantes_collection():
    return get_db()["faltantes"]

_db_usuarios: list[dict] = [
    {"id": 1, "nombre": "marcos", "email": "marcos@utn", "token": settings.user_1_token},
    {"id": 2, "nombre": "jeronimo", "email": "jeronimo@utn", "token": settings.user_2_token},
]

def get_all() -> list[dict]:
    db_users = list(_get_usuarios_collection().find({}, {"_id": 0}))
    return _db_usuarios + db_users

def get_by_id(usuario_id: int) -> dict | None:
    user = next((u for u in _db_usuarios if u["id"] == usuario_id), None)
    if user: return user
    return _get_usuarios_collection().find_one({"id": usuario_id}, {"_id": 0})

def get_by_token(token: str) -> dict | None:
    user = next((u for u in _db_usuarios if u["token"] == token), None)
    if user: return user
    return _get_usuarios_collection().find_one({"token": token}, {"_id": 0})

def get_faltantes(usuario_id: int) -> list[dict]:
    return list(_get_faltantes_collection().find({"usuario_id": usuario_id}, {"_id": 0}))

def create_faltante(faltante_data: dict) -> dict:
    total_faltantes = _get_faltantes_collection().count_documents({})
    faltante_data["id"] = total_faltantes + 1
    
    _get_faltantes_collection().insert_one(faltante_data)
    
    if "_id" in faltante_data:
        del faltante_data["_id"]
        
    return faltante_data

def remove_faltante(usuario_id: int, numero_figurita: int) -> bool:
    resultado = _get_faltantes_collection().delete_one({
        "usuario_id": usuario_id, 
        "numero_figurita": numero_figurita
    })
    return resultado.deleted_count > 0
