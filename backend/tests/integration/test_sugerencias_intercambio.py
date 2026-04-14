"""
Tests de integración — Caso de uso 4: Sugerencias automáticas de intercambio.

Cubre el endpoint GET /api/v1/usuarios/sugerencias verificando:
- Sin faltantes ni figuritas disponibles, la respuesta es vacía.
- Con faltantes que coinciden con figuritas de otros usuarios, devuelve sugerencias.
- Las propias figuritas publicadas nunca se sugieren.
- Múltiples coincidencias (varios usuarios, varios faltantes) se incluyen todas.
- La estructura de cada sugerencia tiene los campos esperados.
"""

import pytest

ENDPOINT_SUGERENCIAS = "/api/v1/usuarios/sugerencias"
ENDPOINT_FALTANTES   = "/api/v1/usuarios/faltantes"
ENDPOINT_FIGURITAS   = "/api/v1/figuritas/"


# ───────────────────
# Fixtures auxiliares
# ───────────────────

@pytest.fixture
def user1_con_faltantes(client, token_user1):
    """
    Registra tres faltantes para user1: números 10, 7 y 9.
    Retorna los números registrados para que los tests puedan referenciarlo.
    """
    numeros = [10, 7, 9]
    for n in numeros:
        client.post(ENDPOINT_FALTANTES, json={"numero_figurita": n}, headers={"X-User-Token": token_user1})
    return numeros


@pytest.fixture
def figuritas_user2(client, token_user2):
    """
    Publica tres figuritas como user2: números 10, 7 y 20.
    Retorna los payloads publicados.
    """
    figuritas = [
        {"numero": 10, "equipo": "Argentina", "jugador": "Lionel Messi",   "cantidad": 1, "tipo_intercambio": "intercambio_directo"},
        {"numero": 7,  "equipo": "Brasil",    "jugador": "Vinicius Junior", "cantidad": 2, "tipo_intercambio": "intercambio_directo"},
        {"numero": 20, "equipo": "Alemania",  "jugador": "Thomas Müller",   "cantidad": 1, "tipo_intercambio": "subasta"},
    ]
    for f in figuritas:
        client.post(ENDPOINT_FIGURITAS, json=f, headers={"X-User-Token": token_user2})
    return figuritas


@pytest.fixture
def escenario_base(user1_con_faltantes, figuritas_user2):
    """
    Fixture compuesto: user1 tiene faltantes [10, 7, 9] y user2 publicó [10, 7, 20].
    Las coincidencias esperadas son las figuritas 10 y 7.
    Llamar a este fixture en un test para generar el escenario base.
    """
    pass


# ───────────────────
# Sugerencias básicas
# ───────────────────

class TestSugerenciasBasicas:

    def test_sin_faltantes_devuelve_lista_vacia(self, client, token_user1):
        """Si el usuario no registró faltantes, no hay sugerencias posibles."""
        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"X-User-Token": token_user1})

        assert resp.status_code == 200
        assert resp.json()["sugerencias"] == []

    def test_con_faltantes_pero_sin_figuritas_disponibles_devuelve_lista_vacia(self, client, token_user1):
        """Aunque el usuario tenga faltantes, si nadie publicó esas figuritas, la respuesta es vacía."""
        client.post(ENDPOINT_FALTANTES, json={"numero_figurita": 99}, headers={"X-User-Token": token_user1})

        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"X-User-Token": token_user1})

        assert resp.status_code == 200
        assert resp.json()["sugerencias"] == []

    def test_devuelve_sugerencias_cuando_hay_coincidencias(self, client, token_user1, escenario_base):
        """Con faltantes que coinciden con figuritas de otro usuario, devuelve sugerencias."""
        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"X-User-Token": token_user1})

        assert resp.status_code == 200
        assert len(resp.json()["sugerencias"]) == 2  # figuritas 10 y 7 coinciden
        assert all(s["cubre_tu_faltante"] in [10, 7] for s in resp.json()["sugerencias"])

    def test_usuario_id_en_respuesta_coincide_con_usuario_autenticado(self, client, token_user1, escenario_base):
        """El campo usuario_id de la respuesta debe ser el del usuario que hizo el request."""
        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"X-User-Token": token_user1})

        assert resp.json()["usuario_id"] == 1  # user1 tiene id=1


# ────────────────────────────────────
# Las propias figuritas no se sugieren
# ────────────────────────────────────

class TestSugerenciasAislamiento:

    def test_propias_figuritas_no_se_incluyen_en_sugerencias(self, client, token_user1):
        """Una figurita publicada por el propio usuario no debe aparecer como sugerencia."""
        # user1 publica la figurita 10
        client.post(
            ENDPOINT_FIGURITAS,
            json={"numero": 10, "equipo": "Argentina", "jugador": "Messi", "cantidad": 1, "tipo_intercambio": "intercambio_directo"},
            headers={"X-User-Token": token_user1}
        )
        # user1 también la registra como faltante
        client.post(ENDPOINT_FALTANTES, json={"numero_figurita": 10}, headers={"X-User-Token": token_user1})

        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"X-User-Token": token_user1})

        assert resp.status_code == 200
        assert resp.json()["sugerencias"] == []

    def test_faltantes_de_user2_no_afectan_sugerencias_de_user1(self, client, token_user1, token_user2):
        """Los faltantes de user2 no deben aparecer en las sugerencias de user1."""
        # user2 registra faltante 10 y user1 publica figurita 10
        client.post(ENDPOINT_FALTANTES, json={"numero_figurita": 10}, headers={"X-User-Token": token_user2})
        client.post(
            ENDPOINT_FIGURITAS,
            json={"numero": 10, "equipo": "Argentina", "jugador": "Messi", "cantidad": 1, "tipo_intercambio": "intercambio_directo"},
            headers={"X-User-Token": token_user1}
        )
        # user1 registra faltante 55 (nadie lo tiene)
        client.post(ENDPOINT_FALTANTES, json={"numero_figurita": 55}, headers={"X-User-Token": token_user1})

        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"X-User-Token": token_user1})

        assert resp.status_code == 200
        assert resp.json()["sugerencias"] == []


