from app.repositories import calificacion_repo, intercambio_repo, usuario_repo
from app.schemas import CalificacionCreate, ReputacionResponse, EstadoIntercambio
from app.domain.errors import (
    DomainNotFoundError,
    DomainValidationError,
    DomainPermissionError,
    DomainConflictError,
)


def crear_calificacion(intercambio_id: str, calificador_id: int, data: CalificacionCreate) -> dict:
    intercambio = intercambio_repo.find_exchange_by_id(intercambio_id)
    if not intercambio:
        raise DomainNotFoundError("Intercambio no encontrado")

    if intercambio.estado != EstadoIntercambio.ACEPTADO:
        raise DomainValidationError("Solo podés calificar después de un intercambio aceptado")

    if calificador_id not in (intercambio.propuesto_por, intercambio.solicitado_a):
        raise DomainPermissionError("No participás en este intercambio")

    if calificacion_repo.find_by_exchange_and_qualifier(intercambio_id, calificador_id):
        raise DomainConflictError("Ya calificaste este intercambio")

    calificado_id = (
        intercambio.solicitado_a
        if calificador_id == intercambio.propuesto_por
        else intercambio.propuesto_por
    )

    return calificacion_repo.create(
        intercambio_id=intercambio_id,
        calificador_id=calificador_id,
        calificado_id=calificado_id,
        puntuacion=data.puntuacion,
        comentario=data.comentario,
    )


def obtener_reputacion(usuario_id: int) -> ReputacionResponse:
    if not usuario_repo.get_by_id(usuario_id):
        raise DomainNotFoundError("Usuario no encontrado")

    recibidas = calificacion_repo.list_by_qualified(usuario_id)
    n = len(recibidas)
    if n == 0:
        return ReputacionResponse(
            usuario_id=usuario_id,
            cantidad_calificaciones=0,
            promedio_puntuacion=None,
        )

    total = sum(c["puntuacion"] for c in recibidas)
    promedio = round(total / n, 2)
    return ReputacionResponse(
        usuario_id=usuario_id,
        cantidad_calificaciones=n,
        promedio_puntuacion=promedio,
    )
