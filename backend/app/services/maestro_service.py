"""
Servicio del Maestro de Figuritas.

El maestro es un catálogo de referencia (equipo + jugador por número de figurita)
generado a partir de scraping de Wikipedia. Los números son asignados una sola vez;
un refresh posterior requiere vaciar la colección primero para evitar re-numeración
accidental mientras haya figuritas en el sistema.
"""

from app.repositories import maestro_repo
from app.scraping.wikipedia_scraper import scrape_planteles

# Flag de proceso: garantiza que el scraping inicial ocurra solo una vez,
# aunque el lifespan de FastAPI se ejecute varias veces (ej: en tests).
_inicializado = False


def inicializar() -> None:
    """
    Popula el maestro en el arranque de la aplicación si está vacío.
    Llama a scrape_planteles() una sola vez por proceso.
    Falla silenciosamente para no bloquear el startup si Wikipedia no está disponible.
    """
    global _inicializado
    if _inicializado:
        return
    _inicializado = True
    if maestro_repo.count() > 0:
        return
    try:
        jugadores = scrape_planteles()
        maestro_repo.bulk_insert(jugadores)
        print(f"[maestro] Inicializado con {len(jugadores)} jugadores.")
    except Exception as exc:
        print(f"[maestro] No se pudo inicializar automáticamente: {exc}")


def get_jugador(numero: int) -> dict | None:
    return maestro_repo.get_by_number(numero)


def get_equipos() -> list[str]:
    return maestro_repo.get_teams()


def get_por_equipo(equipo: str) -> list[dict]:
    return maestro_repo.get_by_team(equipo)


def buscar_por_nombre(nombre: str, equipo: str | None = None, limit: int = 10) -> list[dict]:
    return maestro_repo.search_by_name(nombre, equipo, limit)


def get_todos() -> list[dict]:
    return maestro_repo.get_all()


def refresh() -> int:
    """
    Vuelve a scrapear Wikipedia y reemplaza el maestro completo.
    ADVERTENCIA: si ya existen figuritas en el álbum de usuarios con números
    del maestro anterior, esos números quedarán desincronizados.
    Usar solo antes de que haya datos en producción o cuando se desee resetear.
    """
    global _inicializado
    jugadores = scrape_planteles()
    maestro_repo.drop()
    maestro_repo.bulk_insert(jugadores)
    _inicializado = True
    return len(jugadores)
