from app.repositories import subasta_repo, figurita_repo, oferta_repo
from app.schemas.subasta import SubastaCreate
from app.schemas.oferta import OfertaCreate
import datetime as dt


def crear_subasta(subasta_data: SubastaCreate, usuario_id: int, inicio:dt.datetime, fin:dt.datetime) -> dict:
    #se verifica que la figurita exista
    figuritas = figurita_repo.get_all()
    figurita = next((f for f in figuritas if f["id"] == subasta_data.figurita_id), None)
    
    if not figurita:
        raise ValueError("Figurita inexistente")

        
    if figurita["usuario_id"] != usuario_id:
        raise ValueError("No podés subastar una figurita que no es tuya")

    #verificamos que no esté subasta para no replicarla
    subasta_activa = subasta_repo.get_by_figurita(subasta_data.figurita_id) #si las figuiritas dejan de conocer a su dueño esto deberia cambiar
    if subasta_activa:
        raise ValueError("Esta figurita ya se encuentra en subasta")
        
    return subasta_repo.create(subasta_data.figurita_id, usuario_id,inicio,fin)

def listar_subastas() -> list[dict]:
    return subasta_repo.get_all()

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

    for f in todas:
        if f["id"] in oferta_data.figuritas_ofrecidas: ofrecidas.append(f)
    
    diff = list(set(f["id"] for f in ofrecidas) - set(oferta_data.figuritas_ofrecidas))
    if diff:
        raise ValueError(f"Las figuritas {[f["id"] for f in diff]} que estás ofreciendo no existen")
        
    if all(usuario_id == u for u in [f["usuario_id"] for f in ofrecidas]):
        raise ValueError("No podés ofrecer una figurita que no es tuya")
        
    subastada = next((f for f in todas if f["id"] == subasta["figurita_id"]), None)
    
    nueva_oferta = oferta_repo.crear_oferta(subasta_id, [f["id"] for f in ofrecidas], usuario_id)
    
    return {
        "oferta": nueva_oferta,
        "mensaje": "Oferta realizada",
        "detalle": f"Ofreciste a {[f['jugador'] for f in ofrecidas]} por {subastada['jugador'] if subastada else 'la figurita subastada'}"
    }
