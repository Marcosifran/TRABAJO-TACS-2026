"""
Tests de calificaciones tras intercambio aceptado y consulta de reputación.
"""

from fastapi.testclient import TestClient

from app.dependencies import get_current_user
from app.main import app

ENDPOINT_FIGURITAS = "/api/v1/figuritas/"
ENDPOINT_FALTANTES = "/api/v1/usuarios/faltantes"
ENDPOINT_INTERCAMBIOS = "/api/v1/intercambios/"


def _intercambio_aceptado(client, token_user1, token_user2) -> int:
    client.post(
        ENDPOINT_FIGURITAS,
        json={
            "numero": 1,
            "equipo": "Argentina",
            "jugador": "Jugador 1",
            "cantidad": 1,
            "tipo_intercambio": "intercambio_directo",
        },
        headers={"X-User-Token": token_user1},
    )
    client.post(
        ENDPOINT_FIGURITAS,
        json={
            "numero": 2,
            "equipo": "Brasil",
            "jugador": "Jugador 2",
            "cantidad": 1,
            "tipo_intercambio": "intercambio_directo",
        },
        headers={"X-User-Token": token_user2},
    )
    resp = client.post(
        ENDPOINT_INTERCAMBIOS,
        json={
            "figurita_ofrecida_numero": 1,
            "figurita_solicitada_numero": 2,
            "solicitado_a_id": 2,
        },
        headers={"X-User-Token": token_user1},
    )
    assert resp.status_code == 200
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
        resp = client.post(
            url,
            json={"puntuacion": 4},
            headers={"X-User-Token": token_user1},
        )
        assert resp.status_code == 201
        assert resp.json()["calificador_id"] == 1
        assert resp.json()["calificado_id"] == 2

    def test_no_calificar_intercambio_pendiente_400(self, client, token_user1, token_user2):
        client.post(
            ENDPOINT_FIGURITAS,
            json={
                "numero": 1,
                "equipo": "Argentina",
                "jugador": "J1",
                "cantidad": 1,
                "tipo_intercambio": "intercambio_directo",
            },
            headers={"X-User-Token": token_user1},
        )
        client.post(
            ENDPOINT_FIGURITAS,
            json={
                "numero": 2,
                "equipo": "Brasil",
                "jugador": "J2",
                "cantidad": 1,
                "tipo_intercambio": "intercambio_directo",
            },
            headers={"X-User-Token": token_user2},
        )
        resp = client.post(
            ENDPOINT_INTERCAMBIOS,
            json={
                "figurita_ofrecida_numero": 1,
                "figurita_solicitada_numero": 2,
                "solicitado_a_id": 2,
            },
            headers={"X-User-Token": token_user1},
        )
        assert resp.status_code == 200
        intercambio_id = resp.json()["id"]
        url = f"/api/v1/intercambios/{intercambio_id}/calificaciones"
        resp_cal = client.post(
            url,
            json={"puntuacion": 3},
            headers={"X-User-Token": token_user2},
        )
        assert resp_cal.status_code == 400

    def test_no_calificar_intercambio_rechazado_400(self, client, token_user1, token_user2):
        client.post(
            ENDPOINT_FIGURITAS,
            json={
                "numero": 1,
                "equipo": "Argentina",
                "jugador": "J1",
                "cantidad": 1,
                "tipo_intercambio": "intercambio_directo",
            },
            headers={"X-User-Token": token_user1},
        )
        client.post(
            ENDPOINT_FIGURITAS,
            json={
                "numero": 2,
                "equipo": "Brasil",
                "jugador": "J2",
                "cantidad": 1,
                "tipo_intercambio": "intercambio_directo",
            },
            headers={"X-User-Token": token_user2},
        )
        resp = client.post(
            ENDPOINT_INTERCAMBIOS,
            json={
                "figurita_ofrecida_numero": 1,
                "figurita_solicitada_numero": 2,
                "solicitado_a_id": 2,
            },
            headers={"X-User-Token": token_user1},
        )
        intercambio_id = resp.json()["id"]
        client.patch(
            f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/estado",
            json={"estado": "rechazado"},
            headers={"X-User-Token": token_user2},
        )
        url = f"/api/v1/intercambios/{intercambio_id}/calificaciones"
        resp_cal = client.post(
            url,
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
        url = "/api/v1/intercambios/99999/calificaciones"
        resp = client.post(
            url,
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

        client.post(
            ENDPOINT_FIGURITAS,
            json={
                "numero": 3,
                "equipo": "Argentina",
                "jugador": "J3",
                "cantidad": 1,
                "tipo_intercambio": "intercambio_directo",
            },
            headers={"X-User-Token": token_user1},
        )
        client.post(
            ENDPOINT_FIGURITAS,
            json={
                "numero": 4,
                "equipo": "Brasil",
                "jugador": "J4",
                "cantidad": 1,
                "tipo_intercambio": "intercambio_directo",
            },
            headers={"X-User-Token": token_user2},
        )
        resp_prop = client.post(
            ENDPOINT_INTERCAMBIOS,
            json={
                "figurita_ofrecida_numero": 3,
                "figurita_solicitada_numero": 4,
                "solicitado_a_id": 2,
            },
            headers={"X-User-Token": token_user1},
        )
        assert resp_prop.status_code == 200
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
