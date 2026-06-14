"""
Tests de integración — Casos de uso: Subastas.

Cobertura:
- Crear una subasta a partir de una figurita publicada con tipo 'subasta'
- Ofertar en una subasta activa y consultar historial de ofertas
"""

import datetime as dt

ENDPOINT_ALBUM        = "/api/v1/album/"
ENDPOINT_PUBLICACIONES = "/api/v1/publicaciones/"
ENDPOINT_SUBASTAS     = "/api/v1/subastas/"


# ───────
# Helpers
# ───────

def agregar_y_publicar(client, token, numero, equipo, jugador, cantidad=2, tipo="subasta"):
    """
    Agrega una figurita al álbum y la publica para intercambio.
    Retorna (pub_id, album_id): pub_id para crear subastas, album_id para ofertas.
    """
    resp_album = client.post(
        ENDPOINT_ALBUM,
        json={"numero": numero, "equipo": equipo, "jugador": jugador, "cantidad": cantidad},
        headers={"Authorization": token},
    )
    assert resp_album.status_code == 201
    album_id = resp_album.json()["id"]

    resp_pub = client.post(
        ENDPOINT_PUBLICACIONES,
        json={
            "figurita_personal_id": album_id,
            "tipo_intercambio": tipo,
            "cantidad_disponible": 1,
        },
        headers={"Authorization": token},
    )
    assert resp_pub.status_code == 201
    return resp_pub.json()["id"], album_id


def _payload_subasta(publicacion_id, horas=1):
    ahora = dt.datetime.now(dt.timezone.utc)
    return {
        "figurita_id": publicacion_id,
        "inicio": (ahora - dt.timedelta(minutes=5)).isoformat(),
        "fin": (ahora + dt.timedelta(hours=horas)).isoformat(),
    }


def _crear_subasta(client, token, publicacion_id):
    return client.post(
        ENDPOINT_SUBASTAS,
        json=_payload_subasta(publicacion_id),
        headers={"Authorization": token},
    )


# ────────────────────────────
# Crear subasta
# ────────────────────────────

class TestCrearSubasta:

    def test_flujo_feliz(self, client, token_user1):
        """Una publicación con tipo 'subasta' puede ponerse en subasta correctamente."""
        pub_id, _ = agregar_y_publicar(client, token_user1, 10, "Argentina", "Messi", tipo="subasta")
        resp = _crear_subasta(client, token_user1, pub_id)

        assert resp.status_code == 201
        data = resp.json()
        assert data["figurita_id"] == pub_id
        assert data["usuario_id"] == 1

    def test_figurita_tipo_intercambio_directo_falla(self, client, token_user1):
        """Una publicación con tipo 'intercambio_directo' no puede ponerse en subasta."""
        pub_id, _ = agregar_y_publicar(client, token_user1, 10, "Argentina", "Messi", tipo="intercambio_directo")
        resp = _crear_subasta(client, token_user1, pub_id)

        assert resp.status_code == 400

    def test_figurita_inexistente_falla(self, client, token_user1):
        """Intentar subastar una publicación que no existe devuelve 404."""
        resp = _crear_subasta(client, token_user1, publicacion_id="000000000000000000000000")

        assert resp.status_code == 404

    def test_figurita_de_otro_usuario_falla(self, client, token_user1, token_user2):
        """No se puede subastar una publicación que pertenece a otro usuario."""
        pub_id, _ = agregar_y_publicar(client, token_user2, 10, "Argentina", "Messi", tipo="subasta")
        resp = _crear_subasta(client, token_user1, pub_id)

        assert resp.status_code == 403

    def test_figurita_ya_en_subasta_falla(self, client, token_user1):
        """No se puede crear una segunda subasta para la misma publicación."""
        pub_id, _ = agregar_y_publicar(client, token_user1, 10, "Argentina", "Messi", tipo="subasta")
        _crear_subasta(client, token_user1, pub_id)

        resp = _crear_subasta(client, token_user1, pub_id)

        assert resp.status_code == 409

    def test_listar_subastas_activas(self, client, token_user1):
        """La subasta creada aparece en el listado de subastas activas."""
        pub_id, _ = agregar_y_publicar(client, token_user1, 10, "Argentina", "Messi", tipo="subasta")
        _crear_subasta(client, token_user1, pub_id)

        resp = client.get(ENDPOINT_SUBASTAS, headers={"Authorization": token_user1})

        assert resp.status_code == 200
        subastas = resp.json()
        assert any(s["figurita_id"] == pub_id for s in subastas)


# ─────────────────────────
# Ofertar en subasta activa
# ─────────────────────────

