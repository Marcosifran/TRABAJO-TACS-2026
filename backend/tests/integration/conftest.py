"""
Fixtures exclusivas para tests de integración.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositories import usuario_repo


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
def figurita_album_valida():
    """
    Payload base para agregar una figurita al álbum personal.
    No incluye tipo_intercambio — eso va en la publicación.
    """
    return {
        "numero": 10,
        "equipo": "Argentina",
        "jugador": "Lionel Messi",
        "cantidad": 2,
    }


@pytest.fixture
def figurita_valida():
    """
    Payload base completo para el flujo completo:
    agregar al álbum + publicar para intercambio.
    Se mantiene por compatibilidad con tests de autenticación.
    """
    return {
        "numero": 10,
        "equipo": "Argentina",
        "jugador": "Lionel Messi",
        "cantidad": 2,
    }