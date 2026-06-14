"""
Tests de integración del flujo de autenticación JWT: login y registro.
"""

from app.core.config import settings
from app.repositories import usuario_repo


SEED_EMAIL = usuario_repo._db_usuarios[0]["email"]
SEED_PASSWORD = settings.seed_user_password


def test_login_con_credenciales_validas_devuelve_jwt(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": SEED_EMAIL, "password": SEED_PASSWORD},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["usuario"]["email"] == SEED_EMAIL
    # El hash de la contraseña nunca debe volver en la respuesta.
    assert "password_hash" not in body["usuario"]
    assert "token" not in body["usuario"]


def test_login_con_password_incorrecta_devuelve_401(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": SEED_EMAIL, "password": "password-incorrecta"},
    )
    assert resp.status_code == 401


def test_login_con_email_inexistente_devuelve_401(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "noexiste@test.com", "password": "loquesea"},
    )
    assert resp.status_code == 401


def test_register_crea_usuario_y_permite_login(client):
    nuevo = {"nombre": "ana", "email": "ana@test.com", "password": "secret123"}

    resp = client.post("/api/v1/auth/register", json=nuevo)
    assert resp.status_code == 201
    body = resp.json()
    assert body["access_token"]
    assert body["usuario"]["email"] == nuevo["email"]
    assert body["usuario"]["id"] not in (1, 2)  # id distinto a los sembrados

    # El usuario recién creado puede loguearse con esas credenciales.
    login = client.post(
        "/api/v1/auth/login",
        json={"email": nuevo["email"], "password": nuevo["password"]},
    )
    assert login.status_code == 200


def test_register_con_email_duplicado_devuelve_409(client):
    nuevo = {"nombre": "ana", "email": "ana@test.com", "password": "secret123"}
    assert client.post("/api/v1/auth/register", json=nuevo).status_code == 201

    duplicado = client.post("/api/v1/auth/register", json=nuevo)
    assert duplicado.status_code == 409


def test_jwt_obtenido_permite_acceder_a_endpoint_protegido(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": SEED_EMAIL, "password": SEED_PASSWORD},
    )
    token = login.json()["access_token"]

    resp = client.get(
        "/api/v1/usuarios/faltantes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


def test_listar_usuarios_devuelve_seed_sin_datos_sensibles(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": SEED_EMAIL, "password": SEED_PASSWORD},
    )
    token = login.json()["access_token"]

    resp = client.get("/api/v1/usuarios", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    usuarios = resp.json()
    assert any(u["email"] == SEED_EMAIL for u in usuarios)
    # Nunca se exponen el hash de la contraseña ni el token legacy.
    for u in usuarios:
        assert "password_hash" not in u
        assert "token" not in u


def test_listar_usuarios_requiere_autenticacion(client):
    resp = client.get("/api/v1/usuarios")
    assert resp.status_code in (401, 422)