class TestOfertarEnSubasta:

    def _setup_subasta(self, client, token_user1) -> int:
        """
        Publica una figurita como subasta y la pone en subasta.
        Devuelve el subasta_id.
        """
        pub_id, _ = agregar_y_publicar(client, token_user1, 10, "Argentina", "Messi", tipo="subasta")
        resp = _crear_subasta(client, token_user1, pub_id)
        return resp.json()["id"]

    def test_flujo_feliz(self, client, token_user1, token_user2):
        """User2 oferta en la subasta de user1 con su propia figurita del álbum."""
        subasta_id = self._setup_subasta(client, token_user1)
        _, album_user2 = agregar_y_publicar(
            client, token_user2, 7, "Brasil", "Vinicius", tipo="intercambio_directo"
        )

        resp = client.post(
            f"{ENDPOINT_SUBASTAS}{subasta_id}/ofertas",
            json={"figuritas_ofrecidas": [album_user2]},
            headers={"Authorization": token_user2},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["subasta_id"] == subasta_id
        assert data["usuario_id"] == 2

    def test_no_se_puede_ofertar_en_subasta_propia(self, client, token_user1):
        """El dueño de la subasta no puede ofertar en ella."""
        subasta_id = self._setup_subasta(client, token_user1)
        _, album_extra = agregar_y_publicar(
            client, token_user1, 99, "Uruguay", "Extra", tipo="intercambio_directo"
        )

        resp = client.post(
            f"{ENDPOINT_SUBASTAS}{subasta_id}/ofertas",
            json={"figuritas_ofrecidas": [album_extra]},
            headers={"Authorization": token_user1},
        )

        assert resp.status_code == 403

    def test_subasta_inexistente_devuelve_404(self, client, token_user2):
        """Ofertar en una subasta que no existe devuelve 404."""
        _, album_user2 = agregar_y_publicar(
            client, token_user2, 7, "Brasil", "Vinicius", tipo="intercambio_directo"
        )

        resp = client.post(
            f"{ENDPOINT_SUBASTAS}000000000000000000000000/ofertas",
            json={"figuritas_ofrecidas": [album_user2]},
            headers={"Authorization": token_user2},
        )

        assert resp.status_code == 404

    def test_ofertar_sin_figuritas_falla(self, client, token_user1, token_user2):
        """Enviar lista vacía de figuritas devuelve 400."""
        subasta_id = self._setup_subasta(client, token_user1)

        resp = client.post(
            f"{ENDPOINT_SUBASTAS}{subasta_id}/ofertas",
            json={"figuritas_ofrecidas": []},
            headers={"Authorization": token_user2},
        )

        assert resp.status_code == 400

    def test_ofertar_con_figurita_inexistente_falla(self, client, token_user1, token_user2):
        """Ofrecer un ID de publicación que no existe devuelve 404."""
        subasta_id = self._setup_subasta(client, token_user1)

        resp = client.post(
            f"{ENDPOINT_SUBASTAS}{subasta_id}/ofertas",
            json={"figuritas_ofrecidas": ["000000000000000000000000"]},
            headers={"Authorization": token_user2},
        )

        assert resp.status_code == 404

    def test_ofertar_con_figurita_ajena_falla(self, client, token_user1, token_user2):
        """No se puede ofrecer una figurita del álbum que pertenece a otro usuario."""
        pub_user1, _ = agregar_y_publicar(client, token_user1, 10, "Argentina", "Messi", tipo="subasta")
        subasta_id = _crear_subasta(client, token_user1, pub_user1).json()["id"]
        _, album_user1_extra = agregar_y_publicar(
            client, token_user1, 99, "Uruguay", "Extra", tipo="intercambio_directo"
        )

        resp = client.post(
            f"{ENDPOINT_SUBASTAS}{subasta_id}/ofertas",
            json={"figuritas_ofrecidas": [album_user1_extra]},
            headers={"Authorization": token_user2},
        )

        assert resp.status_code == 403



# ────────────────────
# Historial de ofertas
# ────────────────────

class TestHistorialOfertas:

    def test_subasta_sin_ofertas_devuelve_lista_vacia(self, client, token_user1):
        """Una subasta recién creada no tiene ofertas."""
        pub_id, _ = agregar_y_publicar(client, token_user1, 10, "Argentina", "Messi", tipo="subasta")
        subasta_id = _crear_subasta(client, token_user1, pub_id).json()["id"]

        resp = client.get(f"{ENDPOINT_SUBASTAS}{subasta_id}/ofertas", headers={"Authorization": token_user1})

        assert resp.status_code == 200
        assert resp.json() == []

    def test_historial_refleja_oferta_realizada(self, client, token_user1, token_user2):
        """Tras ofertar, el historial contiene la oferta con los datos correctos."""
        pub_id, _ = agregar_y_publicar(client, token_user1, 10, "Argentina", "Messi", tipo="subasta")
        subasta_id = _crear_subasta(client, token_user1, pub_id).json()["id"]
        _, album_user2 = agregar_y_publicar(
            client, token_user2, 7, "Brasil", "Vinicius", tipo="intercambio_directo"
        )

        client.post(
            f"{ENDPOINT_SUBASTAS}{subasta_id}/ofertas",
            json={"figuritas_ofrecidas": [album_user2]},
            headers={"Authorization": token_user2},
        )

        resp = client.get(f"{ENDPOINT_SUBASTAS}{subasta_id}/ofertas", headers={"Authorization": token_user1})

        assert resp.status_code == 200
        ofertas = resp.json()
        assert len(ofertas) == 1
        assert ofertas[0]["subasta_id"] == subasta_id
        assert ofertas[0]["usuario_id"] == 2
        assert album_user2 in ofertas[0]["ofrecidas"]

    def test_subasta_inexistente_devuelve_404(self, client, token_user1):
        """Consultar historial de una subasta inexistente devuelve 404."""
        resp = client.get(f"{ENDPOINT_SUBASTAS}000000000000000000000000/ofertas", headers={"Authorization": token_user1})

        assert resp.status_code == 404
