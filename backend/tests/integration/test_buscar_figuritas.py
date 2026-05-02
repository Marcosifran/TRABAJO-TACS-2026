"""
Tests de integración — Caso de uso: Buscar figuritas disponibles para intercambio.

Cubre el endpoint GET /api/v1/publicaciones/ verificando:
- Búsqueda sin filtros (devuelve todo)
- Filtro por número exacto
- Filtro por equipo (búsqueda parcial, case-insensitive)
- Filtro por jugador (búsqueda parcial, case-insensitive)
- Filtro por tipo de intercambio
- Combinación de filtros
- Casos sin resultados
- Las propias publicaciones no aparecen en la búsqueda pública
"""

import pytest

ENDPOINT_ALBUM = "/api/v1/album/"
ENDPOINT_PUBLICACIONES = "/api/v1/publicaciones/"


def agregar_y_publicar(client, token, numero, equipo, jugador, cantidad, tipo):
    """
    Helper: agrega una figurita al álbum y la publica para intercambio.
    Retorna la respuesta del POST a publicaciones.
    """
    resp_album = client.post(
        ENDPOINT_ALBUM,
        json={"numero": numero, "equipo": equipo, "jugador": jugador, "cantidad": cantidad},
        headers={"X-User-Token": token},
    )
    assert resp_album.status_code == 201
    figurita_id = resp_album.json()["id"]

    return client.post(
        ENDPOINT_PUBLICACIONES,
        json={
            "figurita_personal_id": figurita_id,
            "tipo_intercambio": tipo,
            "cantidad_disponible": 1,
        },
        headers={"X-User-Token": token},
    )


@pytest.fixture
def figuritas_cargadas(client, token_user1, token_user2):
    """
    Publica un conjunto de figuritas de distintos usuarios
    para usar como base en los tests de búsqueda.

    user1 publica: Messi #10 (directo), Di María #11 (subasta), Müller #20 (directo)
    user2 publica: Vinicius #7 (directo), Mbappé #9 (subasta)
    """
    datos = [
        (token_user1, 10, "Argentina", "Lionel Messi",   2, "intercambio_directo"),
        (token_user1, 11, "Argentina", "Di María",        2, "subasta"),
        (token_user2, 7,  "Brasil",    "Vinicius Junior", 1, "intercambio_directo"),
        (token_user2, 9,  "Francia",   "Kylian Mbappé",   3, "subasta"),
        (token_user1, 20, "Alemania",  "Thomas Müller",   1, "intercambio_directo"),
    ]
    for token, numero, equipo, jugador, cantidad, tipo in datos:
        resp = agregar_y_publicar(client, token, numero, equipo, jugador, cantidad, tipo)
        assert resp.status_code == 201


# -----------------------
# Búsqueda sin filtros
# -----------------------

class TestBusquedaSinFiltros:

    def test_sin_figuritas_devuelve_lista_vacia(self, client, token_user1):
        """Sin publicaciones activas la respuesta es una lista vacía."""
        resp = client.get(ENDPOINT_PUBLICACIONES, headers={"X-User-Token": token_user1})

        assert resp.status_code == 200
        assert resp.json() == []

    def test_devuelve_todas_las_publicaciones_menos_las_propias(self, client, token_user1, figuritas_cargadas):
        """
        Sin filtros devuelve todas las publicaciones excepto las del usuario autenticado.
        user1 tiene 3 publicaciones, user2 tiene 2.
        Cuando user1 consulta, ve solo las 2 de user2.
        """
        resp = client.get(ENDPOINT_PUBLICACIONES, headers={"X-User-Token": token_user1})

        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_user2_ve_publicaciones_de_user1(self, client, token_user2, figuritas_cargadas):
        """user2 ve las 3 publicaciones de user1."""
        resp = client.get(ENDPOINT_PUBLICACIONES, headers={"X-User-Token": token_user2})

        assert resp.status_code == 200
        assert len(resp.json()) == 3


# ---------------------
# Filtro por número
# ---------------------

