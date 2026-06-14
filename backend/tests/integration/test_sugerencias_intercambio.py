"""
Tests de integración — Caso de uso: Sugerencias automáticas de intercambio.

Cubre el endpoint GET /api/v1/publicaciones/sugerencias verificando:
- Sin faltantes ni figuritas disponibles, la respuesta es vacía.
- Con faltantes que coinciden con publicaciones de otros usuarios, devuelve sugerencias.
- Las propias publicaciones nunca se sugieren.
- Múltiples coincidencias se incluyen todas.
- La estructura de cada sugerencia tiene los campos esperados.
"""

import pytest

ENDPOINT_SUGERENCIAS  = "/api/v1/publicaciones/sugerencias"
ENDPOINT_FALTANTES    = "/api/v1/usuarios/faltantes"
ENDPOINT_ALBUM        = "/api/v1/album/"
ENDPOINT_PUBLICACIONES = "/api/v1/publicaciones/"


# ───────────────────
# Helper
# ───────────────────

def agregar_y_publicar(client, token, numero, equipo, jugador, cantidad, tipo):
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
            "cantidad_disponible": 1,
        },
        headers={"Authorization": token},
    )
    assert resp_pub.status_code == 201
    return resp_pub.json()["id"]


# ───────────────────
# Fixtures auxiliares
# ───────────────────

@pytest.fixture
def user1_con_faltantes(client, token_user1):
    numeros = [10, 7, 9]
    for n in numeros:
        client.post(
            ENDPOINT_FALTANTES,
            json={"numero_figurita": n},
            headers={"Authorization": token_user1},
        )
    return numeros


@pytest.fixture
def figuritas_user2(client, token_user2):
    datos = [
        (10, "Argentina", "Lionel Messi",   1, "intercambio_directo"),
        (7,  "Brasil",    "Vinicius Junior", 2, "intercambio_directo"),
        (20, "Alemania",  "Thomas Müller",   1, "subasta"),
    ]
    for numero, equipo, jugador, cantidad, tipo in datos:
        agregar_y_publicar(client, token_user2, numero, equipo, jugador, cantidad, tipo)


@pytest.fixture
def escenario_base(user1_con_faltantes, figuritas_user2):
    """user1 tiene faltantes [10, 7, 9] y user2 publicó [10, 7, 20]."""
    pass


# ───────────────────
# Sugerencias básicas
# ───────────────────

class TestSugerenciasBasicas:

    def test_sin_faltantes_devuelve_lista_vacia(self, client, token_user1):
        """Si el usuario no registró faltantes, no hay sugerencias posibles."""
        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"Authorization": token_user1})

        assert resp.status_code == 200
        assert resp.json() == []

    def test_con_faltantes_pero_sin_publicaciones_devuelve_lista_vacia(self, client, token_user1):
        """Aunque el usuario tenga faltantes, si nadie publicó esas figuritas la respuesta es vacía."""
        client.post(
            ENDPOINT_FALTANTES,
            json={"numero_figurita": 99},
            headers={"Authorization": token_user1},
        )

        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"Authorization": token_user1})

        assert resp.status_code == 200
        assert resp.json() == []

    def test_devuelve_sugerencias_cuando_hay_coincidencias(self, client, token_user1, escenario_base):
        """Con faltantes que coinciden con publicaciones de otro usuario, devuelve sugerencias."""
        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"Authorization": token_user1})

        assert resp.status_code == 200
        sugerencias = resp.json()
        assert len(sugerencias) == 2
        assert all(s["cubre_tu_faltante"] in [10, 7] for s in sugerencias)


# ────────────────────────────────────
# Las propias publicaciones no se sugieren
# ────────────────────────────────────

class TestSugerenciasAislamiento:

    def test_propias_publicaciones_no_se_incluyen_en_sugerencias(self, client, token_user1):
        """Una figurita publicada por el propio usuario no debe aparecer como sugerencia."""
        agregar_y_publicar(client, token_user1, 10, "Argentina", "Messi", 1, "intercambio_directo")
        client.post(
            ENDPOINT_FALTANTES,
            json={"numero_figurita": 10},
            headers={"Authorization": token_user1},
        )

        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"Authorization": token_user1})

        assert resp.status_code == 200
        assert resp.json() == []

    def test_faltantes_de_user2_no_afectan_sugerencias_de_user1(self, client, token_user1, token_user2):
        """Los faltantes de user2 no deben aparecer en las sugerencias de user1."""
        client.post(
            ENDPOINT_FALTANTES,
            json={"numero_figurita": 10},
            headers={"Authorization": token_user2},
        )
        agregar_y_publicar(client, token_user1, 10, "Argentina", "Messi", 1, "intercambio_directo")
        client.post(
            ENDPOINT_FALTANTES,
            json={"numero_figurita": 55},
            headers={"Authorization": token_user1},
        )

        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"Authorization": token_user1})

        assert resp.status_code == 200
        assert resp.json() == []


