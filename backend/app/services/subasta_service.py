from app.repositories import subasta_repo, figurita_repo, oferta_repo
from app.schemas.subasta import SubastaCreate
from app.schemas.oferta import OfertaCreate

def crear_subasta(subasta_data: SubastaCreate, usuario_id: int) -> dict:
    #se verifica que la figurita exista
    figuritas = figurita_repo.get_all()
    figurita = next((f for f in figuritas if f["id"] == subasta_data.figurita_id), None)
    
    if not figurita:
        raise ValueError("Figurita inexistente")

        
    if figurita["usuario_id"] != usuario_id:
        raise ValueError("No podés subastar una figurita que no es tuya")

    if figurita.get("tipo_intercambio") != "subasta":
        raise ValueError("Esta figurita no está configurada para subasta")

    #verificamos que no esté subasta para no replicarla
    subasta_activa = subasta_repo.get_by_figurita(subasta_data.figurita_id) #si las figuiritas dejan de conocer a su dueño esto deberia cambiar
    if subasta_activa:
        raise ValueError("Esta figurita ya se encuentra en subasta")
        
    return subasta_repo.create(subasta_data.figurita_id, usuario_id, subasta_data.inicio, subasta_data.fin)

def listar_subastas() -> list[dict]:
    return subasta_repo.get_all()

def listar_ofertas(subasta_id: int) -> list[dict]:
    subasta = subasta_repo.get_by_id(subasta_id)
    if not subasta:
        raise ValueError("Subasta inexistente")
    return oferta_repo.get_by_subasta(subasta_id)

def ofertar(subasta_id: int, oferta_data: OfertaCreate, usuario_id: int) -> dict:
    subasta = subasta_repo.get_by_id(subasta_id)
    ofrecidas = []
    if not subasta:
        raise ValueError("Subasta inexistente")
        
    if subasta["estado"] != "activa":
        raise ValueError("La subasta no está activa")
        
    if subasta["usuario_id"] == usuario_id:
        raise ValueError("No podés ofertar en tu propia subasta")
        
    todas = figurita_repo.get_all()

    if not oferta_data.figuritas_ofrecidas:
        raise ValueError("Debés ofrecer al menos una figurita")

    for f in todas:
        if f["id"] in oferta_data.figuritas_ofrecidas: ofrecidas.append(f)

    ids_no_encontrados = set(oferta_data.figuritas_ofrecidas) - set(f["id"] for f in ofrecidas)
    if ids_no_encontrados:
        raise ValueError(f"Las figuritas {list(ids_no_encontrados)} que estás ofreciendo no existen")
        
    if any(f["usuario_id"] != usuario_id for f in ofrecidas):
        raise ValueError("No podés ofrecer una figurita que no es tuya")
        
    subastada = next((f for f in todas if f["id"] == subasta["figurita_id"]), None)
    
    nueva_oferta = oferta_repo.crear_oferta(subasta_id, [f["id"] for f in ofrecidas], usuario_id)
    
    return {
        "oferta": nueva_oferta,
        "mensaje": "Oferta realizada",
        "detalle": f"Ofreciste a {[f['jugador'] for f in ofrecidas]} por {subastada['jugador'] if subastada else 'la figurita subastada'}"
    }
