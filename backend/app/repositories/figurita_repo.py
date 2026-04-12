from app.schemas.figurita import FiguritaCreate

_db: list[dict] = []

'''
Repositorio para manejar datos de figuritas. Se usan listas en memoria para simular
una base de datos, pero luego se implementará MongoDB.
Implementación de CRUD para figuritas.
'''

def get_all() -> list[dict]:
    return _db

def buscar(numero: int | None, equipo: str | None, jugador: str | None, skip: int = 0, limit: int = 100) -> list[dict]:
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
    return resultado[skip : skip + limit]


def get_sugerencias(faltantes: list[dict], usuario_id: int) -> list[dict]:
    """
    Busca figuritas publicadas por otros usuarios que coincidan con los datos faltantes del usuario
    (evaluando número, y opcionalmente equipo y jugador).
    """
    sugerencias = []
    for f_db in _db:
        if f_db["usuario_id"] == usuario_id:
            continue
            
        for faltante in faltantes:
            if f_db["numero"] == faltante["numero_figurita"]:
                equipo_match = True
                if faltante.get("equipo"):
                    equipo_match = faltante["equipo"].lower() in f_db["equipo"].lower()
                
                jugador_match = True
                if faltante.get("jugador"):
                    jugador_match = faltante["jugador"].lower() in f_db["jugador"].lower()
                
                if equipo_match and jugador_match:
                    sugerencias.append(f_db)
                    break 
    return sugerencias


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
