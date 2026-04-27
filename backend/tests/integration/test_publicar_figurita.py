"""
Tests de integración — Caso de uso: Publicar figurita para intercambio.

Cubre el endpoint POST /api/v1/figuritas/ verificando:
- Publicación exitosa con todos los campos requeridos
- Validaciones de campos (número, cantidad, tipo de intercambio)
- Persistencia: la figurita publicada aparece en la búsqueda
"""
import pytest


ENDPOINT_ALBUM = "/api/v1/album/"
ENDPOINT_PUBLICACIONES = "/api/v1/publicaciones/"

def agregar_y_publicar(client, token, numero, equipo, jugador, cantidad=1, tipo="intercambio_directo"):
    """Agrega al álbum y publica para intercambio. Retorna la respuesta del POST a publicaciones."""
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

class TestAgregarAlbum:

    def agregar_y_publicar(client, token, numero, equipo, jugador, cantidad, tipo):
        """
        Helper que ejecuta el flujo completo en dos pasos:
        1. Agrega la figurita al álbum.
        2. La publica para intercambio.
        Retorna la publicación creada.
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
            json={"figurita_personal_id": figurita_id, "tipo_intercambio": tipo, "cantidad_disponible": 1},
            headers={"X-User-Token": token},
        )
        return resp_pub

    def test_agregar_figurita_al_album_devuelve_201(self, client, token_user1):
            """Agregar una figurita al álbum devuelve 201 con los datos correctos."""
            resp = client.post(
                ENDPOINT_ALBUM,
                json={"numero": 10, "equipo": "Argentina", "jugador": "Messi", "cantidad": 2},
                headers={"X-User-Token": token_user1},
            )

            assert resp.status_code == 201
            data = resp.json()
            assert data["numero"] == 10
            assert data["equipo"] == "Argentina"
            assert data["jugador"] == "Messi"
            assert data["cantidad"] == 2
            assert "id" in data
            assert data["usuario_id"] is not None
            assert data["en_intercambio"] is False

    def test_numero_es_requerido(self, client, token_user1):
            """Omitir el número devuelve 422."""
            resp = client.post(
                ENDPOINT_ALBUM,
                json={"equipo": "Argentina", "jugador": "Messi", "cantidad": 1},
                headers={"X-User-Token": token_user1},
            )
            assert resp.status_code == 422

    def test_numero_no_puede_ser_cero(self, client, token_user1):
            """El número debe ser >= 1."""
            resp = client.post(
                ENDPOINT_ALBUM,
                json={"numero": 0, "equipo": "Argentina", "jugador": "Messi", "cantidad": 1},
                headers={"X-User-Token": token_user1},
            )
            assert resp.status_code == 422

    def test_cantidad_no_puede_ser_cero(self, client, token_user1):
            """La cantidad debe ser >= 1."""
            resp = client.post(
                ENDPOINT_ALBUM,
                json={"numero": 10, "equipo": "Argentina", "jugador": "Messi", "cantidad": 0},
                headers={"X-User-Token": token_user1},
            )
            assert resp.status_code == 422


class TestPublicarParaIntercambio:

    def test_publicar_con_intercambio_directo_devuelve_201(self, client, token_user1):
        """Publicar una figurita del álbum para intercambio directo devuelve 201."""
        resp = agregar_y_publicar(client, token_user1, 10, "Argentina", "Messi", 2, "intercambio_directo")

        assert resp.status_code == 201
        data = resp.json()
        assert data["numero"] == 10
        assert data["tipo_intercambio"] == "intercambio_directo"
        assert "id" in data

    def test_publicar_con_subasta_devuelve_201(self, client, token_user1):
        """Publicar para subasta devuelve 201."""
        resp = agregar_y_publicar(client, token_user1, 10, "Argentina", "Messi", 2, "subasta")

        assert resp.status_code == 201
        assert resp.json()["tipo_intercambio"] == "subasta"

    def test_no_se_puede_publicar_figurita_ajena(self, client, token_user1, token_user2):
        """No se puede publicar una figurita que pertenece a otro usuario."""
        resp_album = client.post(
            ENDPOINT_ALBUM,
            json={"numero": 10, "equipo": "Argentina", "jugador": "Messi", "cantidad": 1},
            headers={"X-User-Token": token_user1},
        )
        figurita_id = resp_album.json()["id"]

        resp = client.post(
            ENDPOINT_PUBLICACIONES,
            json={"figurita_personal_id": figurita_id, "tipo_intercambio": "intercambio_directo", "cantidad_disponible": 1},
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 403

    def test_no_se_puede_publicar_dos_veces_la_misma_figurita(self, client, token_user1):
        """Una figurita ya publicada no puede volver a publicarse sin retirar la oferta."""
        resp_album = client.post(
            ENDPOINT_ALBUM,
            json={"numero": 10, "equipo": "Argentina", "jugador": "Messi", "cantidad": 2},
            headers={"X-User-Token": token_user1},
        )
        figurita_id = resp_album.json()["id"]

        client.post(
            ENDPOINT_PUBLICACIONES,
            json={"figurita_personal_id": figurita_id, "tipo_intercambio": "intercambio_directo", "cantidad_disponible": 1},
            headers={"X-User-Token": token_user1},
        )
        resp = client.post(
            ENDPOINT_PUBLICACIONES,
            json={"figurita_personal_id": figurita_id, "tipo_intercambio": "subasta", "cantidad_disponible": 1},
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 409

    def test_cantidad_disponible_no_puede_superar_cantidad_en_album(self, client, token_user1):
        """No se puede ofrecer más figuritas de las que tenés en el álbum."""
        resp_album = client.post(
            ENDPOINT_ALBUM,
            json={"numero": 10, "equipo": "Argentina", "jugador": "Messi", "cantidad": 1},
            headers={"X-User-Token": token_user1},
        )
        figurita_id = resp_album.json()["id"]

        resp = client.post(
            ENDPOINT_PUBLICACIONES,
            json={"figurita_personal_id": figurita_id, "tipo_intercambio": "intercambio_directo", "cantidad_disponible": 5},
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 400

    def test_tipo_intercambio_invalido_devuelve_422(self, client, token_user1):
        """Un tipo de intercambio fuera del enum devuelve 422."""
        resp_album = client.post(
            ENDPOINT_ALBUM,
            json={"numero": 10, "equipo": "Argentina", "jugador": "Messi", "cantidad": 1},
            headers={"X-User-Token": token_user1},
        )
        figurita_id = resp_album.json()["id"]

        resp = client.post(
            ENDPOINT_PUBLICACIONES,
            json={"figurita_personal_id": figurita_id, "tipo_intercambio": "invalido", "cantidad_disponible": 1},
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 422