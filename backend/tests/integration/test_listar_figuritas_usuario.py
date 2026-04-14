"""
Tests de listar figuritas del usuario autenticado.

Cubre el endpoint GET /api/v1/usuarios/figuritas verificando:
- Listado exitoso de figuritas propias
- Aislamiento entre usuarios
- Respuesta vacía si no publicó ninguna
"""
import pytest

ENDPOINT_FIGURITAS = "/api/v1/figuritas/"
ENDPOINT_MIS_FIGURITAS = "/api/v1/usuarios/figuritas"


@pytest.fixture
def figurita_user1(client, token_user1):
    """Publica una figurita como user1 y devuelve sus datos."""
    payload = {
        "numero": 10,
        "equipo": "Argentina",
        "jugador": "Messi",
        "cantidad": 2,
        "tipo_intercambio": "intercambio_directo",
    }
    resp = client.post(ENDPOINT_FIGURITAS, json=payload, headers={"X-User-Token": token_user1})
    assert resp.status_code == 201
    return resp.json()["data"]


@pytest.fixture
def figurita_user2(client, token_user2):
    """Publica una figurita como user2 y devuelve sus datos."""
    payload = {
        "numero": 7,
        "equipo": "Brasil",
        "jugador": "Vinicius",
        "cantidad": 1,
        "tipo_intercambio": "subasta",
    }
    resp = client.post(ENDPOINT_FIGURITAS, json=payload, headers={"X-User-Token": token_user2})
    assert resp.status_code == 201
    return resp.json()["data"]


# ------------------------
# GET /usuarios/figuritas
# ------------------------

class TestListarFiguritasUsuario:

    def test_devuelve_200_con_lista_vacia_si_no_publico_nada(self, client, token_user1):
        """Un usuario sin figuritas publicadas recibe 200 y lista vacía."""
        resp = client.get(ENDPOINT_MIS_FIGURITAS, headers={"X-User-Token": token_user1})

        assert resp.status_code == 200
        data = resp.json()
        assert data["figuritas"] == []
        assert "usuario_id" in data

    def test_devuelve_sus_propias_figuritas(self, client, token_user1, figurita_user1):
        """El usuario ve exactamente las figuritas que publicó."""
        resp = client.get(ENDPOINT_MIS_FIGURITAS, headers={"X-User-Token": token_user1})

        assert resp.status_code == 200
        figuritas = resp.json()["figuritas"]
        assert len(figuritas) == 1
        assert figuritas[0]["id"] == figurita_user1["id"]
        assert figuritas[0]["numero"] == figurita_user1["numero"]

    def test_devuelve_multiples_figuritas_propias(self, client, token_user1):
        """Cuando el usuario publicó varias, aparecen todas."""
        payloads = [
            {"numero": 1, "equipo": "Argentina", "jugador": "Messi", "cantidad": 1, "tipo_intercambio": "intercambio_directo"},
            {"numero": 2, "equipo": "Brasil", "jugador": "Vinicius", "cantidad": 2, "tipo_intercambio": "subasta"},
            {"numero": 3, "equipo": "Francia", "jugador": "Mbappé", "cantidad": 1, "tipo_intercambio": "intercambio_directo"},
        ]
        for p in payloads:
            client.post(ENDPOINT_FIGURITAS, json=p, headers={"X-User-Token": token_user1})

        resp = client.get(ENDPOINT_MIS_FIGURITAS, headers={"X-User-Token": token_user1})

        assert resp.status_code == 200
        assert len(resp.json()["figuritas"]) == 3

    def test_no_incluye_figuritas_de_otros_usuarios(self, client, token_user1, token_user2, figurita_user2):
        """Las figuritas de user2 no aparecen en el listado de user1."""
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

# -----------------------------------------
# DELETE /figuritas/{id} — autorización
# -----------------------------------------

class TestEliminarFiguritaAutorizacion:

    def test_duenio_puede_eliminar_su_figurita(self, client, token_user1, figurita_user1):
        """El usuario que publicó la figurita puede eliminarla."""
        resp = client.delete(
            f"{ENDPOINT_FIGURITAS}{figurita_user1['id']}",
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 200
        assert resp.json()["mensaje"] == "Figurita eliminada"

    def test_otro_usuario_no_puede_eliminar_figurita_ajena(self, client, token_user2, figurita_user1):
        """Un usuario distinto al dueño recibe 403 al intentar eliminar."""
        resp = client.delete(
            f"{ENDPOINT_FIGURITAS}{figurita_user1['id']}",
            headers={"X-User-Token": token_user2},
        )

        assert resp.status_code == 403

    def test_eliminar_figurita_inexistente_devuelve_404(self, client, token_user1):
        """Intentar eliminar un ID que no existe devuelve 404."""
        resp = client.delete(
            f"{ENDPOINT_FIGURITAS}9999",
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 404