# ────────────────────────────
# Estructura de la sugerencia
# ────────────────────────────

class TestEstructuraSugerencia:

    def test_sugerencia_contiene_campos_requeridos(self, client, token_user1, escenario_base):
        """Cada sugerencia debe tener los campos 'publicacion', 'ofrecida_por' y 'cubre_tu_faltante'."""
        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"Authorization": token_user1})

        sugerencias = resp.json()
        assert len(sugerencias) > 0
        for s in sugerencias:
            assert "publicacion" in s
            assert "ofrecida_por" in s
            assert "cubre_tu_faltante" in s

    def test_ofrecida_por_es_nombre_del_usuario_oferente(self, client, token_user1, escenario_base):
        """El campo 'ofrecida_por' debe coincidir con el nombre del usuario que publicó."""
        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"Authorization": token_user1})

        for s in resp.json():
            assert s["ofrecida_por"] == "jeronimo"

    def test_cubre_tu_faltante_coincide_con_numero_de_la_publicacion(self, client, token_user1, escenario_base):
        """El campo 'cubre_tu_faltante' debe ser el mismo número que la publicación sugerida."""
        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"Authorization": token_user1})

        for s in resp.json():
            assert s["cubre_tu_faltante"] == s["publicacion"]["numero"]

    def test_publicacion_en_sugerencia_contiene_datos_completos(self, client, token_user1, escenario_base):
        """El objeto 'publicacion' dentro de la sugerencia debe incluir numero, equipo y jugador."""
        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"Authorization": token_user1})

        for s in resp.json():
            pub = s["publicacion"]
            assert "numero" in pub
            assert "equipo" in pub
            assert "jugador" in pub
            assert "tipo_intercambio" in pub


# ─────────────────────────────────────────────
# Múltiples coincidencias
# ─────────────────────────────────────────────

class TestSugerenciasMultiples:

    def test_figurita_con_cantidad_mayor_a_uno_genera_una_sola_sugerencia(
        self, client, token_user1, token_user2
    ):
        client.post(
            ENDPOINT_FALTANTES,
            json={"numero_figurita": 7},
            headers={"Authorization": token_user1},
        )
        agregar_y_publicar(client, token_user2, 7, "Brasil", "Vinicius", 5, "intercambio_directo")

        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"Authorization": token_user1})

        sugerencias_7 = [s for s in resp.json() if s["cubre_tu_faltante"] == 7]
        assert len(sugerencias_7) == 1

    def test_un_faltante_ofrecido_por_dos_usuarios_genera_dos_sugerencias(
        self, client, token_user1, token_user2
    ):
        """
        Si dos usuarios distintos tienen la figurita que le falta al solicitante,
        se generan dos sugerencias separadas, una por cada oferente.
        """
        from app.repositories import usuario_repo
        from app.security import create_access_token

        usuario_repo._db_usuarios.append({
            "id": 3,
            "nombre": "tercerusuario",
            "email": "tercero@utn",
        })
        token_tercero = f"Bearer {create_access_token(subject=3, email='tercero@utn')}"

        client.post(
            ENDPOINT_FALTANTES,
            json={"numero_figurita": 10},
            headers={"Authorization": token_user1},
        )

        agregar_y_publicar(client, token_user2, 10, "Argentina", "Messi", 1, "intercambio_directo")
        agregar_y_publicar(client, token_tercero, 10, "Argentina", "Messi", 1, "intercambio_directo")

        resp = client.get(ENDPOINT_SUGERENCIAS, headers={"Authorization": token_user1})

        sugerencias_10 = [s for s in resp.json() if s["cubre_tu_faltante"] == 10]
        assert len(sugerencias_10) == 2

        oferentes = {s["ofrecida_por"] for s in sugerencias_10}
        assert "jeronimo" in oferentes
        assert "tercerusuario" in oferentes
