"""
Tests de integración — Caso de uso: Registrar figuritas faltantes.

Cubre los endpoints:
  POST /api/v1/usuarios/faltantes  → registrar una figurita como faltante
  GET  /api/v1/usuarios/faltantes  → listar los faltantes del usuario autenticado

Verifica:
- Registro exitoso con y sin campos opcionales
- Que los faltantes de un usuario no se mezclan con los de otro usuario
- Validaciones de campos
- No duplicados dentro del mismo usuario, pero sí entre usuarios distintos
"""

ENDPOINT = "/api/v1/usuarios/faltantes"


# -----------------
# Caminos correctos
# -----------------

class TestRegistrarFaltanteExitoso:

    def test_registrar_faltante_solo_con_numero(self, client, token_user1):
        """Registrar un faltante con solo el número (campos opcionales ausentes) devuelve 201."""
        resp = client.post(
            ENDPOINT,
            json={"numero_figurita": 42},
            headers={"X-User-Token": token_user1}
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["numero_figurita"] == 42
        assert "id" in data
        assert data["usuario_id"] is not None

    def test_registrar_faltante_con_todos_los_campos(self, client, token_user1):
        """Registrar un faltante con número, equipo y jugador devuelve 201 con todos los datos."""
        payload = {
            "numero_figurita": 7,
            "equipo": "Alemania",
            "jugador": "Muller"
        }

        resp = client.post(ENDPOINT, json=payload, headers={"X-User-Token": token_user1})

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["numero_figurita"] == 7
        assert data["equipo"] == "Alemania"
        assert data["jugador"] == "Muller"

    def test_registrar_faltante_con_solo_equipo_opcional(self, client, token_user1):
        """Registrar un faltante con número y equipo (sin jugador) devuelve 201."""
        payload = {
            "numero_figurita": 15,
            "equipo": "Francia"
        }

        resp = client.post(
            ENDPOINT,
            json=payload,
            headers={"X-User-Token": token_user1}
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["numero_figurita"] == 15
        assert data["equipo"] == "Francia"
        assert data["jugador"] is None

    def test_usuario_id_queda_asociado_al_faltante(self, client, token_user1):
        """El faltante registrado queda vinculado al usuario que hizo el request."""
        resp = client.post(
            ENDPOINT,
            json={"numero_figurita": 99},
            headers={"X-User-Token": token_user1}
        )

        usuario_id_esperado = 1  # user1 tiene id=1
        assert resp.json()["data"]["usuario_id"] == usuario_id_esperado

    def test_registrar_multiples_faltantes(self, client, token_user1):
        """Un usuario puede registrar varios faltantes distintos."""
        numerosFaltantes = [1, 5, 10, 50, 100]

        for numero in numerosFaltantes:
            resp = client.post(
                ENDPOINT,
                json={"numero_figurita": numero},
                headers={"X-User-Token": token_user1}
            )
            assert resp.status_code == 201

        resp_lista = client.get(ENDPOINT, headers={"X-User-Token": token_user1})
        assert len(resp_lista.json()["faltantes"]) == len(numerosFaltantes)


# -------------------
# Listar faltantes
# -------------------

class TestListarFaltantes:

    def test_listar_faltantes_vacio(self, client, token_user1):
        """Sin faltantes registrados, la lista es vacía."""
        resp = client.get(ENDPOINT, headers={"X-User-Token": token_user1})

        assert resp.status_code == 200
        assert resp.json()["faltantes"] == []

    def test_listar_faltantes_del_usuario_autenticado(self, client, token_user1):
        """Listar devuelve solo los faltantes del usuario que hace el request."""
        client.post(ENDPOINT, json={"numero_figurita": 10}, headers={"X-User-Token": token_user1})
        client.post(ENDPOINT, json={"numero_figurita": 20}, headers={"X-User-Token": token_user1})

        resp = client.get(ENDPOINT, headers={"X-User-Token": token_user1})

        assert resp.status_code == 200
        faltantes = resp.json()["faltantes"]
        assert len(faltantes) == 2
        numeros = [f["numero_figurita"] for f in faltantes]
        assert 10 in numeros
        assert 20 in numeros

    def test_faltantes_de_un_usuario_no_se_mezclan_con_los_de_otro(self, client, token_user1, token_user2):
        """Los faltantes de user1 no aparecen en la lista de user2 y viceversa."""
        client.post(ENDPOINT, json={"numero_figurita": 11}, headers={"X-User-Token": token_user1})
        client.post(ENDPOINT, json={"numero_figurita": 22}, headers={"X-User-Token": token_user2})

        faltantes_user1 = client.get(ENDPOINT, headers={"X-User-Token": token_user1}).json()["faltantes"]
        faltantes_user2 = client.get(ENDPOINT, headers={"X-User-Token": token_user2}).json()["faltantes"]

        assert len(faltantes_user1) == 1
        assert faltantes_user1[0]["numero_figurita"] == 11

        assert len(faltantes_user2) == 1
        assert faltantes_user2[0]["numero_figurita"] == 22

    def test_listar_devuelve_usuario_id_correcto(self, client, token_user1):
        """El campo usuario_id en la respuesta coincide con el usuario autenticado."""
        client.post(ENDPOINT, json={"numero_figurita": 5}, headers={"X-User-Token": token_user1})

        resp = client.get(ENDPOINT, headers={"X-User-Token": token_user1})

        assert resp.json()["usuario_id"] == 1  # user1 tiene id=1


# ----------------
# No duplicados
# ----------------

class TestFaltanteDuplicado:

    def test_registrar_mismo_numero_dos_veces_devuelve_409(self, client, token_user1):
        """No se puede registrar el mismo número de figurita como faltante dos veces."""
        client.post(ENDPOINT, json={"numero_figurita": 42}, headers={"X-User-Token": token_user1})

        resp = client.post(ENDPOINT, json={"numero_figurita": 42}, headers={"X-User-Token": token_user1})

        assert resp.status_code == 409 # Datos duplicados

    def test_mismo_numero_puede_ser_faltante_de_dos_usuarios_distintos(self, client, token_user1, token_user2):
        """El mismo número de figurita puede ser faltante de diferentes usuarios sin conflicto."""
        resp1 = client.post(ENDPOINT, json={"numero_figurita": 7}, headers={"X-User-Token": token_user1})
        resp2 = client.post(ENDPOINT, json={"numero_figurita": 7}, headers={"X-User-Token": token_user2})

        assert resp1.status_code == 201
        assert resp2.status_code == 201


# --------------------------------
# Validaciones de campos del body
# --------------------------------

class TestValidacionCampos:

    def test_numero_figurita_es_requerido(self, client, token_user1):
        """Omitir numero_figurita devuelve 422."""
        resp = client.post(
            ENDPOINT,
            json={"equipo": "Argentina"},
            headers={"X-User-Token": token_user1}
        )

        assert resp.status_code == 422

    def test_numero_figurita_no_puede_ser_cero(self, client, token_user1):
        """numero_figurita debe ser >= 1. Enviar 0 devuelve 422."""
        resp = client.post(
            ENDPOINT,
            json={"numero_figurita": 0},
            headers={"X-User-Token": token_user1}
        )

        assert resp.status_code == 422

    def test_numero_figurita_no_puede_ser_negativo(self, client, token_user1):
        """numero_figurita no puede ser negativo. Devuelve 422."""
        resp = client.post(
            ENDPOINT,
            json={"numero_figurita": -1},
            headers={"X-User-Token": token_user1}
        )

        assert resp.status_code == 422

    def test_body_vacio_devuelve_422(self, client, token_user1):
        """Enviar un body vacío devuelve 422."""
        resp = client.post(ENDPOINT, json={}, headers={"X-User-Token": token_user1})

        assert resp.status_code == 422
