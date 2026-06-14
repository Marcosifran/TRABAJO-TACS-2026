"""
Fixtures exclusivas para tests de integración.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.security import create_access_token


@pytest.fixture
def client():
    """
    Retorna un TestClient de FastAPI.
    Permite realizar requests HTTP contra la app sin levantar un servidor real.
    """
    return TestClient(app)


@pytest.fixture
def token_user1():
    """
    Valor del header Authorization para el usuario sembrado 1 (marcos, id 1).
    Es un JWT real generado en el momento, listo para usar como
    headers={"Authorization": token_user1}.
    """
    return f"Bearer {create_access_token(subject=1, email='marcos@utn')}"


@pytest.fixture
def token_user2():
    """
    Valor del header Authorization para el usuario sembrado 2 (jeronimo, id 2).
    Mismo formato que token_user1.
    """
    return f"Bearer {create_access_token(subject=2, email='jeronimo@utn')}"


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