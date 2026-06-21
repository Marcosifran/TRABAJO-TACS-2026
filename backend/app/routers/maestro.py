from fastapi import APIRouter, HTTPException, Query
from app.schemas import JugadorMaestroResponse
from app.services import maestro_service

router = APIRouter(prefix="/maestro", tags=["Maestro de Figuritas"])


@router.get(
    "/equipos",
    summary="Listar equipos disponibles",
    description="Devuelve la lista de todos los equipos (selecciones) presentes en el maestro.",
    responses={
        200: {"description": "Lista de equipos ordenada alfabéticamente"},
    },
)
def listar_equipos():
    return {"equipos": maestro_service.get_equipos()}


@router.get(
    "/{numero}",
    status_code=200,
    response_model=JugadorMaestroResponse,
    summary="Obtener jugador por número de figurita",
    description=(
        "Dado el número único de figurita, devuelve los datos del jugador correspondiente "
        "(equipo, nombre, posición y número de camiseta oficial). "
        "Usar para autocompletar el formulario de alta de figurita."
    ),
    responses={
        200: {"description": "Datos del jugador encontrado"},
        404: {"description": "No existe una figurita con ese número en el maestro"},
    },
)
def obtener_jugador(numero: int):
    jugador = maestro_service.get_jugador(numero)
    if not jugador:
        raise HTTPException(status_code=404, detail=f"No existe la figurita número {numero} en el maestro")
    return jugador


@router.get(
    "/",
    status_code=200,
    summary="Listar jugadores del maestro",
    description=(
        "Devuelve todos los jugadores del maestro. "
        "Si se pasa `jugador`, busca por nombre (coincidencia parcial, case-insensitive) "
        "para autocompletar, acotando por `equipo` si también se envía. "
        "Si solo se pasa `equipo`, filtra los jugadores de ese equipo."
    ),
    responses={
        200: {"description": "Lista de jugadores"},
    },
)
def listar_jugadores(
    equipo: str | None = Query(
        None,
        description="Nombre del equipo para filtrar (case-insensitive). Si se omite, devuelve todos.",
    ),
    jugador: str | None = Query(
        None,
        min_length=1,
        description="Nombre del jugador para autocompletar (coincidencia parcial, case-insensitive).",
    ),
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Cantidad máxima de sugerencias al buscar por nombre.",
    ),
):
    if jugador:
        return maestro_service.buscar_por_nombre(jugador, equipo, limit)
    if equipo:
        return maestro_service.get_por_equipo(equipo)
    return maestro_service.get_todos()


@router.post(
    "/refresh",
    status_code=200,
    summary="Re-scrapear y recargar el maestro desde Wikipedia",
    description=(
        "Descarga el plantel actualizado del Mundial 2026 desde Wikipedia, vacía la colección "
        "`maestro_figuritas` y la repopula con los datos frescos. "
        "**ADVERTENCIA:** si ya existen figuritas en los álbumes de usuarios, sus números "
        "pueden quedar desincronizados. Usar únicamente antes del primer uso en producción "
        "o para corregir datos erróneos en un entorno sin figuritas cargadas."
    ),
    responses={
        200: {"description": "Maestro recargado exitosamente"},
        503: {"description": "No se pudo contactar a Wikipedia"},
    },
)
def refresh_maestro():
    try:
        total = maestro_service.refresh()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Error al scrapear Wikipedia: {exc}")
    return {"mensaje": "Maestro recargado exitosamente", "total_jugadores": total}