class TestFiltroPorNumero:

    def test_filtro_por_numero_exacto_devuelve_coincidencia(self, client, token_user2, figuritas_cargadas):
        """Buscar por número exacto devuelve solo la figurita con ese número."""
        resp = client.get(
            ENDPOINT_PUBLICACIONES,
            params={"numero": 10},
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 200
        resultado = resp.json()
        assert len(resultado) == 1
        assert resultado[0]["numero"] == 10
        assert resultado[0]["jugador"] == "Lionel Messi"

    def test_filtro_por_numero_inexistente_devuelve_lista_vacia(self, client, token_user1, figuritas_cargadas):
        """Buscar un número que no existe devuelve lista vacía."""
        resp = client.get(
            ENDPOINT_PUBLICACIONES,
            params={"numero": 999},
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 200
        assert resp.json() == []


# ----------------------
# Filtro por equipo
# ----------------------

class TestFiltroPorEquipo:

    def test_filtro_por_equipo_exacto(self, client, token_user2, figuritas_cargadas):
        """
        Buscar por nombre exacto del equipo devuelve las figuritas de ese equipo.
        user2 consulta Argentina → ve las 2 figuritas de user1 (Messi y Di María).
        """
        resp = client.get(
            ENDPOINT_PUBLICACIONES,
            params={"equipo": "Argentina"},
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 200
        resultado = resp.json()
        assert len(resultado) == 2
        assert all(f["equipo"] == "Argentina" for f in resultado)

    def test_filtro_por_equipo_parcial(self, client, token_user2, figuritas_cargadas):
        """Buscar por substring del equipo devuelve las figuritas que lo contienen."""
        resp = client.get(
            ENDPOINT_PUBLICACIONES,
            params={"equipo": "rgen"},
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 200
        resultado = resp.json()
        assert len(resultado) == 2
        assert all("Argentina" in f["equipo"] for f in resultado)

    def test_filtro_por_equipo_inexistente_devuelve_lista_vacia(self, client, token_user1, figuritas_cargadas):
        """Buscar un equipo que no existe devuelve lista vacía."""
        resp = client.get(
            ENDPOINT_PUBLICACIONES,
            params={"equipo": "Uruguay"},
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 200
        assert resp.json() == []


# -----------------------
# Filtro por jugador
# -----------------------

class TestFiltroPorJugador:

    def test_filtro_por_jugador_exacto(self, client, token_user2, figuritas_cargadas):
        """Buscar por nombre completo del jugador devuelve la figurita correspondiente."""
        resp = client.get(
            ENDPOINT_PUBLICACIONES,
            params={"jugador": "Lionel Messi"},
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 200
        resultado = resp.json()
        assert len(resultado) == 1
        assert resultado[0]["numero"] == 10

    def test_filtro_por_jugador_parcial(self, client, token_user2, figuritas_cargadas):
        """Buscar por apellido devuelve las figuritas que lo contienen."""
        resp = client.get(
            ENDPOINT_PUBLICACIONES,
            params={"jugador": "Messi"},
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 200
        resultado = resp.json()
        assert len(resultado) == 1
        assert resultado[0]["numero"] == 10

    def test_filtro_por_jugador_inexistente_devuelve_lista_vacia(self, client, token_user1, figuritas_cargadas):
        """Buscar un jugador que no existe devuelve lista vacía."""
        resp = client.get(
            ENDPOINT_PUBLICACIONES,
            params={"jugador": "Ronaldo"},
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 200
        assert resp.json() == []


# ----------------------------
# Filtro por tipo intercambio
# ----------------------------

class TestFiltroPorTipoIntercambio:

    def test_filtro_por_intercambio_directo(self, client, token_user2, figuritas_cargadas):
        """
        Filtrar por intercambio_directo devuelve solo esas publicaciones.
        user1 tiene 2 de intercambio_directo (Messi #10 y Müller #20).
        user2 consulta y ve esas 2.
        """
        resp = client.get(
            ENDPOINT_PUBLICACIONES,
            params={"tipo_intercambio": "intercambio_directo"},
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 200
        resultado = resp.json()
        assert len(resultado) == 2
        assert all(f["tipo_intercambio"] == "intercambio_directo" for f in resultado)

    def test_filtro_por_subasta(self, client, token_user2, figuritas_cargadas):
        """
        Filtrar por subasta devuelve solo esas publicaciones.
        user1 tiene 1 subasta (Di María #11).
        user2 consulta y ve esa 1.
        """
        resp = client.get(
            ENDPOINT_PUBLICACIONES,
            params={"tipo_intercambio": "subasta"},
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 200
        resultado = resp.json()
        assert len(resultado) == 1
        assert resultado[0]["tipo_intercambio"] == "subasta"


# --------------------------
# Combinación de filtros
# --------------------------

class TestCombinacionFiltros:

    def test_filtro_por_numero_y_equipo(self, client, token_user2, figuritas_cargadas):
        """Combinar número y equipo devuelve solo la figurita que cumple ambos criterios."""
        resp = client.get(
            ENDPOINT_PUBLICACIONES,
            params={"numero": 10, "equipo": "Argentina"},
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 200
        resultado = resp.json()
        assert len(resultado) == 1
        assert resultado[0]["numero"] == 10

    def test_filtro_por_equipo_y_jugador(self, client, token_user2, figuritas_cargadas):
        """Combinar equipo y jugador devuelve la figurita que cumple ambos."""
        resp = client.get(
            ENDPOINT_PUBLICACIONES,
            params={"equipo": "Argentina", "jugador": "Messi"},
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 200
        resultado = resp.json()
        assert len(resultado) == 1
        assert resultado[0]["jugador"] == "Lionel Messi"

    def test_filtros_sin_interseccion_devuelven_lista_vacia(self, client, token_user1, figuritas_cargadas):
        """Filtros que no tienen intersección devuelven lista vacía."""
        resp = client.get(
            ENDPOINT_PUBLICACIONES,
            params={"equipo": "Brasil", "jugador": "Messi"},
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 200
        assert resp.json() == []

    def test_filtro_por_numero_equipo_y_jugador(self, client, token_user2, figuritas_cargadas):
        """Combinar los tres filtros devuelve la figurita que cumple todos."""
        resp = client.get(
            ENDPOINT_PUBLICACIONES,
            params={"numero": 10, "equipo": "Argentina", "jugador": "Messi"},
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 200
        resultado = resp.json()
        assert len(resultado) == 1
        assert resultado[0]["numero"] == 10