"""
Tests de integración — Caso de uso: Intercambios dirigidos.

Incluye cobertura de:
- Propuesta de intercambio y validaciones de negocio
- Respuesta del receptor (aceptar/rechazar)
- Cambio de posesión al aceptar
- Limpieza opcional de faltantes al aceptar
"""

ENDPOINT_FIGURITAS = "/api/v1/figuritas/"
ENDPOINT_FALTANTES = "/api/v1/usuarios/faltantes"
ENDPOINT_INTERCAMBIOS = "/api/v1/intercambios/"


# -------------------------
# Proponer intercambio
# -------------------------

class TestProponerIntercambio:

    def test_user1_publica_faltante_y_propone_intercambio_a_user2(self, client, token_user1, token_user2):
        """Flujo feliz: user1 propone a user2 y el intercambio queda pendiente."""
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

        resp_pub_user1 = client.post(ENDPOINT_FIGURITAS, json=figurita_user1, headers={"X-User-Token": token_user1})
        resp_pub_user2 = client.post(ENDPOINT_FIGURITAS, json=figurita_user2, headers={"X-User-Token": token_user2})

        assert resp_pub_user1.status_code == 201
        assert resp_pub_user2.status_code == 201

        resp_faltante = client.post(ENDPOINT_FALTANTES, json={"numero_figurita": 2}, headers={"X-User-Token": token_user1})

        assert resp_faltante.status_code == 201
        assert resp_faltante.json()["data"]["numero_figurita"] == 2
        assert resp_faltante.json()["data"]["usuario_id"] == 1

        propuesta = {
            "figurita_ofrecida_numero": 1,
            "figurita_solicitada_numero": 2,
            "solicitado_a_id": 2,
        }
        resp_intercambio = client.post(ENDPOINT_INTERCAMBIOS, json=propuesta, headers={"X-User-Token": token_user1})

        assert resp_intercambio.status_code == 200
        data = resp_intercambio.json()
        assert data["propuesto_por"] == 1
        assert data["solicitado_a"] == 2
        assert data["figurita_ofrecida"] == 1
        assert data["figurita_solicitada"] == 2
        assert data["estado"] == "pendiente"

    def test_no_permite_intercambiar_misma_figurita(self, client, token_user1, token_user2):
        """No se puede proponer intercambio usando el mismo número ofrecido y solicitado."""
        client.post(ENDPOINT_FIGURITAS, json={"numero": 1, "equipo": "Argentina", "jugador": "Jugador 1", "cantidad": 1, "tipo_intercambio": "intercambio_directo"}, headers={"X-User-Token": token_user1})
        client.post(ENDPOINT_FIGURITAS, json={"numero": 1, "equipo": "Brasil", "jugador": "Jugador 2", "cantidad": 1, "tipo_intercambio": "intercambio_directo"}, headers={"X-User-Token": token_user2})

        resp = client.post(ENDPOINT_INTERCAMBIOS, json={"figurita_ofrecida_numero": 1, "figurita_solicitada_numero": 1, "solicitado_a_id": 2}, headers={"X-User-Token": token_user1})

        assert resp.status_code == 400

    def test_no_permite_proponer_intercambio_a_si_mismo(self, client, token_user1):
        """No se puede proponer un intercambio al propio usuario."""
        client.post(ENDPOINT_FIGURITAS, json={"numero": 1, "equipo": "Argentina", "jugador": "Jugador 1", "cantidad": 1, "tipo_intercambio": "intercambio_directo"}, headers={"X-User-Token": token_user1})
        client.post(ENDPOINT_FIGURITAS, json={"numero": 2, "equipo": "Argentina", "jugador": "Jugador 2", "cantidad": 1, "tipo_intercambio": "intercambio_directo"}, headers={"X-User-Token": token_user1})

        resp = client.post(ENDPOINT_INTERCAMBIOS, json={"figurita_ofrecida_numero": 1, "figurita_solicitada_numero": 2, "solicitado_a_id": 1}, headers={"X-User-Token": token_user1})

        assert resp.status_code == 400

    def test_falla_si_usuario_no_tiene_publicada_la_figurita_ofrecida(self, client, token_user1, token_user2):
        """Si el proponente no posee la figurita ofrecida, devuelve 404."""
        client.post(ENDPOINT_FIGURITAS, json={"numero": 2, "equipo": "Brasil", "jugador": "Jugador 2", "cantidad": 1, "tipo_intercambio": "intercambio_directo"}, headers={"X-User-Token": token_user2})

        resp = client.post(ENDPOINT_INTERCAMBIOS, json={"figurita_ofrecida_numero": 99, "figurita_solicitada_numero": 2, "solicitado_a_id": 2}, headers={"X-User-Token": token_user1})

        assert resp.status_code == 404

    def test_falla_si_usuario_destino_no_tiene_publicada_figurita_solicitada(self, client, token_user1, token_user2):
        """Si el receptor no posee la figurita solicitada, devuelve 404."""
        client.post(ENDPOINT_FIGURITAS, json={"numero": 1, "equipo": "Argentina", "jugador": "Jugador 1", "cantidad": 1, "tipo_intercambio": "intercambio_directo"}, headers={"X-User-Token": token_user1})

        resp = client.post(ENDPOINT_INTERCAMBIOS, json={"figurita_ofrecida_numero": 1, "figurita_solicitada_numero": 2, "solicitado_a_id": 2}, headers={"X-User-Token": token_user1})

        assert resp.status_code == 404

    def test_falla_si_figurita_ofrecida_no_es_intercambio_directo(self, client, token_user1, token_user2):
        """La figurita ofrecida debe estar publicada para intercambio directo."""
        client.post(ENDPOINT_FIGURITAS, json={"numero": 1, "equipo": "Argentina", "jugador": "Jugador 1", "cantidad": 1, "tipo_intercambio": "subasta"}, headers={"X-User-Token": token_user1})
        client.post(ENDPOINT_FIGURITAS, json={"numero": 2, "equipo": "Brasil", "jugador": "Jugador 2", "cantidad": 1, "tipo_intercambio": "intercambio_directo"}, headers={"X-User-Token": token_user2})

        resp = client.post(ENDPOINT_INTERCAMBIOS, json={"figurita_ofrecida_numero": 1, "figurita_solicitada_numero": 2, "solicitado_a_id": 2}, headers={"X-User-Token": token_user1})

        assert resp.status_code == 400

    def test_falla_si_figurita_solicitada_no_es_intercambio_directo(self, client, token_user1, token_user2):
        """La figurita solicitada también debe estar publicada para intercambio directo."""
        client.post(ENDPOINT_FIGURITAS, json={"numero": 1, "equipo": "Argentina", "jugador": "Jugador 1", "cantidad": 1, "tipo_intercambio": "intercambio_directo"}, headers={"X-User-Token": token_user1})
        client.post(ENDPOINT_FIGURITAS, json={"numero": 2, "equipo": "Brasil", "jugador": "Jugador 2", "cantidad": 1, "tipo_intercambio": "subasta"}, headers={"X-User-Token": token_user2})

        resp = client.post(ENDPOINT_INTERCAMBIOS, json={"figurita_ofrecida_numero": 1, "figurita_solicitada_numero": 2, "solicitado_a_id": 2}, headers={"X-User-Token": token_user1})

        assert resp.status_code == 400


