from app.schemas.figurita import FiguritaCreate
from app.repositories import figurita_repo, usuario_repo, oferta_repo


def listar() -> list[dict]:
    return figurita_repo.get_all()


def buscar(numero: int | None, equipo: str | None, jugador: str | None, skip: int = 0, limit: int = 100) -> list[dict]:
    # Busca figuritas disponibles aplicando filtros opcionales.

    return figurita_repo.buscar(numero, equipo, jugador, skip, limit)


def sugerir_intercambios(usuario_id: int) -> list[dict]:
    """
    Genera sugerencias automáticas de intercambio para el usuario.
    Cruza los faltantes del usuario con las figuritas publicadas por otros usuarios.
    """
    faltantes = usuario_repo.get_faltantes(usuario_id)

    if not faltantes:
        return []

    figuritas_candidatas = figurita_repo.get_sugerencias(faltantes, usuario_id)

    sugerencias = []
    for figurita in figuritas_candidatas:
        oferente = usuario_repo.get_by_id(figurita["usuario_id"])
        sugerencias.append({
            "figurita": figurita,
            "ofrecida_por": oferente["nombre"] if oferente else "Usuario desconocido",
            "cubre_tu_faltante": figurita["numero"],
        })
    return sugerencias


def publicar(figurita: FiguritaCreate, usuario_id: int) -> dict:
    return figurita_repo.create(figurita, usuario_id)


def eliminar(figurita_id: int) -> bool:
    oferta_repo.delete_by_figurita(figurita_id)
    return figurita_repo.delete(figurita_id)
