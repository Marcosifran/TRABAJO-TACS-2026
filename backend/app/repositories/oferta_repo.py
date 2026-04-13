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