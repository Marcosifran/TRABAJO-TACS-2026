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

    #verificamos que no esté subasta para no replicarla
    subasta_activa = subasta_repo.get_by_figurita(subasta_data.figurita_id)
    if subasta_activa:
        raise ValueError("Esta figurita ya se encuentra en subasta")
        
    return subasta_repo.create(subasta_data.figurita_id, usuario_id)

def listar_subastas() -> list[dict]:
    return subasta_repo.get_all()

def ofertar(subasta_id: int, oferta_data: OfertaCreate, usuario_id: int) -> dict:
    subasta = subasta_repo.get_by_id(subasta_id)
    if not subasta:
        raise ValueError("Subasta inexistente")
        
    if subasta["estado"] != "activa":
        raise ValueError("La subasta no está activa")
        
    if subasta["usuario_id"] == usuario_id:
        raise ValueError("No podés ofertar en tu propia subasta")
        
    todas = figurita_repo.get_all()
    ofrecida = next((f for f in todas if f["id"] == oferta_data.figurita_ofrecida_id), None)
    
    if not ofrecida:
        raise ValueError("La figurita que estás ofreciendo no existe")
        
    if ofrecida["usuario_id"] != usuario_id:
        raise ValueError("No podés ofrecer una figurita que no es tuya")
        
    subastada = next((f for f in todas if f["id"] == subasta["figurita_id"]), None)
    
    nueva_oferta = oferta_repo.crear_oferta(subasta_id, ofrecida["id"], usuario_id)
    
    return {
        "mensaje": "Oferta realizada",
        "detalle": f"Ofreciste a {ofrecida['jugador']} por {subastada['jugador'] if subastada else 'la figurita subastada'}"
    }
