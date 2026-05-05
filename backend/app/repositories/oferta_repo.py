_db_ofertas: list[dict] = []

def crear_oferta(subasta_id: int, ofrecidas:list[int], usuario_id: int) -> dict:
    nueva_oferta = {
        "id": len(_db_ofertas) + 1,
        "subasta_id": subasta_id,   #figurita que se subasta
        "ofrecidas": ofrecidas, #figurita que se ofrece
        "usuario_id": usuario_id    #usuario que ofrece
    }

    _db_ofertas.append(nueva_oferta)
    return nueva_oferta

def get_all() -> list[dict]:
    return _db_ofertas

def get_by_subasta(subasta_id: int) -> list[dict]:
    return [o for o in _db_ofertas if o["subasta_id"] == subasta_id]

def get_by_usuario(usuario_id: int) -> list[dict]:
    return [o for o in _db_ofertas if o["usuario_id"] == usuario_id]

def get_by_id(oferta_id: int) -> dict | None:
    return next((o for o in _db_ofertas if o["id"] == oferta_id), None)

def delete(oferta_id: int) -> bool:
    for i, o in enumerate(_db_ofertas):
        if o["id"] == oferta_id:
            _db_ofertas.pop(i)
            return True
    return False