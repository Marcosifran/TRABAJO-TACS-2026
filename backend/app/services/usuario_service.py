from app.schemas.faltante import FaltanteCreate
from app.repositories import usuario_repo


def registrar_faltante(usuario_id: int, faltante: FaltanteCreate) -> dict | None:
    if not usuario_repo.get_by_id(usuario_id):
        return None
    faltante_data = faltante.model_dump()
    faltante_data["usuario_id"] = usuario_id
    return usuario_repo.create_faltante(faltante_data)


def listar_faltantes(usuario_id: int) -> list[dict] | None:
    if not usuario_repo.get_by_id(usuario_id):
        return None
    return usuario_repo.get_faltantes(usuario_id)
