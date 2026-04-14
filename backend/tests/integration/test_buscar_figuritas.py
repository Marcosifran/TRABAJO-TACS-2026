"""
Tests de integración — Caso de uso: Buscar figuritas disponibles.

Cubre el endpoint GET /api/v1/figuritas/ verificando:
- Búsqueda sin filtros (devuelve todo)
- Filtro por número exacto
- Filtro por equipo (búsqueda parcial, case-insensitive)
- Filtro por jugador (búsqueda parcial, case-insensitive)
- Combinación de filtros
- Casos sin resultados
"""

import pytest

ENDPOINT = "/api/v1/figuritas/"

'''
Se define un fixture que carga un conjunto de figuritas de prueba antes
de ejecutar los tests de búsqueda.
'''
@pytest.fixture
def figuritas_cargadas(client, token_user1, token_user2):
    """
    Publica un conjunto de figuritas de distintos usuarios para usar como base en los tests de búsqueda.
    """
    figuritas = [
        {"numero": 10, "equipo": "Argentina", "jugador": "Lionel Messi",   "cantidad": 1, "tipo_intercambio": "intercambio_directo"},
        {"numero": 11, "equipo": "Argentina", "jugador": "Di María",        "cantidad": 2, "tipo_intercambio": "subasta"},
        {"numero": 7,  "equipo": "Brasil",    "jugador": "Vinicius Junior", "cantidad": 1, "tipo_intercambio": "intercambio_directo"},
        {"numero": 9,  "equipo": "Francia",   "jugador": "Kylian Mbappé",   "cantidad": 3, "tipo_intercambio": "subasta"},
        {"numero": 20, "equipo": "Alemania",  "jugador": "Thomas Müller",   "cantidad": 1, "tipo_intercambio": "intercambio_directo"},
    ]
    tokens = [token_user1, token_user1, token_user2, token_user2, token_user1]
    # zip permite iterar simultáneamente sobre figuritas y tokens.
    for figurita, token in zip(figuritas, tokens):
        client.post(ENDPOINT, json=figurita, headers={"X-User-Token": token})


# -----------------------
# Búsqueda sin filtros
# -----------------------

class TestBusquedaSinFiltros:

    def test_sin_figuritas_devuelve_lista_vacia(self, client):
        """Sin figuritas publicadas la respuesta es una lista vacía."""
        resp = client.get(ENDPOINT)

        assert resp.status_code == 200
        assert resp.json()["figuritasDisponibles"] == []

    def test_devuelve_todas_las_figuritas_disponibles(self, client, figuritas_cargadas):
        """Sin filtros devuelve todas las figuritas publicadas."""
        resp = client.get(ENDPOINT)

        assert resp.status_code == 200
        assert len(resp.json()["figuritasDisponibles"]) == 5


# ---------------------
# Filtro por número
# ---------------------

class TestFiltroPorNumero:

    def test_filtro_por_numero_exacto_devuelve_coincidencia(self, client, figuritas_cargadas):
        """Buscar por número exacto devuelve solo la figurita con ese número."""
        resp = client.get(ENDPOINT, params={"numero": 10})

        assert resp.status_code == 200
        resultado = resp.json()["figuritasDisponibles"]
        assert len(resultado) == 1
        assert resultado[0]["numero"] == 10
        assert resultado[0]["jugador"] == "Lionel Messi"

    def test_filtro_por_numero_inexistente_devuelve_lista_vacia(self, client, figuritas_cargadas):
        """Buscar un número que no existe devuelve lista vacía."""
        resp = client.get(ENDPOINT, params={"numero": 999})

        assert resp.status_code == 200
        assert resp.json()["figuritasDisponibles"] == []

    def test_filtro_por_numero_cero_devuelve_422(self, client):
        """El número de figurita debe ser >= 1. Enviar 0 devuelve 422."""
        resp = client.get(ENDPOINT, params={"numero": 0})

        assert resp.status_code == 422

    def test_filtro_por_numero_negativo_devuelve_422(self, client):
        """Número negativo devuelve 422."""
        resp = client.get(ENDPOINT, params={"numero": -1})

        assert resp.status_code == 422


# ----------------------
# Filtro por equipo
# ----------------------

