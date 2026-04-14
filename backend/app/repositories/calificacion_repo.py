_db: list[dict] = []

'''
Repositorio de calificaciones entre usuarios tras intercambios concretados.
Persistencia en memoria; mismo patrón que intercambio_repo.
'''


def crear(
    intercambio_id: int,
    calificador_id: int,
    calificado_id: int,
    puntuacion: int,
    comentario: str | None,
) -> dict:
    nuevo = {
        "id": len(_db) + 1,
        "intercambio_id": intercambio_id,
        "calificador_id": calificador_id,
        "calificado_id": calificado_id,
        "puntuacion": puntuacion,
        "comentario": comentario,
    }
    _db.append(nuevo)
    return nuevo


def buscar_por_intercambio_y_calificador(intercambio_id: int, calificador_id: int) -> dict | None:
    for c in _db:
        if c["intercambio_id"] == intercambio_id and c["calificador_id"] == calificador_id:
            return c
    return None


def listar_por_calificado(calificado_id: int) -> list[dict]:
    return [c for c in _db if c["calificado_id"] == calificado_id]
