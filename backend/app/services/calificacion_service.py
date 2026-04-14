from fastapi import HTTPException

from app.repositories import calificacion_repo, intercambio_repo, usuario_repo
from app.schemas.calificacion_sch import CalificacionCreate, ReputacionResponse


def crear_calificacion(intercambio_id: int, calificador_id: int, data: CalificacionCreate) -> dict:
    """
    Registra la calificación que un participante le otorga al otro tras un intercambio aceptado.

    Valida que:
    - El intercambio exista y esté en estado 'aceptado'.
    - El calificador haya participado en el intercambio.
    - El calificador no haya calificado este intercambio previamente.

    El calificado se determina automáticamente: si el calificador fue quien propuso el intercambio,
    se califica al receptor, y viceversa.

    Args:
        intercambio_id: ID del intercambio a calificar.
        calificador_id: ID del usuario que emite la calificación.
        data: Datos de la calificación (puntuacion, comentario opcional).

    Returns:
        Diccionario con los datos de la calificación creada.

    Raises:
        HTTPException 404: Si el intercambio no existe.
        HTTPException 400: Si el intercambio no está aceptado.
        HTTPException 403: Si el calificador no participó en el intercambio.
        HTTPException 409: Si el calificador ya calificó este intercambio.
    """
    intercambio = intercambio_repo.buscar_intercambio_por_id(intercambio_id)
    if not intercambio:
        raise HTTPException(status_code=404, detail="Intercambio no encontrado")

    if intercambio["estado"] != "aceptado":
        raise HTTPException(
            status_code=400,
            detail="Solo podés calificar después de un intercambio aceptado",
        )

    if calificador_id not in (intercambio["propuesto_por"], intercambio["solicitado_a"]):
        raise HTTPException(status_code=403, detail="No participás en este intercambio")

    if calificacion_repo.buscar_por_intercambio_y_calificador(intercambio_id, calificador_id):
        raise HTTPException(status_code=409, detail="Ya calificaste este intercambio")

    calificado_id = (
        intercambio["solicitado_a"]
        if calificador_id == intercambio["propuesto_por"]
        else intercambio["propuesto_por"]
    )

    return calificacion_repo.crear(
        intercambio_id=intercambio_id,
        calificador_id=calificador_id,
        calificado_id=calificado_id,
        puntuacion=data.puntuacion,
        comentario=data.comentario,
    )


def obtener_reputacion(usuario_id: int) -> ReputacionResponse:
    """
    Calcula y retorna la reputación de un usuario basada en las calificaciones recibidas.

    Si el usuario no tiene calificaciones, retorna promedio None y cantidad 0.

    Args:
        usuario_id: ID del usuario cuya reputación se quiere consultar.

    Returns:
        ReputacionResponse con usuario_id, cantidad_calificaciones y promedio_puntuacion.

    Raises:
        HTTPException 404: Si el usuario no existe.
    """
    if not usuario_repo.get_by_id(usuario_id):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    recibidas = calificacion_repo.listar_por_calificado(usuario_id)
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
