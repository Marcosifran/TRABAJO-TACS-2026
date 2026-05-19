"""
Tests de integración — Maestro de Figuritas

Cubre los endpoints HTTP sin depender del scraper real:
los tests insertan datos directamente en la colección de prueba.
"""

import pytest
from unittest.mock import patch
from app.repositories import maestro_repo

ENDPOINT = "/api/v1/maestro/"

_JUGADORES_PRUEBA = [
    {"numero": 1,  "equipo": "Argentina", "jugador": "Emiliano Martínez", "posicion": "GK", "numero_camiseta": 1},
    {"numero": 2,  "equipo": "Argentina", "jugador": "Julián Álvarez",    "posicion": "FW", "numero_camiseta": 9},
    {"numero": 3,  "equipo": "Argentina", "jugador": "Lionel Messi",      "posicion": "FW", "numero_camiseta": 10},
    {"numero": 4,  "equipo": "Brazil",    "jugador": "Alisson",           "posicion": "GK", "numero_camiseta": 1},
    {"numero": 5,  "equipo": "Brazil",    "jugador": "Vinícius Júnior",   "posicion": "FW", "numero_camiseta": 10},
]


@pytest.fixture
def maestro_con_datos():
    """Puebla el maestro con datos de prueba antes de cada test que lo requiera."""
    maestro_repo.bulk_insert(_JUGADORES_PRUEBA)


# ────────────────────────────────────────────
# GET /maestro/{numero}
# ────────────────────────────────────────────

class TestObtenerJugador:

    def test_numero_existente_devuelve_200_con_datos(self, client, maestro_con_datos):
        resp = client.get(f"{ENDPOINT}3")
        assert resp.status_code == 200
        data = resp.json()
        assert data["numero"] == 3
        assert data["equipo"] == "Argentina"
        assert data["jugador"] == "Lionel Messi"
        assert data["posicion"] == "FW"
        assert data["numero_camiseta"] == 10

    def test_numero_inexistente_devuelve_404(self, client):
        resp = client.get(f"{ENDPOINT}9999")
        assert resp.status_code == 404

    def test_respuesta_tiene_todos_los_campos(self, client, maestro_con_datos):
        resp = client.get(f"{ENDPOINT}1")
        assert resp.status_code == 200
        data = resp.json()
        assert set(data.keys()) == {"numero", "equipo", "jugador", "posicion", "numero_camiseta"}


# ────────────────────────────────────────────
# GET /maestro/equipos
# ────────────────────────────────────────────

class TestListarEquipos:

    def test_devuelve_equipos_ordenados_alfabeticamente(self, client, maestro_con_datos):
        resp = client.get(f"{ENDPOINT}equipos")
        assert resp.status_code == 200
        equipos = resp.json()["equipos"]
        assert equipos == sorted(equipos)
        assert "Argentina" in equipos
        assert "Brazil" in equipos

    def test_sin_datos_devuelve_lista_vacia(self, client):
        resp = client.get(f"{ENDPOINT}equipos")
        assert resp.status_code == 200
        assert resp.json()["equipos"] == []

    def test_no_devuelve_duplicados(self, client, maestro_con_datos):
        resp = client.get(f"{ENDPOINT}equipos")
        equipos = resp.json()["equipos"]
        assert len(equipos) == len(set(equipos))


# ────────────────────────────────────────────
# GET /maestro/
# ────────────────────────────────────────────

class TestListarJugadores:

    def test_sin_filtro_devuelve_todos(self, client, maestro_con_datos):
        resp = client.get(ENDPOINT)
        assert resp.status_code == 200
        jugadores = resp.json()["jugadores"]
        assert len(jugadores) == len(_JUGADORES_PRUEBA)

    def test_filtro_equipo_devuelve_solo_ese_equipo(self, client, maestro_con_datos):
        resp = client.get(ENDPOINT, params={"equipo": "Argentina"})
        assert resp.status_code == 200
        jugadores = resp.json()["jugadores"]
        assert len(jugadores) == 3
        assert all(j["equipo"] == "Argentina" for j in jugadores)

    def test_filtro_equipo_es_case_insensitive(self, client, maestro_con_datos):
        resp = client.get(ENDPOINT, params={"equipo": "argentina"})
        assert resp.status_code == 200
        assert len(resp.json()["jugadores"]) == 3

    def test_filtro_equipo_inexistente_devuelve_lista_vacia(self, client, maestro_con_datos):
        resp = client.get(ENDPOINT, params={"equipo": "Wakanda"})
        assert resp.status_code == 200
        assert resp.json()["jugadores"] == []

    def test_sin_datos_devuelve_lista_vacia(self, client):
        resp = client.get(ENDPOINT)
        assert resp.status_code == 200
        assert resp.json()["jugadores"] == []


# ────────────────────────────────────────────
# POST /maestro/refresh
# ────────────────────────────────────────────

class TestRefreshMaestro:

    def test_refresh_popula_la_coleccion(self, client):
        fake_jugadores = [
            {"numero": 1, "equipo": "TestFC", "jugador": "Jugador Uno", "posicion": "GK", "numero_camiseta": 1},
            {"numero": 2, "equipo": "TestFC", "jugador": "Jugador Dos", "posicion": "FW", "numero_camiseta": 9},
        ]
        with patch("app.services.maestro_service.scrape_planteles", return_value=fake_jugadores):
            resp = client.post(f"{ENDPOINT}refresh")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_jugadores"] == 2
        assert maestro_repo.count() == 2

    def test_refresh_reemplaza_datos_existentes(self, client, maestro_con_datos):
        nuevos = [{"numero": 1, "equipo": "Nuevo", "jugador": "Nuevo Jugador", "posicion": "MF", "numero_camiseta": 8}]
        with patch("app.services.maestro_service.scrape_planteles", return_value=nuevos):
            resp = client.post(f"{ENDPOINT}refresh")

        assert resp.status_code == 200
        assert maestro_repo.count() == 1
        assert maestro_repo.get_by_numero(1)["equipo"] == "Nuevo"

    def test_refresh_devuelve_503_si_scrape_falla(self, client):
        with patch("app.services.maestro_service.scrape_planteles", side_effect=Exception("timeout")):
            resp = client.post(f"{ENDPOINT}refresh")
        assert resp.status_code == 503
