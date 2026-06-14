"""
Tests de integración — Autenticación.

Verifica el comportamiento del mecanismo de autenticación por JWT en el header
Authorization: Bearer <token>, que es transversal a todos los endpoints
protegidos de la aplicación.
"""

from datetime import timedelta

from app.security import create_access_token

# Para testear usamos cualquier endpoint protegido.
ENDPOINT_PROTEGIDO = "/api/v1/album/"

class TestAutenticacion:

    def test_sin_token_devuelve_422(self, client, figurita_valida):
        """Sin el header Authorization FastAPI rechaza el request con 422 (campo requerido ausente)."""
        resp = client.post(ENDPOINT_PROTEGIDO, json=figurita_valida)

        assert resp.status_code == 422

    def test_token_invalido_devuelve_401(self, client, figurita_valida):
        """Un Bearer que no corresponde a un JWT válido devuelve 401."""
        resp = client.post(
            ENDPOINT_PROTEGIDO,
            json=figurita_valida,
            headers={"Authorization": "Bearer token-que-no-existe"},
        )

        assert resp.status_code == 401

    def test_authorization_sin_esquema_bearer_devuelve_401(self, client, figurita_valida):
        """Un header Authorization sin el esquema Bearer (o sin token) devuelve 401."""
        resp = client.post(
            ENDPOINT_PROTEGIDO,
            json=figurita_valida,
            headers={"Authorization": "Bearer "},
        )

        assert resp.status_code == 401

    def test_token_valido_permite_acceso(self, client, token_user1, figurita_valida):
        """Un token válido permite realizar la operación correctamente."""
        resp = client.post(
            ENDPOINT_PROTEGIDO,
            json=figurita_valida,
            headers={"Authorization": token_user1},
        )

        assert resp.status_code == 201

    def test_bearer_jwt_valido_permite_acceso(self, client, figurita_valida):
        """Un JWT válido en Authorization: Bearer también permite acceder."""
        token = create_access_token(subject=1, email="marcos@utn")

        resp = client.post(
            ENDPOINT_PROTEGIDO,
            json=figurita_valida,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 201

    def test_bearer_jwt_invalido_devuelve_401(self, client, figurita_valida):
        """Un JWT manipulado o con firma inválida devuelve 401."""
        token = create_access_token(subject=1, email="marcos@utn") + "corrupto"

        resp = client.post(
            ENDPOINT_PROTEGIDO,
            json=figurita_valida,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 401

    def test_bearer_jwt_expirado_devuelve_401(self, client, figurita_valida):
        """Un JWT expirado no debe permitir acceso."""
        token = create_access_token(
            subject=1,
            email="marcos@utn",
            expires_delta=timedelta(minutes=-1),
        )

        resp = client.post(
            ENDPOINT_PROTEGIDO,
            json=figurita_valida,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 401
