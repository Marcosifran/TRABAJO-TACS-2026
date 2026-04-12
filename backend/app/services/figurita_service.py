from app.schemas.figurita import FiguritaCreate
from app.repositories import figurita_repo, usuario_repo


def listar() -> list[dict]:
    return figurita_repo.get_all()


def buscar(numero: int | None, equipo: str | None, jugador: str | None) -> list[dict]:
    # Busca figuritas disponibles aplicando filtros opcionales.

    return figurita_repo.buscar(numero, equipo, jugador)


def sugerir_intercambios(usuario_id: int) -> list[dict]:
    """
    Genera sugerencias automáticas de intercambio para el usuario.
    Cruza los faltantes del usuario con las figuritas publicadas por otros usuarios.
    """
    faltantes = usuario_repo.get_faltantes(usuario_id)
    numeros_faltantes = [f["numero_figurita"] for f in faltantes]

    if not numeros_faltantes:
        return []

    figuritas_candidatas = figurita_repo.get_sugerencias(numeros_faltantes, usuario_id)

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
    return figurita_repo.delete(figurita_id)
