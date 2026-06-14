"""
Tests de integración — Caso de uso: Chat para Intercambios.
"""

import pytest
from app.repositories import usuario_repo
from app.security import create_access_token

ENDPOINT_ALBUM         = "/api/v1/album/"
ENDPOINT_PUBLICACIONES = "/api/v1/publicaciones/"
ENDPOINT_INTERCAMBIOS  = "/api/v1/intercambios/"


@pytest.fixture
def token_user3():
    """Header Authorization (JWT) de un tercer usuario que no participa en el intercambio."""
    user3 = {"id": 3, "nombre": "pepe", "email": "pepe@utn", "es_admin": False}
    usuario_repo._db_usuarios.append(user3)
    yield f"Bearer {create_access_token(subject=3, email='pepe@utn')}"
    usuario_repo._db_usuarios.remove(user3)


def agregar_y_publicar(client, token, numero, equipo, jugador, cantidad=1, tipo="intercambio_directo"):
    """Agrega una figurita al álbum y la publica para intercambio."""
    resp_album = client.post(
        ENDPOINT_ALBUM,
        json={"numero": numero, "equipo": equipo, "jugador": jugador, "cantidad": cantidad},
        headers={"Authorization": token},
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
        headers={"Authorization": token},
    )
    assert resp_pub.status_code == 201
    return resp_pub.json()["id"]


def crear_intercambio_pendiente(client, token_user1, token_user2) -> str:
    """Helper para crear un intercambio pendiente entre user1 y user2."""
    agregar_y_publicar(client, token_user1, 1, "Argentina", "Jugador 1")
    agregar_y_publicar(client, token_user2, 2, "Brasil",    "Jugador 2")

    resp = client.post(
        ENDPOINT_INTERCAMBIOS,
        json={
            "figuritas_ofrecidas_numero": [1],
            "figurita_solicitada_numero": 2,
            "solicitado_a_id": 2,
        },
        headers={"Authorization": token_user1},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


class TestChatIntercambio:

    def test_enviar_y_obtener_mensajes_exitosamente(self, client, token_user1, token_user2):
        """Los participantes de un intercambio pueden chatear entre sí."""
        intercambio_id = crear_intercambio_pendiente(client, token_user1, token_user2)

        # 1. User1 envía un mensaje
        resp_send_1 = client.post(
            f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/mensajes",
            json={"contenido": "Hola, ¿cuándo nos juntamos?"},
            headers={"Authorization": token_user1}
        )
        assert resp_send_1.status_code == 201
        msg1 = resp_send_1.json()
        assert msg1["intercambio_id"] == intercambio_id
        assert msg1["remitente_id"] == 1
        assert msg1["contenido"] == "Hola, ¿cuándo nos juntamos?"
        assert "fecha_envio" in msg1

        # 2. User2 responde
        resp_send_2 = client.post(
            f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/mensajes",
            json={"contenido": "Hola! A la tarde en el campus."},
            headers={"Authorization": token_user2}
        )
        assert resp_send_2.status_code == 201
        msg2 = resp_send_2.json()
        assert msg2["intercambio_id"] == intercambio_id
        assert msg2["remitente_id"] == 2
        assert msg2["contenido"] == "Hola! A la tarde en el campus."

        # 3. User1 lee el chat
        resp_get_1 = client.get(
            f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/mensajes",
            headers={"Authorization": token_user1}
        )
        assert resp_get_1.status_code == 200
        mensajes_1 = resp_get_1.json()
        assert len(mensajes_1) == 2
        assert mensajes_1[0]["contenido"] == "Hola, ¿cuándo nos juntamos?"
        assert mensajes_1[1]["contenido"] == "Hola! A la tarde en el campus."

        # 4. User2 lee el chat
        resp_get_2 = client.get(
            f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/mensajes",
            headers={"Authorization": token_user2}
        )
        assert resp_get_2.status_code == 200
        assert len(resp_get_2.json()) == 2

    def test_usuario_no_participante_no_puede_enviar_mensaje(self, client, token_user1, token_user2, token_user3):
        """Un usuario que no forma parte del intercambio no puede enviar mensajes."""
        intercambio_id = crear_intercambio_pendiente(client, token_user1, token_user2)

        resp = client.post(
            f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/mensajes",
            json={"contenido": "Mensaje intruso"},
            headers={"Authorization": token_user3}
        )
        assert resp.status_code == 403
        assert "No tenés permiso" in resp.json()["detail"]

    def test_usuario_no_participante_no_puede_obtener_mensajes(self, client, token_user1, token_user2, token_user3):
        """Un usuario que no forma parte del intercambio no puede leer los mensajes."""
        intercambio_id = crear_intercambio_pendiente(client, token_user1, token_user2)

        # User1 envía un mensaje
        client.post(
            f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/mensajes",
            json={"contenido": "Hola de nuevo"},
            headers={"Authorization": token_user1}
        )

        # User3 intenta leer
        resp = client.get(
            f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/mensajes",
            headers={"Authorization": token_user3}
        )
        assert resp.status_code == 403
        assert "No tenés permiso" in resp.json()["detail"]

    def test_mensajes_en_intercambio_inexistente_retorna_404(self, client, token_user1):
        """Endpoints de chat sobre un intercambio no existente devuelven 404."""
        non_existent_id = "64b0f1a9c1a5e123456789ab"
        resp_send = client.post(
            f"{ENDPOINT_INTERCAMBIOS}{non_existent_id}/mensajes",
            json={"contenido": "Test"},
            headers={"Authorization": token_user1}
        )
        assert resp_send.status_code == 404
        assert "Intercambio no encontrado" in resp_send.json()["detail"]

        resp_get = client.get(
            f"{ENDPOINT_INTERCAMBIOS}{non_existent_id}/mensajes",
            headers={"Authorization": token_user1}
        )
        assert resp_get.status_code == 404
        assert "Intercambio no encontrado" in resp_get.json()["detail"]

    def test_validar_longitud_mensaje_min_y_max(self, client, token_user1, token_user2):
        """El contenido del mensaje debe tener entre 1 y 1000 caracteres."""
        intercambio_id = crear_intercambio_pendiente(client, token_user1, token_user2)

        # Mensaje vacío
        resp_vacio = client.post(
            f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/mensajes",
            json={"contenido": ""},
            headers={"Authorization": token_user1}
        )
        assert resp_vacio.status_code == 422

        # Mensaje de más de 1000 caracteres
        contenido_largo = "x" * 1001
        resp_largo = client.post(
            f"{ENDPOINT_INTERCAMBIOS}{intercambio_id}/mensajes",
            json={"contenido": contenido_largo},
            headers={"Authorization": token_user1}
        )
        assert resp_largo.status_code == 422
