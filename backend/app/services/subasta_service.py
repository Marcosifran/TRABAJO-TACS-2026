from app.repositories import subasta_repo, figurita_repo, oferta_repo
from app.schemas.subasta import SubastaCreate
from app.schemas.oferta import OfertaCreate

def crear_subasta(subasta_data: SubastaCreate, usuario_id: int) -> dict:
    """
    Crea una nueva subasta para una figurita del usuario.

    Valida que:
    - La figurita exista en el sistema.
    - El usuario sea el dueño de la figurita.
    - La figurita esté configurada con tipo_intercambio == 'subasta'.
    - La figurita no tenga ya una subasta activa.

    Args:
        subasta_data: Datos de la subasta a crear (figurita_id, inicio, fin).
        usuario_id: ID del usuario que quiere crear la subasta.

    Returns:
        Diccionario con los datos de la subasta creada.

    Raises:
        ValueError: Si alguna validación falla.
    """
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
    """
    Retorna todas las subastas registradas en el sistema.
    """
    return subasta_repo.get_all()

def listar_ofertas(subasta_id: int) -> list[dict]:
    """
    Retorna todas las ofertas realizadas para una subasta específica.

    Args:
        subasta_id: ID de la subasta a consultar.

    Returns:
        Lista de ofertas asociadas a la subasta.

    Raises:
        ValueError: Si la subasta no existe.
    """
    subasta = subasta_repo.get_by_id(subasta_id)
    if not subasta:
        raise ValueError("Subasta inexistente")
    return oferta_repo.get_by_subasta(subasta_id)

def ofertar(subasta_id: int, oferta_data: OfertaCreate, usuario_id: int) -> dict:
    """
    Registra una oferta de un usuario en una subasta activa.

    Valida que:
    - La subasta exista y esté en estado 'activa'.
    - El usuario no sea el dueño de la subasta.
    - Se ofrezca al menos una figurita.
    - Todas las figuritas ofrecidas existan en el sistema.
    - Todas las figuritas ofrecidas pertenezcan al usuario que oferta.

    Args:
        subasta_id: ID de la subasta sobre la que se quiere ofertar.
        oferta_data: Datos de la oferta (lista de IDs de figuritas ofrecidas).
        usuario_id: ID del usuario que realiza la oferta.

    Returns:
        Diccionario con la oferta creada, un mensaje y el detalle de la operación.

    Raises:
        ValueError: Si alguna validación falla.
    """
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

def listar_subastas_usuario(usuario_id: int) -> list[dict]:
    """
    Retorna todas las subastas activas creadas por un usuario específico
    """
    return subasta_repo.get_by_usuario(usuario_id)
