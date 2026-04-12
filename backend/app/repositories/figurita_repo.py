from app.schemas.figurita import FiguritaCreate

_db: list[dict] = []

'''
Repositorio para manejar datos de figuritas. Se usan listas en memoria para simular
una base de datos, pero luego se implementará MongoDB.
Implementación de CRUD para figuritas.
'''

def get_all() -> list[dict]:
    return _db

def create(figurita: FiguritaCreate, usuario_id: int) -> dict:
    nueva = figurita.model_dump()
    nueva["id"] = len(_db) + 1
    # Guardamos quién publicó la figurita para poder filtrar y validar después
    nueva["usuario_id"] = usuario_id
    _db.append(nueva)
    return nueva


def delete(figurita_id: int) -> bool:
    for index, figu in enumerate(_db):
        if figu["id"] == figurita_id:
            _db.pop(index)
            return True
    return False
