"""
Tests de integración — Casos de uso: Subastas.

Cobertura:
- Publicar una figurita en subasta con sus validaciones
- Ofertar en una subasta activa y consultar historial de ofertas
"""

import datetime as dt

ENDPOINT_FIGURITAS = "/api/v1/figuritas/"
ENDPOINT_SUBASTAS  = "/api/v1/subastas/"

# ───────
# Helpers
# ───────

def _publicar_figurita(client, token, tipo="subasta", numero=10, jugador="Messi"):
    payload = {
        "numero": numero,
        "equipo": "Argentina",
        "jugador": jugador,
        "cantidad": 2,
        "tipo_intercambio": tipo,
    }
    resp = client.post(ENDPOINT_FIGURITAS, json=payload, headers={"X-User-Token": token})
    assert resp.status_code == 201
    return resp.json()["data"]["id"]

def _payload_subasta(figurita_id, horas=1):
    ahora = dt.datetime.now()
    return {
        "figurita_id": figurita_id,
        "inicio": ahora.isoformat(),
        "fin": (ahora + dt.timedelta(hours=horas)).isoformat(),
    }

def _crear_subasta(client, token, figurita_id):
    return client.post(
        ENDPOINT_SUBASTAS,
        json=_payload_subasta(figurita_id),
        headers={"X-User-Token": token},
    )


# ────────────────────────────
# Publicar figurita en subasta
# ────────────────────────────

class TestCrearSubasta:

    def test_flujo_feliz(self, client, token_user1):
        """Figurita con tipo 'subasta' puede ponerse en subasta correctamente."""
        figurita_id = _publicar_figurita(client, token_user1, tipo="subasta")
        resp = _crear_subasta(client, token_user1, figurita_id)

        assert resp.status_code == 201
        data = resp.json()
        assert "subasta" in data
        assert data["subasta"]["figurita_id"] == figurita_id
        assert data["subasta"]["usuario_id"] == 1

    def test_figurita_tipo_intercambio_directo_falla(self, client, token_user1):
        """Figurita con tipo 'intercambio_directo' no puede ponerse en subasta."""
        figurita_id = _publicar_figurita(client, token_user1, tipo="intercambio_directo")
        resp = _crear_subasta(client, token_user1, figurita_id)

        assert resp.status_code == 400

    def test_figurita_inexistente_falla(self, client, token_user1):
        """Intentar subastar una figurita que no existe devuelve 400."""
        resp = _crear_subasta(client, token_user1, figurita_id=999)

        assert resp.status_code == 400

    def test_figurita_de_otro_usuario_falla(self, client, token_user1, token_user2):
        """No se puede subastar una figurita que pertenece a otro usuario."""
        figurita_id = _publicar_figurita(client, token_user2, tipo="subasta")
        resp = _crear_subasta(client, token_user1, figurita_id)

        assert resp.status_code == 400

    def test_figurita_ya_en_subasta_falla(self, client, token_user1):
        """No se puede crear una segunda subasta para la misma figurita."""
        figurita_id = _publicar_figurita(client, token_user1, tipo="subasta")
        _crear_subasta(client, token_user1, figurita_id)

        resp = _crear_subasta(client, token_user1, figurita_id)

        assert resp.status_code == 400

    def test_listar_subastas_activas(self, client, token_user1):
        """La subasta creada aparece en el listado de subastas activas."""
        figurita_id = _publicar_figurita(client, token_user1, tipo="subasta")
        _crear_subasta(client, token_user1, figurita_id)

        resp = client.get(ENDPOINT_SUBASTAS)

        assert resp.status_code == 200
        subastas = resp.json()["subastas"]
        assert any(s["figurita_id"] == figurita_id for s in subastas)


# ─────────────────────────
# Ofertar en subasta activa
# ─────────────────────────

