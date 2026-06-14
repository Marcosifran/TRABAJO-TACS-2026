from app.repositories import intercambio_repo, mensaje_repo
from app.domain.errors import DomainNotFoundError, DomainPermissionError
from app.schemas.mensaje_sch import MensajeCreate, MensajeResponse

def enviar_mensaje(intercambio_id: int, remitente_id:int, contenido: str) -> dict:
    intercambio = intercambio_repo.buscar_intercambio_por_id(intercambio_id)
    if not intercambio:
        raise DomainNotFoundError("Intercambio no encontrado")
    
    if remitente_id not in (intercambio["propuesto_por"],
        intercambio["solicitado_a"]):
        raise DomainPermissionError("No tenés permiso para chatear en este intercambio")
    return mensaje_repo.crear_mensaje(
        intercambio_id = intercambio_id,
        remitente_id = remitente_id,
        contenido = contenido
    )

def obtener_mensaje(intercambio_id: int, usuario_id: int) -> list[dict]:
    intercambio = intercambio_repo.buscar_intercambio_por_id(intercambio_id)
    if not intercambio:
        raise DomainNotFoundError("Intercambio no encontrado")
    
    if usuario_id not in (intercambio["propuesto_por"],
                          intercambio["solicitado_a"]):
        raise DomainPermissionError("No tenés permiso para ver este chat")
    return mensaje_repo.listar_mensajes_por_intercambio(intercambio_id)

