"""
Tests de integración — Autenticación.

Verifica el comportamiento del mecanismo de autenticación por header X-User-Token,
que es transversal a todos los endpoints protegidos de la aplicación.
"""

# Para testear usamos cualquier endpoint protegido.
ENDPOINT_PROTEGIDO = "/api/v1/album/"

class TestAutenticacion:

    def test_sin_token_devuelve_422(self, client, figurita_valida):
        """Sin el header X-User-Token FastAPI rechaza el request con 422 (campo requerido ausente)."""
        resp = client.post(ENDPOINT_PROTEGIDO, json=figurita_valida)

        assert resp.status_code == 422

    def test_token_invalido_devuelve_401(self, client, figurita_valida):
        """Un token que no corresponde a ningún usuario devuelve 401."""
        resp = client.post(
            ENDPOINT_PROTEGIDO,
            json=figurita_valida,
            headers={"X-User-Token": "token-que-no-existe"},
        )

        assert resp.status_code == 401

    def test_token_vacio_devuelve_401(self, client, figurita_valida):
        """Un header X-User-Token vacío no matchea ningún usuario y devuelve 401."""
        resp = client.post(
            ENDPOINT_PROTEGIDO,
            json=figurita_valida,
            headers={"X-User-Token": ""},
        )

        assert resp.status_code == 401

    def test_token_valido_permite_acceso(self, client, token_user1, figurita_valida):
        """Un token válido permite realizar la operación correctamente."""
        resp = client.post(
            ENDPOINT_PROTEGIDO,
            json=figurita_valida,
            headers={"X-User-Token": token_user1},
        )

        assert resp.status_code == 201
