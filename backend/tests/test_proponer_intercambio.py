"""
Tests de integración — Caso de uso: Proponer intercambio dirigido.

Escenario cubierto:
- user1 publica la figurita 1
- user2 publica la figurita 2
- user1 registra como faltante la figurita 2
- user1 propone intercambio a user2
"""

ENDPOINT_FIGURITAS = "/api/v1/figuritas/"
ENDPOINT_FALTANTES = "/api/v1/usuarios/faltantes"
ENDPOINT_INTERCAMBIOS = "/api/v1/intercambios/"


class TestProponerIntercambio:

    def test_user1_publica_faltante_y_propone_intercambio_a_user2(self, client, token_user1, token_user2):
        figurita_user1 = {
            "numero": 1,
            "equipo": "Argentina",
            "jugador": "Jugador 1",
            "cantidad": 1,
            "tipo_intercambio": "intercambio_directo",
        }
        figurita_user2 = {
            "numero": 2,
            "equipo": "Brasil",
            "jugador": "Jugador 2",
            "cantidad": 1,
            "tipo_intercambio": "intercambio_directo",
        }

        resp_pub_user1 = client.post(
            ENDPOINT_FIGURITAS,
            json=figurita_user1,
            headers={"X-User-Token": token_user1},
        )
        resp_pub_user2 = client.post(
            ENDPOINT_FIGURITAS,
            json=figurita_user2,
            headers={"X-User-Token": token_user2},
        )

        assert resp_pub_user1.status_code == 201
        assert resp_pub_user2.status_code == 201

        resp_faltante = client.post(
            ENDPOINT_FALTANTES,
            json={"numero_figurita": 2},
            headers={"X-User-Token": token_user1},
        )

        assert resp_faltante.status_code == 201
        assert resp_faltante.json()["data"]["numero_figurita"] == 2
        assert resp_faltante.json()["data"]["usuario_id"] == 1

        propuesta = {
            "figurita_ofrecida_numero": 1,
            "figurita_solicitada_numero": 2,
            "solicitado_a_id": 2,
        }
        resp_intercambio = client.post(
            ENDPOINT_INTERCAMBIOS,
            json=propuesta,
            headers={"X-User-Token": token_user1},
        )

        assert resp_intercambio.status_code == 200
        data = resp_intercambio.json()
        assert data["propuesto_por"] == 1
        assert data["solicitado_a"] == 2
        assert data["figurita_ofrecida"] == 1
        assert data["figurita_solicitada"] == 2
        assert data["estado"] == "pendiente"

    def test_no_permite_intercambiar_misma_figurita(self, client, token_user1, token_user2):
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
                "numero": 1,
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
                "figurita_solicitada_numero": 1,
                "solicitado_a_id": 2,
            },
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 400
        assert resp.json()["detail"] == "La figurita ofrecida y solicitada no pueden ser la misma"

    def test_no_permite_proponer_intercambio_a_si_mismo(self, client, token_user1):
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
                "equipo": "Argentina",
                "jugador": "Jugador 2",
                "cantidad": 1,
                "tipo_intercambio": "intercambio_directo",
            },
            headers={"X-User-Token": token_user1},
        )

        resp = client.post(
            ENDPOINT_INTERCAMBIOS,
            json={
                "figurita_ofrecida_numero": 1,
                "figurita_solicitada_numero": 2,
                "solicitado_a_id": 1,
            },
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 400
        assert resp.json()["detail"] == "No podés proponerte un intercambio a vos mismo"

    def test_falla_si_usuario_no_tiene_publicada_la_figurita_ofrecida(self, client, token_user1, token_user2):
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
                "figurita_ofrecida_numero": 99,
                "figurita_solicitada_numero": 2,
                "solicitado_a_id": 2,
            },
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 404
        assert resp.json()["detail"] == "No tenés publicada la figurita que ofrecés"

    def test_falla_si_usuario_destino_no_tiene_publicada_figurita_solicitada(self, client, token_user1, token_user2):
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

        resp = client.post(
            ENDPOINT_INTERCAMBIOS,
            json={
                "figurita_ofrecida_numero": 1,
                "figurita_solicitada_numero": 2,
                "solicitado_a_id": 2,
            },
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 404
        assert resp.json()["detail"] == "El usuario destino no tiene publicada la figurita solicitada"

    def test_falla_si_figurita_ofrecida_no_es_intercambio_directo(self, client, token_user1, token_user2):
        client.post(
            ENDPOINT_FIGURITAS,
            json={
                "numero": 1,
                "equipo": "Argentina",
                "jugador": "Jugador 1",
                "cantidad": 1,
                "tipo_intercambio": "subasta",
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

        assert resp.status_code == 400
        assert resp.json()["detail"] == "Tu figurita ofrecida no está configurada para intercambio directo"

    def test_falla_si_figurita_solicitada_no_es_intercambio_directo(self, client, token_user1, token_user2):
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
                "tipo_intercambio": "subasta",
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

        assert resp.status_code == 400
        assert resp.json()["detail"] == "La figurita solicitada no está configurada para intercambio directo"
