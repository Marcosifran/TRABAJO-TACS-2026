"""
Tests de integración — Caso de uso: Listar figuritas del álbum personal.

Cubre los endpoints:
  GET    /api/v1/usuarios/figuritas  → listar álbum del usuario autenticado
  POST   /api/v1/album/              → agregar al álbum
  DELETE /api/v1/album/{id}          → eliminar del álbum

Verifica:
- Listado exitoso del álbum personal
- Aislamiento entre usuarios
- El campo en_intercambio refleja si hay publicación activa
- Autorización para eliminar
"""
import pytest

ENDPOINT_ALBUM = "/api/v1/album/"
ENDPOINT_MIS_FIGURITAS = "/api/v1/usuarios/figuritas"
ENDPOINT_PUBLICACIONES = "/api/v1/publicaciones/"


@pytest.fixture
def figurita_user1(client, token_user1):
    """Agrega una figurita al álbum de user1 y devuelve sus datos."""
    resp = client.post(
        ENDPOINT_ALBUM,
        json={"numero": 10, "equipo": "Argentina", "jugador": "Messi", "cantidad": 2},
        headers={"X-User-Token": token_user1},
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def figurita_user2(client, token_user2):
    """Agrega una figurita al álbum de user2 y devuelve sus datos."""
    resp = client.post(
        ENDPOINT_ALBUM,
        json={"numero": 7, "equipo": "Brasil", "jugador": "Vinicius", "cantidad": 1},
        headers={"X-User-Token": token_user2},
    )
    assert resp.status_code == 201
    return resp.json()


# --------------------------
# GET /usuarios/figuritas
# --------------------------

class TestListarAlbumPersonal:

    def test_devuelve_200_con_lista_vacia_si_no_tiene_figuritas(self, client, token_user1):
        """Un usuario sin figuritas en el álbum recibe 200 y lista vacía."""
        resp = client.get(ENDPOINT_MIS_FIGURITAS, headers={"X-User-Token": token_user1})

        assert resp.status_code == 200
        data = resp.json()
        assert data["figuritas"] == []
        assert "usuario_id" in data

    def test_devuelve_sus_propias_figuritas(self, client, token_user1, figurita_user1):
        """El usuario ve exactamente las figuritas que tiene en su álbum."""
        resp = client.get(ENDPOINT_MIS_FIGURITAS, headers={"X-User-Token": token_user1})

        assert resp.status_code == 200
        figuritas = resp.json()["figuritas"]
        assert len(figuritas) == 1
        assert figuritas[0]["id"] == figurita_user1["id"]
        assert figuritas[0]["numero"] == figurita_user1["numero"]

    def test_devuelve_multiples_figuritas_propias(self, client, token_user1):
        """Cuando el usuario tiene varias figuritas en el álbum, aparecen todas."""
        payloads = [
            {"numero": 1, "equipo": "Argentina", "jugador": "Messi",   "cantidad": 1},
            {"numero": 2, "equipo": "Brasil",    "jugador": "Vinicius", "cantidad": 2},
            {"numero": 3, "equipo": "Francia",   "jugador": "Mbappé",   "cantidad": 1},
        ]
        for p in payloads:
            client.post(ENDPOINT_ALBUM, json=p, headers={"X-User-Token": token_user1})

        resp = client.get(ENDPOINT_MIS_FIGURITAS, headers={"X-User-Token": token_user1})

        assert resp.status_code == 200
        assert len(resp.json()["figuritas"]) == 3

    def test_no_incluye_figuritas_de_otros_usuarios(self, client, token_user1, figurita_user2):
        """Las figuritas de user2 no aparecen en el álbum de user1."""
        resp = client.get(ENDPOINT_MIS_FIGURITAS, headers={"X-User-Token": token_user1})

        assert resp.status_code == 200
        assert resp.json()["figuritas"] == []

    def test_cada_usuario_ve_solo_las_suyas(self, client, token_user1, token_user2, figurita_user1, figurita_user2):
        """user1 y user2 ven únicamente sus propias figuritas."""
        resp1 = client.get(ENDPOINT_MIS_FIGURITAS, headers={"X-User-Token": token_user1})
        resp2 = client.get(ENDPOINT_MIS_FIGURITAS, headers={"X-User-Token": token_user2})

        figuritas_user1 = resp1.json()["figuritas"]
        figuritas_user2 = resp2.json()["figuritas"]

        assert len(figuritas_user1) == 1
        assert figuritas_user1[0]["id"] == figurita_user1["id"]

        assert len(figuritas_user2) == 1
        assert figuritas_user2[0]["id"] == figurita_user2["id"]


# -------------------------------------------
# Campo en_intercambio
# -------------------------------------------

class TestCampoEnIntercambio:

    def test_figurita_recien_agregada_no_esta_en_intercambio(self, client, token_user1, figurita_user1):
        """Una figurita recién agregada al álbum tiene en_intercambio = False."""
        resp = client.get(ENDPOINT_MIS_FIGURITAS, headers={"X-User-Token": token_user1})

        figurita = resp.json()["figuritas"][0]
        assert figurita["en_intercambio"] is False

    def test_figurita_publicada_aparece_en_intercambio(self, client, token_user1, figurita_user1):
        """Después de publicarla, en_intercambio pasa a True."""
        client.post(
            ENDPOINT_PUBLICACIONES,
            json={
                "figurita_personal_id": figurita_user1["id"],
                "tipo_intercambio": "intercambio_directo",
                "cantidad_disponible": 1,
            },
            headers={"X-User-Token": token_user1},
        )

        resp = client.get(ENDPOINT_MIS_FIGURITAS, headers={"X-User-Token": token_user1})

        figurita = resp.json()["figuritas"][0]
        assert figurita["en_intercambio"] is True

    def test_retirar_publicacion_vuelve_en_intercambio_a_false(self, client, token_user1, figurita_user1):
        """Después de retirar la publicación, en_intercambio vuelve a False."""
        resp_pub = client.post(
            ENDPOINT_PUBLICACIONES,
            json={
                "figurita_personal_id": figurita_user1["id"],
                "tipo_intercambio": "intercambio_directo",
                "cantidad_disponible": 1,
            },
            headers={"X-User-Token": token_user1},
        )
        publicacion_id = resp_pub.json()["id"]

        client.delete(
            f"{ENDPOINT_PUBLICACIONES}{publicacion_id}",
            headers={"X-User-Token": token_user1},
        )

        resp = client.get(ENDPOINT_MIS_FIGURITAS, headers={"X-User-Token": token_user1})
        figurita = resp.json()["figuritas"][0]
        assert figurita["en_intercambio"] is False


# -----------------------------------------
# DELETE /album/{id} — autorización
# -----------------------------------------

class TestEliminarDelAlbum:

    def test_duenio_puede_eliminar_su_figurita(self, client, token_user1, figurita_user1):
        """El usuario que agregó la figurita puede eliminarla del álbum."""
        resp = client.delete(
            f"{ENDPOINT_ALBUM}{figurita_user1['id']}",
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 204

    def test_otro_usuario_no_puede_eliminar_figurita_ajena(self, client, token_user2, figurita_user1):
        """Un usuario distinto al dueño recibe 403 al intentar eliminar."""
        resp = client.delete(
            f"{ENDPOINT_ALBUM}{figurita_user1['id']}",
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 403

    def test_eliminar_figurita_inexistente_devuelve_404(self, client, token_user1):
        """Intentar eliminar un ID que no existe devuelve 404."""
        resp = client.delete(
            f"{ENDPOINT_ALBUM}9999",
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 404

    def test_no_se_puede_eliminar_figurita_con_publicacion_activa(self, client, token_user1, figurita_user1):
        """
        No se puede eliminar una figurita del álbum si tiene una publicación activa.
        Hay que retirar la publicación primero.
        """
        client.post(
            ENDPOINT_PUBLICACIONES,
            json={
                "figurita_personal_id": figurita_user1["id"],
                "tipo_intercambio": "intercambio_directo",
                "cantidad_disponible": 1,
            },
            headers={"X-User-Token": token_user1},
        )

        resp = client.delete(
            f"{ENDPOINT_ALBUM}{figurita_user1['id']}",
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 409