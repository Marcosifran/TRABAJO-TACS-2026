_db_subastas: list[dict] = []

def create(figurita_id: int, usuario_id: int) -> dict:
    nueva_subasta = {
        "id": len(_db_subastas) + 1,
        "figurita_id": figurita_id,
        "usuario_id": usuario_id,
        "estado": "activa"
    }
    _db_subastas.append(nueva_subasta)
    return nueva_subasta

def get_all() -> list[dict]:
    return [s for s in _db_subastas if s["estado"] == "activa"]

def get_by_id(subasta_id: int) -> dict | None:
    return next((s for s in _db_subastas if s["id"] == subasta_id), None)

def get_by_figurita(figurita_id: int) -> dict | None:
    return next((s for s in _db_subastas if s["figurita_id"] == figurita_id and s["estado"] == "activa"), None)