# ────────────────────────────
# Estructura de la sugerencia
# ────────────────────────────

class TestEstructuraSugerencia:

    def test_sugerencia_contiene_campos_requeridos(self, client, token_user1, escenario_base):
        """Cada sugerencia debe tener los campos 'figurita', 'ofrecida_por' y 'cubre_tu_faltante'."""
        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"X-User-Token": token_user1})

        sugerencias = resp.json()["sugerencias"]
        assert len(sugerencias) > 0
        for s in sugerencias:
            assert "figurita" in s
            assert "ofrecida_por" in s
            assert "cubre_tu_faltante" in s

    def test_ofrecida_por_es_nombre_del_usuario_oferente(self, client, token_user1, escenario_base):
        """El campo 'ofrecida_por' debe coincidir con el nombre del usuario que publicó la figurita."""
        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"X-User-Token": token_user1})

        for s in resp.json()["sugerencias"]:
            assert s["ofrecida_por"] == "jeronimo"  # user2 se llama 'jeronimo'

    def test_cubre_tu_faltante_coincide_con_numero_de_figurita(self, client, token_user1, escenario_base):
        """El campo 'cubre_tu_faltante' debe ser el mismo número que la figurita sugerida."""
        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"X-User-Token": token_user1})

        for s in resp.json()["sugerencias"]:
            assert s["cubre_tu_faltante"] == s["figurita"]["numero"]

    def test_figurita_en_sugerencia_contiene_datos_completos(self, client, token_user1, escenario_base):
        """El objeto 'figurita' dentro de la sugerencia debe incluir numero, equipo y jugador."""
        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"X-User-Token": token_user1})

        for s in resp.json()["sugerencias"]:
            figurita = s["figurita"]
            assert "numero" in figurita
            assert "equipo" in figurita
            assert "jugador" in figurita


# ─────────────────────────────────────────────
# Múltiples coincidencias y múltiples usuarios
# ─────────────────────────────────────────────

class TestSugerenciasMultiples:

    def test_figurita_con_cantidad_mayor_a_uno_genera_una_sola_sugerencia(self, client, token_user1, token_user2):
        """
        Una figurita publicada con cantidad > 1 no debe generar sugerencias duplicadas.
        La sugerencia se da una vez, independientemente de la cantidad disponible.
        """
        client.post(ENDPOINT_FALTANTES, json={"numero_figurita": 7}, headers={"X-User-Token": token_user1})
        client.post(
            ENDPOINT_FIGURITAS,
            json={"numero": 7, "equipo": "Brasil", "jugador": "Vinicius", "cantidad": 5, "tipo_intercambio": "intercambio_directo"},
            headers={"X-User-Token": token_user2}
        )

        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"X-User-Token": token_user1})

        sugerencias_numero_7 = [s for s in resp.json()["sugerencias"] if s["cubre_tu_faltante"] == 7]
        assert len(sugerencias_numero_7) == 1

    def test_un_faltante_ofrecido_por_dos_usuarios_genera_dos_sugerencias(self, client, token_user1, token_user2):
        """
        Si dos usuarios distintos tienen la figurita que le falta al solicitante,
        se generan dos sugerencias separadas, una por cada oferente.

        Para cubrir este escenario se usa un tercer usuario simulado.
        """
        from app.repositories import usuario_repo, figurita_repo
        from app.schemas.figurita import FiguritaCreate

        # Simulamos un tercer usuario directamente en la DB en memoria
        usuario_repo._db_usuarios.append({"id": 3, "nombre": "tercerusuario", "email": "tercero@utn", "token": "token_tercero"})

        # user1 registra faltante 10
        client.post(ENDPOINT_FALTANTES, json={"numero_figurita": 10}, headers={"X-User-Token": token_user1})

        # user2 publica figurita 10
        client.post(
            ENDPOINT_FIGURITAS,
            json={"numero": 10, "equipo": "Argentina", "jugador": "Messi", "cantidad": 1, "tipo_intercambio": "intercambio_directo"},
            headers={"X-User-Token": token_user2}
        )

        # usuario 3 también publica figurita 10
        client.post(
            ENDPOINT_FIGURITAS,
            json={"numero": 10, "equipo": "Argentina", "jugador": "Messi", "cantidad": 1, "tipo_intercambio": "intercambio_directo"},
            headers={"X-User-Token": "token_tercero"}
        )

        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"X-User-Token": token_user1})

        sugerencias_numero_10 = [s for s in resp.json()["sugerencias"] if s["cubre_tu_faltante"] == 10]
        assert len(sugerencias_numero_10) == 2

        oferentes = {s["ofrecida_por"] for s in sugerencias_numero_10}
        assert "jeronimo" in oferentes
        assert "tercerusuario" in oferentes

