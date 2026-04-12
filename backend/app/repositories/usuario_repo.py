_db_usuarios: list[dict] = [{"id": 1, "nombre": "marcos", "email": "marcos@utn"}]
_db_faltantes: list[dict] = []

'''
Repositorio para manejar datos de usuarios. Se usan listas en memoria para simular
una base de datos, pero luego se implementará MongoDB.
Implementación de CRUD para usuarios.
'''

def get_by_id(usuario_id: int) -> dict | None:
    return next((u for u in _db_usuarios if u["id"] == usuario_id), None)


def get_faltantes(usuario_id: int) -> list[dict]:
    return [f for f in _db_faltantes if f["usuario_id"] == usuario_id]


def create_faltante(faltante_data: dict) -> dict:
    faltante_data["id"] = len(_db_faltantes) + 1
    _db_faltantes.append(faltante_data)
    return faltante_data
