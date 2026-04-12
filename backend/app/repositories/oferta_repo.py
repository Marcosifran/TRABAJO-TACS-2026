_db_ofertas: list[dict] = []

def crear_oferta(subasta_id: int, ofrecida_id:int, usuario_id: int) -> dict:
    nueva_oferta = {
        "id": len(_db_ofertas) + 1,
        "subasta_id": subasta_id,   #figurita que se subasta
        "ofrecida_id": ofrecida_id, #figurita que se ofrece
        "usuario_id": usuario_id    #usuario que ofrece
    }

    _db_ofertas.append(nueva_oferta)
    return nueva_oferta

def get_all() -> list[dict]:
    return _db_ofertas

def count_by_ofrecida(ofrecida_id: int) -> int:
    return sum(1 for o in _db_ofertas if o["ofrecida_id"] == ofrecida_id)

def delete_by_figurita(figurita_id: int):
    global _db_ofertas
    _db_ofertas = [o for o in _db_ofertas if o["subasta_id"] != figurita_id and o["ofrecida_id"] != figurita_id]