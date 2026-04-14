from app.schemas.figurita import FiguritaCreate
from app.repositories import figurita_repo, usuario_repo


def listar() -> list[dict]:
    """
    Retorna todas las figuritas publicadas en el sistema.
    """
    return figurita_repo.get_all()


def buscar(numero: int | None, equipo: str | None, jugador: str | None) -> list[dict]:
    """
    Busca figuritas disponibles aplicando filtros opcionales.
    Los parámetros que se dejen en None no se utilizan como criterio de filtrado.

    Args:
        numero: Número exacto de la figurita.
        equipo: Nombre del equipo (búsqueda parcial, case-insensitive).
        jugador: Nombre del jugador (búsqueda parcial, case-insensitive).

    Returns:
        Lista de figuritas que coinciden con los filtros aplicados.
    """
    return figurita_repo.buscar(numero, equipo, jugador)

def buscar_por_usuario(usuario_id: int) -> list[dict]:
    """
    Retorna las figuritas publicadas por un usuario específico.

    Args:
        usuario_id: ID del usuario dueño de las figuritas.
    """
    return figurita_repo.get_by_usuario_id(usuario_id)

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
    """
    Publica una figurita para intercambio, asociándola al usuario que la registra.

    Args:
        figurita: Datos de la figurita a publicar.
        usuario_id: ID del usuario que publica la figurita.

    Returns:
        Diccionario con los datos de la figurita creada, incluyendo su ID asignado.
    """
    return figurita_repo.create(figurita, usuario_id)


def eliminar(figurita_id: int, usuario_id: int) -> bool | None:
    """
    Elimina una figurita del sistema por su ID, solo si pertenece al usuario.

    Args:
        figurita_id: ID de la figurita a eliminar.
        usuario_id: ID del usuario que intenta eliminar.

    Returns:
        True si fue eliminada, False si no existía, None si no le pertenece.
    """
    figurita = figurita_repo.get_by_id(figurita_id)
    if figurita is None:
        return False
    if figurita["usuario_id"] != usuario_id:
        return None
    figurita_repo.delete(figurita_id)
    return True
