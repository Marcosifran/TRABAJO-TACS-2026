"""
Tests de integración — Caso de uso: Intercambios dirigidos.

Incluye cobertura de:
- Propuesta de intercambio y validaciones de negocio
- Respuesta del receptor (aceptar/rechazar)
- Cambio de posesión al aceptar
- Limpieza de faltantes al aceptar
"""

import pytest

ENDPOINT_ALBUM         = "/api/v1/album/"
ENDPOINT_PUBLICACIONES = "/api/v1/publicaciones/"
ENDPOINT_FALTANTES     = "/api/v1/usuarios/faltantes"
ENDPOINT_INTERCAMBIOS  = "/api/v1/intercambios/"


def agregar_y_publicar(client, token, numero, equipo, jugador, cantidad=1, tipo="intercambio_directo"):
    """
    Agrega una figurita al álbum y la publica para intercambio.
    Por defecto el tipo es intercambio_directo.
    Retorna el id de la publicación creada.
    """
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
            "cantidad_disponible": cantidad,
        },
        headers={"X-User-Token": token},
    )
    assert resp_pub.status_code == 201
    return resp_pub.json()["id"]


# -------------------------
# Proponer intercambio
# -------------------------

class TestProponerIntercambio:

    def test_flujo_feliz_user1_propone_a_user2(self, client, token_user1, token_user2):
        """
        Flujo completo: ambos usuarios tienen sus figuritas publicadas
        para intercambio directo. user1 propone intercambiar su #1 por el #2 de user2.
        El intercambio queda en estado pendiente.
        """
        agregar_y_publicar(client, token_user1, 1, "Argentina", "Jugador 1")
        agregar_y_publicar(client, token_user2, 2, "Brasil",    "Jugador 2")

        propuesta = {
            "figuritas_ofrecidas_numero": [1],
            "figurita_solicitada_numero": 2,
            "solicitado_a_id": 2,
        }
        resp = client.post(
            ENDPOINT_INTERCAMBIOS,
            json=propuesta,
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["propuesto_por"] == 1
        assert data["solicitado_a"] == 2
        assert data["figuritas_ofrecidas"] == [1]
        assert data["figurita_solicitada"] == 2
        assert data["estado"] == "pendiente"

    def test_permite_ofrecer_multiples_figuritas_por_una(self, client, token_user1, token_user2):
        """El proponente puede ofrecer varias figuritas y pedir una sola."""
        agregar_y_publicar(client, token_user1, 1, "Argentina", "Jugador 1")
        agregar_y_publicar(client, token_user1, 3, "Uruguay",   "Jugador 3")
        agregar_y_publicar(client, token_user2, 2, "Brasil",    "Jugador 2")

        resp = client.post(
            ENDPOINT_INTERCAMBIOS,
            json={
                "figuritas_ofrecidas_numero": [1, 3],
                "figurita_solicitada_numero": 2,
                "solicitado_a_id": 2,
            },
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["figuritas_ofrecidas"] == [1, 3]
        assert data["figurita_solicitada"] == 2

    def test_no_permite_proponer_a_si_mismo(self, client, token_user1):
        """No se puede proponer un intercambio al propio usuario."""
        agregar_y_publicar(client, token_user1, 1, "Argentina", "Jugador 1")
        agregar_y_publicar(client, token_user1, 2, "Argentina", "Jugador 2")

        resp = client.post(
            ENDPOINT_INTERCAMBIOS,
            json={
                "figuritas_ofrecidas_numero": [1],
                "figurita_solicitada_numero": 2,
                "solicitado_a_id": 1,
            },
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 400

    def test_no_permite_intercambiar_mismo_numero(self, client, token_user1, token_user2):
        """No se puede ofrecer y solicitar el mismo número de figurita."""
        agregar_y_publicar(client, token_user1, 1, "Argentina", "Jugador 1")
        agregar_y_publicar(client, token_user2, 1, "Brasil",    "Jugador 2")

        resp = client.post(
            ENDPOINT_INTERCAMBIOS,
            json={
                "figuritas_ofrecidas_numero": [1],
                "figurita_solicitada_numero": 1,
                "solicitado_a_id": 2,
            },
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 400

    def test_falla_si_proponente_no_tiene_figurita_publicada(self, client, token_user1, token_user2):
        """
        Si el proponente no tiene la figurita publicada para intercambio directo,
        devuelve 404.
        """
        agregar_y_publicar(client, token_user2, 2, "Brasil", "Jugador 2")

        resp = client.post(
            ENDPOINT_INTERCAMBIOS,
            json={
                "figuritas_ofrecidas_numero": [99],
                "figurita_solicitada_numero": 2,
                "solicitado_a_id": 2,
            },
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 404

    def test_falla_si_receptor_no_tiene_figurita_publicada(self, client, token_user1, token_user2):
        """
        Si el receptor no tiene la figurita solicitada publicada para intercambio directo,
        devuelve 404.
        """
        agregar_y_publicar(client, token_user1, 1, "Argentina", "Jugador 1")

        resp = client.post(
            ENDPOINT_INTERCAMBIOS,
            json={
                "figuritas_ofrecidas_numero": [1],
                "figurita_solicitada_numero": 99,
                "solicitado_a_id": 2,
            },
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 404

    def test_falla_si_figurita_ofrecida_es_subasta(self, client, token_user1, token_user2):
        """
        Si la figurita ofrecida está publicada como subasta en vez de
        intercambio_directo, no puede usarse en un intercambio directo.
        """
        agregar_y_publicar(client, token_user1, 1, "Argentina", "Jugador 1", tipo="subasta")
        agregar_y_publicar(client, token_user2, 2, "Brasil",    "Jugador 2")

        resp = client.post(
            ENDPOINT_INTERCAMBIOS,
            json={
                "figuritas_ofrecidas_numero": [1],
                "figurita_solicitada_numero": 2,
                "solicitado_a_id": 2,
            },
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 404

    def test_falla_si_figurita_solicitada_es_subasta(self, client, token_user1, token_user2):
        """
        Si la figurita solicitada está publicada como subasta,
        no puede pedirse en un intercambio directo.
        """
        agregar_y_publicar(client, token_user1, 1, "Argentina", "Jugador 1")
        agregar_y_publicar(client, token_user2, 2, "Brasil",    "Jugador 2", tipo="subasta")

        resp = client.post(
            ENDPOINT_INTERCAMBIOS,
            json={
                "figuritas_ofrecidas_numero": [1],
                "figurita_solicitada_numero": 2,
                "solicitado_a_id": 2,
            },
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 404

    def test_falla_si_lista_ofrecidas_esta_vacia(self, client, token_user1, token_user2):
        """La propuesta debe incluir al menos una figurita ofrecida."""
        agregar_y_publicar(client, token_user2, 2, "Brasil", "Jugador 2")

        resp = client.post(
            ENDPOINT_INTERCAMBIOS,
            json={
                "figuritas_ofrecidas_numero": [],
                "figurita_solicitada_numero": 2,
                "solicitado_a_id": 2,
            },
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 400

    def test_falla_si_usuario_destino_no_existe(self, client, token_user1):
        """No se puede proponer un intercambio a un usuario que no existe."""
        agregar_y_publicar(client, token_user1, 1, "Argentina", "Jugador 1")

        resp = client.post(
            ENDPOINT_INTERCAMBIOS,
            json={
                "figuritas_ofrecidas_numero": [1],
                "figurita_solicitada_numero": 99,
                "solicitado_a_id": 999,
            },
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 404


# -------------------------
# Responder intercambio
# -------------------------

class TestResponderIntercambio:

    def _crear_intercambio_pendiente(self, client, token_user1, token_user2) -> int:
        """
        Helper interno: crea un intercambio pendiente base.
        user1 publica #1 para intercambio directo.
        user2 publica #2 para intercambio directo.
        user1 propone intercambiar su #1 por el #2 de user2.
        Retorna el id del intercambio creado.
        """
        agregar_y_publicar(client, token_user1, 1, "Argentina", "Jugador 1")
        agregar_y_publicar(client, token_user2, 2, "Brasil",    "Jugador 2")

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
        return resp.json()["id"]

    def test_proponente_no_puede_responder_su_propio_intercambio(
        self, client, token_user1, token_user2
    ):
        """El usuario que propuso el intercambio no puede aceptarlo ni rechazarlo."""
        intercambio_id = self._crear_intercambio_pendiente(client, token_user1, token_user2)

        resp = client.patch(
            f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/estado",
            json={"estado": "aceptado"},
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 403

    def test_no_permite_responder_dos_veces(self, client, token_user1, token_user2):
        """Una vez respondido, el intercambio no puede volver a responderse."""
        intercambio_id = self._crear_intercambio_pendiente(client, token_user1, token_user2)

        resp_1 = client.patch(
            f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/estado",
            json={"estado": "aceptado"},
            headers={"X-User-Token": token_user2},
        )
        assert resp_1.status_code == 200

        resp_2 = client.patch(
            f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/estado",
            json={"estado": "rechazado"},
            headers={"X-User-Token": token_user2},
        )

        assert resp_2.status_code == 400

    def test_aceptar_cambia_posesion_en_album(self, client, token_user1, token_user2):
        """
        Al aceptar, las figuritas cambian de dueño en el álbum.
        user1 tenía #1 y user2 tenía #2.
        Después: user1 tiene #2 y user2 tiene #1.
        """
        intercambio_id = self._crear_intercambio_pendiente(client, token_user1, token_user2)

        client.patch(
            f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/estado",
            json={"estado": "aceptado"},
            headers={"X-User-Token": token_user2},
        )

        album_user1 = client.get(
            "/api/v1/usuarios/figuritas",
            headers={"X-User-Token": token_user1},
        ).json()["figuritas"]

        album_user2 = client.get(
            "/api/v1/usuarios/figuritas",
            headers={"X-User-Token": token_user2},
        ).json()["figuritas"]

        numeros_user1 = [f["numero"] for f in album_user1]
        numeros_user2 = [f["numero"] for f in album_user2]

        assert 2 in numeros_user1
        assert 1 not in numeros_user1
        assert 1 in numeros_user2
        assert 2 not in numeros_user2

    def test_rechazar_no_cambia_posesion(self, client, token_user1, token_user2):
        """Rechazar mantiene la posesión original de ambas figuritas."""
        intercambio_id = self._crear_intercambio_pendiente(client, token_user1, token_user2)

        client.patch(
            f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/estado",
            json={"estado": "rechazado"},
            headers={"X-User-Token": token_user2},
        )

        album_user1 = client.get(
            "/api/v1/usuarios/figuritas",
            headers={"X-User-Token": token_user1},
        ).json()["figuritas"]

        album_user2 = client.get(
            "/api/v1/usuarios/figuritas",
            headers={"X-User-Token": token_user2},
        ).json()["figuritas"]

        numeros_user1 = [f["numero"] for f in album_user1]
        numeros_user2 = [f["numero"] for f in album_user2]

        assert 1 in numeros_user1
        assert 2 in numeros_user2

    def test_faltante_se_elimina_al_aceptar(self, client, token_user1, token_user2):
        """
        Si la figurita recibida estaba registrada como faltante,
        se elimina automáticamente al aceptar el intercambio.
        user2 recibe #1 y la tenía como faltante — debe desaparecer de su lista.
        """
        intercambio_id = self._crear_intercambio_pendiente(client, token_user1, token_user2)

        client.post(
            ENDPOINT_FALTANTES,
            json={"numero_figurita": 1},
            headers={"X-User-Token": token_user2},
        )

        client.patch(
            f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/estado",
            json={"estado": "aceptado"},
            headers={"X-User-Token": token_user2},
        )

        faltantes_user2 = client.get(
            ENDPOINT_FALTANTES,
            headers={"X-User-Token": token_user2},
        ).json()["faltantes"]

        numeros = [f["numero_figurita"] for f in faltantes_user2]
        assert 1 not in numeros