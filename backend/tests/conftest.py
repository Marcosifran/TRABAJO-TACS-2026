"""
Configuración global de pytest — compartida entre tests unitarios y de integración.
"""

import pytest
from app.core.database import connect_to_mongo, close_mongo_connection, get_db

_TEST_DB_NAME = "mundial_figuritas_test_db"
_TEST_MONGODB_URL = "mongodb://localhost:27017"

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
    Abre la conexión a MongoDB una sola vez para toda la sesión de tests,
    apuntando siempre a la base de datos de test — nunca a la de producción/dev,
    sin importar lo que diga el .env.
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
