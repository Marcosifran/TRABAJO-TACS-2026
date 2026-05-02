"""
Configuración global de pytest — compartida entre tests unitarios y de integración.
"""

import pytest
from app.repositories import (
    album_repo,
    publicacion_repo,
    usuario_repo,
    intercambio_repo,
    subasta_repo,
    oferta_repo,
    calificacion_repo,
)


@pytest.fixture(autouse=True)
def limpiar_db():
    """
    Se ejecuta automáticamente antes y después de cada test.
    Limpia el estado en memoria para garantizar aislamiento entre tests.
    """
    album_repo._db.clear()
    album_repo._next_id = 1
    publicacion_repo._db.clear()
    publicacion_repo._next_id = 1
    usuario_repo._db_faltantes.clear()
    intercambio_repo._db.clear()
    calificacion_repo._db.clear()
    subasta_repo._db_subastas.clear()
    oferta_repo._db_ofertas.clear()
    yield
