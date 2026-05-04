import datetime as dt

_db_subastas: list[dict] = []

def create(figurita_id: int, usuario_id: int, inicio:dt.datetime, fin:dt.datetime) -> dict:
    estado = "activa" if inicio <= dt.datetime.now(dt.timezone.utc) <= fin else "inactiva"
    nueva_subasta = {
        "id": len(_db_subastas) + 1,
        "figurita_id": figurita_id,
        "usuario_id": usuario_id,
        "inicio": inicio,
        "fin": fin, 
        "estado": estado #pasaria a ser un campo calculado
    }
    _db_subastas.append(nueva_subasta)
    return nueva_subasta

def get_all() -> list[dict]:
    return [s for s in _db_subastas if s["estado"] == "activa"]

def get_by_id(subasta_id: int) -> dict | None:
    return next((s for s in _db_subastas if s["id"] == subasta_id), None)

def get_by_figurita(figurita_id: int) -> dict | None:
    return next((s for s in _db_subastas if s["figurita_id"] == figurita_id and s["estado"] == "activa"), None)

def get_by_usuario(usuario_id: int) -> list[dict]:
    return [u for u in _db_subastas if u["usuario_id"] == usuario_id and u["estado"] == "activa"]

def update(subasta_actualizada: dict) -> dict:
    global _db_subastas

    for i, sub in enumerate(_db_subastas):
        if sub["id"] == subasta_actualizada["id"]:
            _db_subastas[i] = subasta_actualizada
            return _db_subastas[i]

    raise ValueError(f"No se encontro la subasta de id {subasta_actualizada['id']}")