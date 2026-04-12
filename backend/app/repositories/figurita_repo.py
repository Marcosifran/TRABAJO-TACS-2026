from app.schemas.figurita import FiguritaCreate

_db: list[dict] = []

'''
Repositorio para manejar datos de figuritas. Se usan listas en memoria para simular
una base de datos, pero luego se implementará MongoDB.
Implementación de CRUD para figuritas.
'''

def get_all() -> list[dict]:
    return _db

def buscar(numero: int | None, equipo: str | None, jugador: str | None) -> list[dict]:
    """
    Filtra las figuritas disponibles según criterios opcionales. Si dejamos alguno vacio, no lo utiliza para filtrar
    """
    resultado = _db
    if numero is not None:
        resultado = [f for f in resultado if f["numero"] == numero]
    if equipo is not None:
        resultado = [f for f in resultado if equipo.lower() in f["equipo"].lower()]
    if jugador is not None:
        resultado = [f for f in resultado if jugador.lower() in f["jugador"].lower()]
    return resultado


def get_sugerencias(numeros_faltantes: list[int], usuario_id: int) -> list[dict]:
    """
    Busca figuritas publicadas por otros usuarios que coincidan con los números faltantes del usuario.
    """
    return [
        f for f in _db
        if f["numero"] in numeros_faltantes and f["usuario_id"] != usuario_id
    ]


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
