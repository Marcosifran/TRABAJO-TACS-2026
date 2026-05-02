"""
Tests de calificaciones tras intercambio aceptado y consulta de reputación.
"""

import pytest
from fastapi.testclient import TestClient
from app.dependencies import get_current_user
from app.main import app

ENDPOINT_ALBUM        = "/api/v1/album/"
ENDPOINT_PUBLICACIONES = "/api/v1/publicaciones/"
ENDPOINT_FALTANTES    = "/api/v1/usuarios/faltantes"
ENDPOINT_INTERCAMBIOS = "/api/v1/intercambios/"


def agregar_y_publicar(client, token, numero, equipo, jugador, cantidad=1, tipo="intercambio_directo"):
    """Agrega al álbum y publica para intercambio. Retorna el id de la publicación."""
    resp_album = client.post(
        ENDPOINT_ALBUM,
        json={"numero": numero, "equipo": equipo, "jugador": jugador, "cantidad": cantidad},
        headers={"X-User-Token": token},
    )
    assert resp_album.status_code == 201
    figurita_id = resp_album.json()["id"]

    resp_pub = client.post(
        ENDPOINT_PUBLICACIONES,
        json={
            "figurita_personal_id": figurita_id,
            "tipo_intercambio": tipo,
            "cantidad_disponible": 1,
        },
        headers={"X-User-Token": token},
    )
    assert resp_pub.status_code == 201
    return resp_pub.json()["id"]


def _intercambio_aceptado(client, token_user1, token_user2) -> int:
    """
    Crea y acepta un intercambio entre user1 y user2.
    user1 publica #1, user2 publica #2, user1 propone, user2 acepta.
    """
    agregar_y_publicar(client, token_user1, 1, "Argentina", "Jugador 1")
    agregar_y_publicar(client, token_user2, 2, "Brasil", "Jugador 2")

    resp = client.post(
        ENDPOINT_INTERCAMBIOS,
        json={
            "figuritas_ofrecidas_numero": [1],
            "figurita_solicitada_numero": 2,
            "solicitado_a_id": 2,
        },
        headers={"X-User-Token": token_user1},
    )
    assert resp.status_code == 201
    intercambio_id = resp.json()["id"]

    resp_patch = client.patch(
        f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/estado",
        json={"estado": "aceptado"},
        headers={"X-User-Token": token_user2},
    )
    assert resp_patch.status_code == 200
    return intercambio_id


