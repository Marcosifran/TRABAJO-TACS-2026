import datetime as dt

_db: list[dict] = []
_next_id: int = 1

def crear_mensaje(intercambio_id: int, remitente_id: int, contenido: str) -> dict:
    global _next_id
    nuevo = {
        "id": _next_id,
        "intercambio_id": intercambio_id,
        "remitente_id": remitente_id,
        "contenido": contenido,
        "fecha_envio": dt.datetime.now()
    }
    _db.append(nuevo)
    _next_id += 1
    return nuevo

def listar_mensajes_por_intercambio(intercambio_id: int) -> list[dict]:
    return [msg for msg in _db if msg["intercambio_id"] == intercambio_id]

