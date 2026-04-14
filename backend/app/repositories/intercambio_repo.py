# intercambio_repo.py
from app.schemas.intercambio_sch import IntercambioCreate

_db: list[dict] = []

'''
Repositorio para manejar datos de intercambios. Se usan listas en memoria para simular
una base de datos, pero luego se implementará MongoDB.
Implementación de CRUD para intercambios.
'''


def crear_intercambio(intercambio: IntercambioCreate, propuesto_por: int, solicitado_a: int) -> dict:
    nuevo = {
        "id": len(_db) + 1,
        "propuesto_por": propuesto_por,
        "solicitado_a": solicitado_a,
        "figuritas_ofrecidas": intercambio.figuritas_ofrecidas_numero,
        "figurita_solicitada": intercambio.figurita_solicitada_numero,
        "estado": "pendiente",
    }
    _db.append(nuevo)
    return nuevo

def listar_intercambios() -> list[dict]:
    return _db


def buscar_intercambio_por_id(intercambio_id: int) -> dict | None:
    for intercambio in _db:
        if intercambio["id"] == intercambio_id:
            return intercambio
    return None


def responder_intercambio(intercambio_id: int, estado: str) -> dict | None:
    intercambio = buscar_intercambio_por_id(intercambio_id)
    if not intercambio:
        return None
    intercambio["estado"] = estado
    return intercambio

def buscar_intercambios_por_usuario(usuario_id: int) -> list[dict]:
    return [intercambio for intercambio in _db if intercambio["propuesto_por"] == usuario_id]


def buscar_intercambios_enviados(usuario_id: int) -> list[dict]:
    return [intercambio for intercambio in _db if intercambio["propuesto_por"] == usuario_id]


def buscar_intercambios_recibidos(usuario_id: int) -> list[dict]:
    return [intercambio for intercambio in _db if intercambio["solicitado_a"] == usuario_id]

def listar_intercambios_por_usuario(usuario_id: int) -> dict[str, list[dict]]:
    enviados = buscar_intercambios_enviados(usuario_id)
    recibidos = buscar_intercambios_recibidos(usuario_id)
    return {"enviados": enviados, "recibidos": recibidos}