class TestCalificarTrasIntercambio:

    def test_calificar_despues_de_aceptar_201(self, client, token_user1, token_user2):
        intercambio_id = _intercambio_aceptado(client, token_user1, token_user2)
        url = f"/api/v1/intercambios/{intercambio_id}/calificaciones"
        resp = client.post(
            url,
            json={"puntuacion": 5, "comentario": "Todo bien"},
            headers={"X-User-Token": token_user2},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["intercambio_id"] == intercambio_id
        assert data["calificador_id"] == 2
        assert data["calificado_id"] == 1
        assert data["puntuacion"] == 5
        assert data["comentario"] == "Todo bien"

    def test_proponente_tambien_puede_calificar(self, client, token_user1, token_user2):
        intercambio_id = _intercambio_aceptado(client, token_user1, token_user2)
        url = f"/api/v1/intercambios/{intercambio_id}/calificaciones"
        resp = client.post(url, json={"puntuacion": 4}, headers={"X-User-Token": token_user1})

        assert resp.status_code == 201
        assert resp.json()["calificador_id"] == 1
        assert resp.json()["calificado_id"] == 2

    @pytest.mark.parametrize("estado_final", ["pendiente", "rechazado"])
    def test_no_calificar_intercambio_no_aceptado_400(self, client, token_user1, token_user2, estado_final):
        agregar_y_publicar(client, token_user1, 1, "Argentina", "J1")
        agregar_y_publicar(client, token_user2, 2, "Brasil", "J2")

        resp = client.post(
            ENDPOINT_INTERCAMBIOS,
            json={"figuritas_ofrecidas_numero": [1], "figurita_solicitada_numero": 2, "solicitado_a_id": 2},
            headers={"X-User-Token": token_user1},
        )
        assert resp.status_code == 201
        intercambio_id = resp.json()["id"]

        if estado_final == "rechazado":
            client.patch(
                f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/estado",
                json={"estado": "rechazado"},
                headers={"X-User-Token": token_user2},
            )

        resp_cal = client.post(
            f"/api/v1/intercambios/{intercambio_id}/calificaciones",
            json={"puntuacion": 3},
            headers={"X-User-Token": token_user2},
        )
        assert resp_cal.status_code == 400

    def test_usuario_no_participa_403(self, client, token_user1, token_user2):
        intercambio_id = _intercambio_aceptado(client, token_user1, token_user2)
        url = f"/api/v1/intercambios/{intercambio_id}/calificaciones"

        def fake_user():
            return {"id": 99, "nombre": "otro", "email": "otro@test", "token": "x"}

        app.dependency_overrides[get_current_user] = fake_user
        try:
            c = TestClient(app)
            resp = c.post(url, json={"puntuacion": 5}, headers={"X-User-Token": "cualquiera"})
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 403

    def test_duplicado_misma_calificacion_409(self, client, token_user1, token_user2):
        intercambio_id = _intercambio_aceptado(client, token_user1, token_user2)
        url = f"/api/v1/intercambios/{intercambio_id}/calificaciones"
        headers = {"X-User-Token": token_user2}
        assert client.post(url, json={"puntuacion": 5}, headers=headers).status_code == 201
        resp2 = client.post(url, json={"puntuacion": 4}, headers=headers)
        assert resp2.status_code == 409

    def test_intercambio_inexistente_404(self, client, token_user1):
        resp = client.post(
            "/api/v1/intercambios/99999/calificaciones",
            json={"puntuacion": 5},
            headers={"X-User-Token": token_user1},
        )
        assert resp.status_code == 404


class TestReputacion:

    def test_sin_calificaciones_promedio_null(self, client):
        resp = client.get("/api/v1/usuarios/1/reputacion")
        assert resp.status_code == 200
        data = resp.json()
        assert data["usuario_id"] == 1
        assert data["cantidad_calificaciones"] == 0
        assert data["promedio_puntuacion"] is None

    def test_usuario_inexistente_404(self, client):
        resp = client.get("/api/v1/usuarios/99999/reputacion")
        assert resp.status_code == 404

    def test_promedio_con_varias_calificaciones(self, client, token_user1, token_user2):
        i1 = _intercambio_aceptado(client, token_user1, token_user2)
        client.post(
            f"/api/v1/intercambios/{i1}/calificaciones",
            json={"puntuacion": 4},
            headers={"X-User-Token": token_user2},
        )

        agregar_y_publicar(client, token_user1, 3, "Argentina", "J3")
        agregar_y_publicar(client, token_user2, 4, "Brasil", "J4")

        resp_prop = client.post(
            ENDPOINT_INTERCAMBIOS,
            json={"figuritas_ofrecidas_numero": [3], "figurita_solicitada_numero": 4, "solicitado_a_id": 2},
            headers={"X-User-Token": token_user1},
        )
        assert resp_prop.status_code == 201
        i2 = resp_prop.json()["id"]

        client.patch(
            f"{ENDPOINT_INTERCAMBIOS}{i2}/estado",
            json={"estado": "aceptado"},
            headers={"X-User-Token": token_user2},
        )
        client.post(
            f"/api/v1/intercambios/{i2}/calificaciones",
            json={"puntuacion": 5},
            headers={"X-User-Token": token_user2},
        )

        rep = client.get("/api/v1/usuarios/1/reputacion").json()
        assert rep["cantidad_calificaciones"] == 2
        assert rep["promedio_puntuacion"] == 4.5