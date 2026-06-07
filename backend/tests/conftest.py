"""
Configuración global de pytest — compartida entre tests unitarios y de integración.
"""

import os
import pytest
from app.core.database import connect_to_mongo, close_mongo_connection, get_db

# DB separada de prod/dev para que el drop final no destruya datos reales.
# Sobreescribir con TEST_MONGODB_URL si se corre fuera de Docker.
_TEST_DB_NAME = "mundial_figuritas_test"


def _default_test_mongodb_url() -> str:
    """Elige la URL de Mongo para tests según el entorno.

    - TEST_MONGODB_URL explícita: siempre gana.
    - En Docker Compose, `mongodb` resuelve y se usa ese host.
    - En el host, `mongodb` no resuelve, así que usamos `localhost`.
    """
    url = os.getenv("TEST_MONGODB_URL")
    if url:
        return url

    try:
        import socket

        socket.gethostbyname("mongodb")
        return "mongodb://mongodb:27017"
    except OSError:
        return "mongodb://localhost:27017"


_TEST_MONGODB_URL = _default_test_mongodb_url()



_COLLECTIONS = [
    "album",
    "publicaciones",
    "figuritas",
    "intercambios",
    "subastas",
    "ofertas",
    "calificaciones",
    "faltantes",
    "maestro_figuritas",
]


@pytest.fixture(scope="session", autouse=True)
def mongo_connection():
    """
    Abre la conexión a MongoDB una sola vez para toda la sesión de tests.
    Usa _TEST_DB_NAME (distinto a la DB de prod) para que el drop final
    no destruya datos reales. La URL se puede sobreescribir con TEST_MONGODB_URL.
    """
    connect_to_mongo(url=_TEST_MONGODB_URL, db_name=_TEST_DB_NAME)
    yield
    # Al finalizar la sesión limpiamos la base de test completa
    get_db().client.drop_database(_TEST_DB_NAME)
    close_mongo_connection()


@pytest.fixture(autouse=True)
def limpiar_db(mongo_connection):
    """
    Se ejecuta automáticamente antes de cada test.
    Limpia las colecciones de la base de test para garantizar aislamiento.
    """
    db = get_db()
    for col in _COLLECTIONS:
        db[col].delete_many({})
    yield
