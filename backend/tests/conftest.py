"""
Configuración global de pytest para los tests de integración.

Define fixtures compartidas entre todos los módulos de test:
- client: TestClient de FastAPI (sin servidor HTTP real)
- limpiar_db: limpia el estado en memoria antes de cada test (pruebas aisladas)
- token_user1 / token_user2: tokens válidos cargados desde el entorno
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositories import figurita_repo, usuario_repo, intercambio_repo, subasta_repo, oferta_repo

# Con fixture autouse ejecutamos entre tests el método limpiar_db.
@pytest.fixture(autouse=True)
def limpiar_db():
    """
    Se ejecuta automáticamente antes y después de cada test.
    Limpia el estado en memoria para garantizar aislamiento entre tests.
    """
    figurita_repo._db.clear()
    usuario_repo._db_faltantes.clear()
    intercambio_repo._db.clear()
    subasta_repo._db_subastas.clear()
    oferta_repo._db_ofertas.clear()
    yield # Ejecutamos el test


@pytest.fixture
def client():
    """
    Retorna un TestClient de FastAPI.
    Permite realizar requests HTTP contra la app sin levantar un servidor real.
    """
    return TestClient(app)


@pytest.fixture
def token_user1():
    """Token del usuario 1, cargado desde el entorno."""
    return usuario_repo._db_usuarios[0]["token"]


@pytest.fixture
def token_user2():
    """Token del usuario 2, cargado desde el entorno."""
    return usuario_repo._db_usuarios[1]["token"]


@pytest.fixture
def figurita_valida():
    """Payload base para publicar una figurita válida y no repetir código."""
    return {
        "numero": 10,
        "equipo": "Argentina",
        "jugador": "Lionel Messi",
        "cantidad": 2,
        "tipo_intercambio": "intercambio_directo"
    }
