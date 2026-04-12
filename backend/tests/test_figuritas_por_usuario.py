"""
Tests de integración — Caso de uso: Buscar figuritas disponibles.

Cubre el endpoint GET /api/v1/usuarios/figuritas verificando:
- Dado el token del usuario devuelve las figuritas publicadas repetidas/faltantes
"""

import pytest

ENDPOINT1 = "/api/v1/figuritas"
ENDPOINT2 = "/api/v1/usuarios/figuritas"

# -----------------------
# Retorna figuritas publicadas
# -----------------------

class TestFiguritasPublicadas:

    def test_usuario_sin_figuritas(self, client, token_user2):
        """Sin figuritas publicadas la respuesta es una lista vacía."""
        resp = client.get(ENDPOINT2,headers={"X-User-Token": token_user2})

        assert resp.status_code == 200
        assert resp.json()["figuritas"] == []

    def test_usuario_con_figuritas(self, client, token_user1):
        """Usuario con figuritas publicadas."""
        figuritas = [
            {"numero": 10, "equipo": "Argentina", "jugador": "Lionel Messi",   "cantidad": 1, "tipo_intercambio": "intercambio_directo"},
            {"numero": 11, "equipo": "Argentina", "jugador": "Di María",        "cantidad": 2, "tipo_intercambio": "subasta"},
            {"numero": 7,  "equipo": "Brasil",    "jugador": "Vinicius Junior", "cantidad": 1, "tipo_intercambio": "intercambio_directo"},
            {"numero": 9,  "equipo": "Francia",   "jugador": "Kylian Mbappé",   "cantidad": 3, "tipo_intercambio": "subasta"},
            {"numero": 20, "equipo": "Alemania",  "jugador": "Thomas Müller",   "cantidad": 1, "tipo_intercambio": "intercambio_directo"},
        ]
    
        for figurita in figuritas:
            client.post(ENDPOINT1, json=figurita, headers={"X-User-Token": token_user1})
        resp = client.get(ENDPOINT2,headers={"X-User-Token": token_user1})

        assert resp.status_code == 200
        assert len(resp.json()["figuritas"]) == 5


