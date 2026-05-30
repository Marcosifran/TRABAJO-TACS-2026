from app.schemas.faltante import FaltanteCreate
from app.repositories import usuario_repo, faltante_repo
from app.domain.errors import DomainNotFoundError, DomainConflictError


def registrar_faltante(usuario_id: int, faltante: FaltanteCreate) -> dict:
    if not usuario_repo.get_by_id(usuario_id):
        raise DomainNotFoundError("Usuario no encontrado")
    existentes = faltante_repo.get_missing(usuario_id)
    if any(f["numero_figurita"] == faltante.numero_figurita for f in existentes):
        raise DomainConflictError(f"La figurita {faltante.numero_figurita} ya está registrada como faltante")
    faltante_data = faltante.model_dump()
    faltante_data["usuario_id"] = usuario_id
    return faltante_repo.create_missing(faltante_data)


def listar_faltantes(usuario_id: int) -> list[dict]:
    if not usuario_repo.get_by_id(usuario_id):
        raise DomainNotFoundError("Usuario no encontrado")
    return faltante_repo.get_missing(usuario_id)
