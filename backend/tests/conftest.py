"""
Configuración global de pytest — compartida entre tests unitarios y de integración.
"""

import pytest
from app.repositories import (
    figurita_repo,
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
    figurita_repo._db.clear()
    usuario_repo._db_faltantes.clear()
    intercambio_repo._db.clear()
    calificacion_repo._db.clear()
    subasta_repo._db_subastas.clear()
    oferta_repo._db_ofertas.clear()
    yield