# -------------------------
# Responder intercambio
# -------------------------

class TestResponderIntercambio:

    def _crear_intercambio_pendiente(self, client, token_user1, token_user2) -> int:
        """Crea un intercambio base pendiente (user1 ofrece #1 por #2 de user2)."""
        client.post(ENDPOINT_FIGURITAS, json={"numero": 1, "equipo": "Argentina", "jugador": "Jugador 1", "cantidad": 1, "tipo_intercambio": "intercambio_directo"}, headers={"X-User-Token": token_user1})
        client.post(ENDPOINT_FIGURITAS, json={"numero": 2, "equipo": "Brasil", "jugador": "Jugador 2", "cantidad": 1, "tipo_intercambio": "intercambio_directo"}, headers={"X-User-Token": token_user2})

        resp = client.post(ENDPOINT_INTERCAMBIOS, json={"figurita_ofrecida_numero": 1, "figurita_solicitada_numero": 2, "solicitado_a_id": 2}, headers={"X-User-Token": token_user1})
        assert resp.status_code == 200
        return resp.json()["id"]

    def test_no_receptor_no_puede_responder_intercambio(self, client, token_user1, token_user2):
        """Un usuario que no es receptor debe obtener 403 al intentar responder."""
        intercambio_id = self._crear_intercambio_pendiente(client, token_user1, token_user2)

        resp = client.patch(f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/estado", json={"estado": "aceptado"}, headers={"X-User-Token": token_user1})

        assert resp.status_code == 403

    def test_no_permite_responder_dos_veces(self, client, token_user1, token_user2):
        """Una vez respondido, el intercambio no puede volver a responderse."""
        intercambio_id = self._crear_intercambio_pendiente(client, token_user1, token_user2)

        resp_1 = client.patch(f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/estado", json={"estado": "aceptado"}, headers={"X-User-Token": token_user2})
        assert resp_1.status_code == 200

        resp_2 = client.patch(f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/estado", json={"estado": "rechazado"}, headers={"X-User-Token": token_user2})

        assert resp_2.status_code == 400

    def test_aceptar_intercambio_cambia_posesion_de_figuritas(self, client, token_user1, token_user2):
        """Aceptar intercambio invierte la posesión de las figuritas involucradas."""
        intercambio_id = self._crear_intercambio_pendiente(client, token_user1, token_user2)

        resp = client.patch(f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/estado", json={"estado": "aceptado"}, headers={"X-User-Token": token_user2})

        assert resp.status_code == 200
        lista = client.get(ENDPOINT_FIGURITAS).json()["figuritasDisponibles"]
        figurita_1 = next(f for f in lista if f["numero"] == 1)
        figurita_2 = next(f for f in lista if f["numero"] == 2)
        assert figurita_1["usuario_id"] == 2
        assert figurita_2["usuario_id"] == 1

    def test_rechazar_intercambio_no_cambia_posesion(self, client, token_user1, token_user2):
        """Rechazar intercambio mantiene la posesión original de ambas figuritas."""
        intercambio_id = self._crear_intercambio_pendiente(client, token_user1, token_user2)

        resp = client.patch(f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/estado", json={"estado": "rechazado"}, headers={"X-User-Token": token_user2})

        assert resp.status_code == 200
        lista = client.get(ENDPOINT_FIGURITAS).json()["figuritasDisponibles"]
        figurita_1 = next(f for f in lista if f["numero"] == 1)
        figurita_2 = next(f for f in lista if f["numero"] == 2)
        assert figurita_1["usuario_id"] == 1
        assert figurita_2["usuario_id"] == 2

    def test_si_hay_faltante_registrado_se_elimina_al_aceptar(self, client, token_user1, token_user2):
        """Si la figurita recibida estaba como faltante, se elimina al aceptar."""
        intercambio_id = self._crear_intercambio_pendiente(client, token_user1, token_user2)

        resp_faltante = client.post(ENDPOINT_FALTANTES, json={"numero_figurita": 1}, headers={"X-User-Token": token_user2})
        assert resp_faltante.status_code == 201

        resp = client.patch(f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/estado", json={"estado": "aceptado"}, headers={"X-User-Token": token_user2})
        assert resp.status_code == 200

        faltantes_user2 = client.get(ENDPOINT_FALTANTES, headers={"X-User-Token": token_user2}).json()["faltantes"]
        numeros = [f["numero_figurita"] for f in faltantes_user2]
        assert 1 not in numeros
