"""
Tests de integración — Caso de uso: Publicar figurita para intercambio.

Cubre el endpoint POST /api/v1/figuritas/ verificando:
- Publicación exitosa con todos los campos requeridos
- Validaciones de campos (número, cantidad, tipo de intercambio)
- Persistencia: la figurita publicada aparece en la búsqueda
"""
import pytest


ENDPOINT = "/api/v1/figuritas/"

# -----------------
# Caminos correctos
# -----------------

class TestPublicarFiguritaExitosa:

    def test_publicar_con_intercambio_directo(self, client, token_user1, figurita_valida):
        """Publicar una figurita con tipo intercambio_directo devuelve 201 y los datos correctos."""
        figurita_valida["tipo_intercambio"] = "intercambio_directo"

        resp = client.post(ENDPOINT, json=figurita_valida, headers={"X-User-Token": token_user1})

        assert resp.status_code == 201
        data = resp.json()["data"]
        # Chequeamos que los datos devueltos sean correctos.
        assert data["numero"] == figurita_valida["numero"]
        assert data["equipo"] == figurita_valida["equipo"]
        assert data["jugador"] == figurita_valida["jugador"]
        assert data["cantidad"] == figurita_valida["cantidad"]
        assert data["tipo_intercambio"] == "intercambio_directo"
        assert "id" in data
        assert data["usuario_id"] is not None

    def test_publicar_con_subasta(self, client, token_user1, figurita_valida):
        """Publicar una figurita con tipo subasta devuelve 201."""
        figurita_valida["tipo_intercambio"] = "subasta"

        resp = client.post(ENDPOINT, json=figurita_valida, headers={"X-User-Token": token_user1})

        assert resp.status_code == 201
        assert resp.json()["data"]["tipo_intercambio"] == "subasta"

    def test_figurita_publicada_aparece_en_busqueda(self, client, token_user1, figurita_valida):
        """Después de publicar, la figurita es recuperable por GET /figuritas/."""
        client.post(ENDPOINT, json=figurita_valida, headers={"X-User-Token": token_user1})

        resp = client.get(ENDPOINT)

        assert resp.status_code == 200
        disponibles = resp.json()["figuritasDisponibles"]
        assert len(disponibles) == 1
        assert disponibles[0]["numero"] == figurita_valida["numero"]

    def test_usuario_id_queda_asociado_a_la_figurita(self, client, token_user1, figurita_valida):
        """El usuario_id registrado en la figurita corresponde al usuario que la publicó."""
        resp = client.post(ENDPOINT, json=figurita_valida, headers={"X-User-Token": token_user1})

        usuario_id_esperado = 1  # user1 tiene id=1
        assert resp.json()["data"]["usuario_id"] == usuario_id_esperado

    def test_publicar_multiples_figuritas(self, client, token_user1):
        """Un mismo usuario puede publicar varias figuritas distintas en varias solicitudes."""
        figuritas = [
            {"numero": 1, "equipo": "Argentina", "jugador": "Messi", "cantidad": 1, "tipo_intercambio": "intercambio_directo"},
            {"numero": 2, "equipo": "Brasil", "jugador": "Vinicius", "cantidad": 3, "tipo_intercambio": "subasta"},
            {"numero": 3, "equipo": "Francia", "jugador": "Mbappé", "cantidad": 2, "tipo_intercambio": "intercambio_directo"},
        ]
        for f in figuritas:
            resp = client.post(ENDPOINT, json=f, headers={"X-User-Token": token_user1})
            assert resp.status_code == 201

        disponibles = client.get(ENDPOINT).json()["figuritasDisponibles"]
        assert len(disponibles) == 3


# --------------------------------
# Validaciones de campos del body
# --------------------------------

class TestValidacionCampos:

    def test_numero_de_figurita_es_requerido(self, client, token_user1, figurita_valida):
        """Omitir el número de figurita devuelve 422."""
        del figurita_valida["numero"]

        resp = client.post(ENDPOINT, json=figurita_valida, headers={"X-User-Token": token_user1})

        assert resp.status_code == 422

    def test_numero_de_figurita_no_puede_ser_cero(self, client, token_user1, figurita_valida):
        """El número de figurita debe ser >= 1. Enviar 0 devuelve 422."""
        figurita_valida["numero"] = 0

        resp = client.post(ENDPOINT, json=figurita_valida, headers={"X-User-Token": token_user1})

        assert resp.status_code == 422

    def test_numero_de_figurita_no_puede_ser_negativo(self, client, token_user1, figurita_valida):
        """El número de figurita no puede ser negativo. Devuelve 422."""
        figurita_valida["numero"] = -5

        resp = client.post(ENDPOINT, json=figurita_valida, headers={"X-User-Token": token_user1})

        assert resp.status_code == 422

    def test_equipo_es_requerido(self, client, token_user1, figurita_valida):
        """Omitir el equipo devuelve 422."""
        del figurita_valida["equipo"]

        resp = client.post(ENDPOINT, json=figurita_valida, headers={"X-User-Token": token_user1})

        assert resp.status_code == 422

    def test_equipo_no_puede_ser_string_vacio(self, client, token_user1, figurita_valida):
        """El equipo no puede ser un string vacío (min_length=1). Devuelve 422."""
        figurita_valida["equipo"] = ""

        resp = client.post(ENDPOINT, json=figurita_valida, headers={"X-User-Token": token_user1})

        assert resp.status_code == 422

    def test_jugador_es_requerido(self, client, token_user1, figurita_valida):
        """Omitir el jugador devuelve 422."""
        del figurita_valida["jugador"]

        resp = client.post(ENDPOINT, json=figurita_valida, headers={"X-User-Token": token_user1})

        assert resp.status_code == 422

    def test_jugador_no_puede_ser_string_vacio(self, client, token_user1, figurita_valida):
        """El jugador no puede ser un string vacío (min_length=1). Devuelve 422."""
        figurita_valida["jugador"] = ""

        resp = client.post(ENDPOINT, json=figurita_valida, headers={"X-User-Token": token_user1})

        assert resp.status_code == 422

    def test_cantidad_es_requerida(self, client, token_user1, figurita_valida):
        """Omitir la cantidad devuelve 422."""
        del figurita_valida["cantidad"]

        resp = client.post(ENDPOINT, json=figurita_valida, headers={"X-User-Token": token_user1})

        assert resp.status_code == 422

    def test_cantidad_no_puede_ser_cero(self, client, token_user1, figurita_valida):
        """La cantidad debe ser >= 1. Enviar 0 devuelve 422."""
        figurita_valida["cantidad"] = 0

        resp = client.post(ENDPOINT, json=figurita_valida, headers={"X-User-Token": token_user1})

        assert resp.status_code == 422

    def test_tipo_intercambio_es_requerido(self, client, token_user1, figurita_valida):
        """Omitir tipo_intercambio devuelve 422."""
        del figurita_valida["tipo_intercambio"]

        resp = client.post(ENDPOINT, json=figurita_valida, headers={"X-User-Token": token_user1})

        assert resp.status_code == 422

    def test_tipo_intercambio_valor_invalido(self, client, token_user1, figurita_valida):
        """Un tipo_intercambio fuera del enum devuelve 422."""
        figurita_valida["tipo_intercambio"] = "ambas"

        resp = client.post(ENDPOINT, json=figurita_valida, headers={"X-User-Token": token_user1})

        assert resp.status_code == 422


