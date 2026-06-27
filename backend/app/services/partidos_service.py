"""
Servicio de partidos del Mundial 2026.
Obtiene datos de football-data.org y los cachea en MongoDB.
El mismo patrón que maestro_service: init una sola vez, refresh manual.
"""
from app.repositories import partido_repo
from app.scraping.football_api import fetch_partidos_wc

_inicializado = False


def inicializar() -> None:
    """
    Popula la colección partidos en el arranque si está vacía.
    Falla silenciosamente para no bloquear el startup si la API no está disponible.
    """
    global _inicializado
    if _inicializado:
        return
    _inicializado = True
    if partido_repo.count() > 0:
        return
    try:
        partidos = fetch_partidos_wc()
        partido_repo.replace_all(partidos)
        print(f"[partidos] Inicializado con {len(partidos)} partidos.")
    except Exception as exc:
        print(f"[partidos] No se pudo inicializar automáticamente: {exc}")


def get_todos() -> list[dict]:
    return partido_repo.get_all()


def refresh() -> int:
    """
    Vuelve a consultar football-data.org y reemplaza todos los partidos en MongoDB.
    Útil para traer resultados actualizados durante el torneo.
    """
    global _inicializado
    partidos = fetch_partidos_wc()
    partido_repo.replace_all(partidos)
    _inicializado = True
    return len(partidos)
