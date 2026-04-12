from app.core.config import settings

# Los tokens vienen del entorno (.env), no se generan en código ni se exponen por API
_db_usuarios: list[dict] = [
    {"id": 1, "nombre": "marcos", "email": "marcos@utn", "token": settings.user_1_token},
    {"id": 2, "nombre": "jeronimo", "email": "jeronimo@utn", "token": settings.user_2_token},
]
_db_faltantes: list[dict] = []

'''
Repositorio para manejar datos de usuarios. Se usan listas en memoria para simular
una base de datos, pero luego se implementará MongoDB.
Implementación de CRUD para usuarios.
'''

def get_all() -> list[dict]:
    return _db_usuarios

def get_by_id(usuario_id: int) -> dict | None:
    return next((u for u in _db_usuarios if u["id"] == usuario_id), None)

# Buscamos el usuario por token para identificarlo en cada request
def get_by_token(token: str) -> dict | None:
    return next((u for u in _db_usuarios if u["token"] == token), None)


def get_faltantes(usuario_id: int) -> list[dict]:
    return [f for f in _db_faltantes if f["usuario_id"] == usuario_id]


def create_faltante(faltante_data: dict) -> dict:
    faltante_data["id"] = len(_db_faltantes) + 1
    _db_faltantes.append(faltante_data)
    return faltante_data
