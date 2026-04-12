from app.schemas.faltante import FaltanteCreate
from app.repositories import usuario_repo, intercambio_repo


def registrar_faltante(usuario_id: int, faltante: FaltanteCreate) -> dict | None:
    if not usuario_repo.get_by_id(usuario_id):
        return None
    existentes = usuario_repo.get_faltantes(usuario_id)
    if any(f["numero_figurita"] == faltante.numero_figurita for f in existentes):
        raise ValueError(f"La figurita {faltante.numero_figurita} ya está registrada como faltante")
    faltante_data = faltante.model_dump()
    faltante_data["usuario_id"] = usuario_id
    return usuario_repo.create_faltante(faltante_data)

def listar_faltantes(usuario_id: int) -> list[dict] | None:
    if not usuario_repo.get_by_id(usuario_id):
        return None
    return usuario_repo.get_faltantes(usuario_id)

def listar_intercambios(usuario_id: int) -> dict[str, list[dict]] | None:
    if not usuario_repo.get_by_id(usuario_id):
        return None

    enviados = intercambio_repo.buscar_intercambios_enviados(usuario_id)
    recibidos = intercambio_repo.buscar_intercambios_recibidos(usuario_id)

    return {
        "enviados": enviados,
        "recibidos": recibidos,
    }