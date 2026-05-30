from app.schemas.figurita import FiguritaCreate
from app.repositories import figurita_repo, usuario_repo, faltante_repo
from app.domain.errors import DomainNotFoundError, DomainPermissionError


def listar() -> list[dict]:
    return figurita_repo.get_all()


def buscar(numero: int | None, equipo: str | None, jugador: str | None) -> list[dict]:
    return figurita_repo.find(numero, equipo, jugador)


def buscar_por_usuario(usuario_id: int) -> list[dict]:
    return figurita_repo.get_by_user_id(usuario_id)


def sugerir_intercambios(usuario_id: int) -> list[dict]:
    faltantes = faltante_repo.get_missing(usuario_id)
    numeros_faltantes = [f["numero_figurita"] for f in faltantes]

    if not numeros_faltantes:
        return []

    figuritas_candidatas = figurita_repo.get_suggestions(numeros_faltantes, usuario_id)

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


def eliminar(figurita_id: str, usuario_id: int) -> None:
    figurita = figurita_repo.get_by_id(figurita_id)
    if figurita is None:
        raise DomainNotFoundError("Figurita no encontrada")
    if figurita["usuario_id"] != usuario_id:
        raise DomainPermissionError("No tenés permiso para eliminar esta figurita")
    figurita_repo.delete(figurita_id)