class TestFiltroPorEquipo:

    def test_filtro_por_equipo_exacto(self, client, figuritas_cargadas):
        """Buscar por nombre de equipo exacto devuelve las figuritas de ese equipo."""
        resp = client.get(ENDPOINT, params={"equipo": "Argentina"})

        assert resp.status_code == 200
        resultado = resp.json()["figuritasDisponibles"]
        assert len(resultado) == 2
        assert all(f["equipo"] == "Argentina" for f in resultado)

    def test_filtro_por_equipo_parcial(self, client, figuritas_cargadas):
        """Buscar por substring del equipo devuelve las figuritas que lo contienen."""
        resp = client.get(ENDPOINT, params={"equipo": "rgen"})

        assert resp.status_code == 200
        resultado = resp.json()["figuritasDisponibles"]
        assert len(resultado) == 2
        assert all("Argentina" in f["equipo"] for f in resultado) # Chequeamos que argentina este contenido en el equipo de cada resultado

    def test_filtro_por_equipo_inexistente_devuelve_lista_vacia(self, client, figuritas_cargadas):
        """Buscar un equipo que no existe devuelve lista vacía."""
        resp = client.get(ENDPOINT, params={"equipo": "Uruguay"})

        assert resp.status_code == 200
        assert resp.json()["figuritasDisponibles"] == []

    def test_filtro_por_equipo_vacio_devuelve_422(self, client):
        """Pasar equipo como string vacío devuelve 422."""
        resp = client.get(ENDPOINT, params={"equipo": ""})

        assert resp.status_code == 422


# -----------------------
# Filtro por jugador
# -----------------------

class TestFiltroPorJugador:

    def test_filtro_por_jugador_exacto(self, client, figuritas_cargadas):
        """Buscar por nombre completo del jugador devuelve la figurita correspondiente."""
        resp = client.get(ENDPOINT, params={"jugador": "Lionel Messi"})

        assert resp.status_code == 200
        resultado = resp.json()["figuritasDisponibles"]
        assert len(resultado) == 1
        assert resultado[0]["numero"] == 10
        assert resultado[0]["jugador"] == "Lionel Messi"

    def test_filtro_por_jugador_parcial(self, client, figuritas_cargadas):
        """Buscar por apellido devuelve las figuritas que lo contienen."""
        resp = client.get(ENDPOINT, params={"jugador": "Messi"})

        assert resp.status_code == 200
        resultado = resp.json()["figuritasDisponibles"]
        assert len(resultado) == 1
        assert resultado[0]["numero"] == 10

    def test_filtro_por_jugador_inexistente_devuelve_lista_vacia(self, client, figuritas_cargadas):
        """Buscar un jugador que no existe devuelve lista vacía."""
        resp = client.get(ENDPOINT, params={"jugador": "Ronaldo"})

        assert resp.status_code == 200
        assert resp.json()["figuritasDisponibles"] == []

    def test_filtro_por_jugador_vacio_devuelve_422(self, client):
        """Pasar jugador como string vacío devuelve 422."""
        resp = client.get(ENDPOINT, params={"jugador": ""})

        assert resp.status_code == 422


# --------------------------
# Combinación de filtros
# --------------------------

class TestCombinacionFiltros:

    def test_filtro_por_numero_y_equipo(self, client, figuritas_cargadas):
        """Combinar número y equipo devuelve solo la figurita que cumple ambos criterios."""
        resp = client.get(ENDPOINT, params={"numero": 10, "equipo": "Argentina"})

        assert resp.status_code == 200
        resultado = resp.json()["figuritasDisponibles"]
        assert len(resultado) == 1
        assert resultado[0]["numero"] == 10

    def test_filtro_por_equipo_y_jugador(self, client, figuritas_cargadas):
        """Combinar equipo y jugador devuelve la figurita que cumple ambos."""
        resp = client.get(ENDPOINT, params={"equipo": "Argentina", "jugador": "Messi"})

        assert resp.status_code == 200
        resultado = resp.json()["figuritasDisponibles"]
        assert len(resultado) == 1
        assert resultado[0]["jugador"] == "Lionel Messi"

    def test_filtros_sin_interseccion_devuelven_lista_vacia(self, client, figuritas_cargadas):
        """Filtros que no tienen intersección devuelven lista vacía."""
        resp = client.get(ENDPOINT, params={"equipo": "Argentina", "jugador": "Mbappé"})

        assert resp.status_code == 200
        assert resp.json()["figuritasDisponibles"] == []

    def test_filtro_por_numero_equipo_y_jugador(self, client, figuritas_cargadas):
        """Combinar los tres filtros devuelve la figurita que cumple todos."""
        resp = client.get(ENDPOINT, params={"numero": 10, "equipo": "Argentina", "jugador": "Messi"})

        assert resp.status_code == 200
        resultado = resp.json()["figuritasDisponibles"]
        assert len(resultado) == 1
        assert resultado[0]["numero"] == 10