class TestOfertarEnSubasta:

    def _setup_subasta(self, client, token_user1):
        """Publica una figurita y crea una subasta para user1. Devuelve subasta_id."""
        figurita_id = _publicar_figurita(client, token_user1, tipo="subasta")
        resp = _crear_subasta(client, token_user1, figurita_id)
        return resp.json()["subasta"]["id"]

    def test_flujo_feliz(self, client, token_user1, token_user2):
        """User2 oferta en la subasta de user1 con su propia figurita."""
        subasta_id = self._setup_subasta(client, token_user1)
        figurita_user2 = _publicar_figurita(client, token_user2, tipo="intercambio_directo", numero=7, jugador="Vinicius")

        resp = client.post(
            f"{ENDPOINT_SUBASTAS}{subasta_id}/ofertar",
            json={"figuritas_ofrecidas": [figurita_user2]},
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["mensaje"] == "Oferta realizada"
        assert data["oferta"]["subasta_id"] == subasta_id
        assert data["oferta"]["usuario_id"] == 2

    def test_no_se_puede_ofertar_en_subasta_propia(self, client, token_user1):
        """El dueño de la subasta no puede ofertar en ella."""
        subasta_id = self._setup_subasta(client, token_user1)
        figurita_extra = _publicar_figurita(client, token_user1, tipo="subasta", numero=99, jugador="Extra")

        resp = client.post(
            f"{ENDPOINT_SUBASTAS}{subasta_id}/ofertar",
            json={"figuritas_ofrecidas": [figurita_extra]},
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 400

    def test_subasta_inexistente_devuelve_404(self, client, token_user2):
        """Ofertar en una subasta que no existe devuelve 404."""
        figurita_id = _publicar_figurita(client, token_user2, tipo="intercambio_directo", numero=7, jugador="Vinicius")

        resp = client.post(
            f"{ENDPOINT_SUBASTAS}999/ofertar",
            json={"figuritas_ofrecidas": [figurita_id]},
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 404

    def test_ofertar_sin_figuritas_falla(self, client, token_user1, token_user2):
        """Enviar lista vacía de figuritas devuelve 400."""
        subasta_id = self._setup_subasta(client, token_user1)

        resp = client.post(
            f"{ENDPOINT_SUBASTAS}{subasta_id}/ofertar",
            json={"figuritas_ofrecidas": []},
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 400

    def test_ofertar_con_figurita_inexistente_falla(self, client, token_user1, token_user2):
        """Ofrecer un ID de figurita que no existe devuelve 404."""
        subasta_id = self._setup_subasta(client, token_user1)

        resp = client.post(
            f"{ENDPOINT_SUBASTAS}{subasta_id}/ofertar",
            json={"figuritas_ofrecidas": [9999]},
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 404

    def test_ofertar_con_figurita_ajena_falla(self, client, token_user1, token_user2):
        """No se puede ofrecer una figurita que pertenece a otro usuario."""
        figurita_user1 = _publicar_figurita(client, token_user1, tipo="subasta")
        subasta_id = _crear_subasta(client, token_user1, figurita_user1).json()["subasta"]["id"]
        figurita_user1_extra = _publicar_figurita(client, token_user1, tipo="intercambio_directo", numero=99, jugador="Extra")

        resp = client.post(
            f"{ENDPOINT_SUBASTAS}{subasta_id}/ofertar",
            json={"figuritas_ofrecidas": [figurita_user1_extra]},
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 400


# ────────────────────
# Historial de ofertas
# ────────────────────

class TestHistorialOfertas:

    def test_subasta_sin_ofertas_devuelve_lista_vacia(self, client, token_user1):
        """Una subasta recién creada no tiene ofertas."""
        figurita_id = _publicar_figurita(client, token_user1, tipo="subasta")
        subasta_id = _crear_subasta(client, token_user1, figurita_id).json()["subasta"]["id"]

        resp = client.get(f"{ENDPOINT_SUBASTAS}{subasta_id}/ofertas")

        assert resp.status_code == 200
        assert resp.json()["ofertas"] == []

    def test_historial_refleja_oferta_realizada(self, client, token_user1, token_user2):
        """Tras ofertar, el historial contiene la oferta con los datos correctos."""
        figurita_id = _publicar_figurita(client, token_user1, tipo="subasta")
        subasta_id = _crear_subasta(client, token_user1, figurita_id).json()["subasta"]["id"]
        figurita_user2 = _publicar_figurita(client, token_user2, tipo="intercambio_directo", numero=7, jugador="Vinicius")

        client.post(
            f"{ENDPOINT_SUBASTAS}{subasta_id}/ofertar",
            json={"figuritas_ofrecidas": [figurita_user2]},
            headers={"X-User-Token": token_user2},
        )

        resp = client.get(f"{ENDPOINT_SUBASTAS}{subasta_id}/ofertas")

        assert resp.status_code == 200
        ofertas = resp.json()["ofertas"]
        assert len(ofertas) == 1
        assert ofertas[0]["subasta_id"] == subasta_id
        assert ofertas[0]["usuario_id"] == 2
        assert figurita_user2 in ofertas[0]["ofrecidas"]

    def test_subasta_inexistente_devuelve_404(self, client):
        """Consultar historial de una subasta inexistente devuelve 404."""
        resp = client.get(f"{ENDPOINT_SUBASTAS}999/ofertas")

        assert resp.status_code == 404
