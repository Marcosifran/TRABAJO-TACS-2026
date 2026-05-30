from app.repositories import album_repo, publicacion_repo, usuario_repo, faltante_repo
from app.schemas.publicacion_sch import PublicacionCreate
from app.domain.errors import (
    DomainNotFoundError,
    DomainPermissionError,
    DomainConflictError,
    DomainValidationError,
)


def publicar_figurita(publicacion: PublicacionCreate, usuario_id: int) -> dict:
    figurita = album_repo.get_by_id(publicacion.figurita_personal_id)

    if not figurita:
        raise DomainNotFoundError("Figurita no encontrada en el álbum del usuario")
    if figurita["usuario_id"] != usuario_id:
        raise DomainPermissionError("La figurita no pertenece al usuario")
    if publicacion_repo.get_by_personal_figurita(publicacion.figurita_personal_id):
        raise DomainConflictError("La figurita ya está publicada para intercambio")
    if publicacion.cantidad_disponible > figurita["cantidad"]:
        raise DomainValidationError("La cantidad disponible no puede ser mayor a la cantidad en el álbum")

    return publicacion_repo.create(
        publicacion=publicacion,
        usuario_id=usuario_id,
        numero=figurita["numero"],
        equipo=figurita["equipo"],
        jugador=figurita["jugador"],
    )


def listar_publicaciones(
    numero: int | None,
    equipo: str | None,
    jugador: str | None,
    tipo_intercambio: str | None,
    excluir_usuario_id: int | None
) -> list[dict]:
    return publicacion_repo.find(
        numero=numero,
        equipo=equipo,
        jugador=jugador,
        tipo_intercambio=tipo_intercambio,
        usuario_id=excluir_usuario_id,
    )


def retirar_publicacion(publicacion_id: str, usuario_id: int) -> None:
    publicacion = publicacion_repo.get_by_id(publicacion_id)
    if publicacion is None:
        raise DomainNotFoundError("Publicación no encontrada")
    if publicacion["usuario_id"] != usuario_id:
        raise DomainPermissionError("No tiene permiso para retirar esta publicación")
    publicacion_repo.delete(publicacion_id)


def obtener_sugerencias(usuario_id: int) -> list[dict]:
    faltantes = faltante_repo.get_missing(usuario_id)

    if not faltantes:
        return []

    numeros_faltantes = {f["numero_figurita"] for f in faltantes}

    publicaciones = publicacion_repo.find(
        numero=None,
        equipo=None,
        jugador=None,
        usuario_id=usuario_id,
    )

    sugerencias = []
    for pub in publicaciones:
        if pub["numero"] in numeros_faltantes:
            oferente = usuario_repo.get_by_id(pub["usuario_id"])
            sugerencias.append({
                "publicacion": pub,
                "ofrecida_por": oferente["nombre"] if oferente else "Usuario desconocido",
                "cubre_tu_faltante": pub["numero"],
            })

    return sugerencias


def mis_publicaciones(usuario_id: int) -> list[dict]:
    return publicacion_repo.get_by_user(usuario_id)
