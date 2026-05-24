import pytest

ENDPOINT_ADMIN_STATS = "/api/v1/admin/estadisticas"
ENDPOINT_ALBUM = "/api/v1/album"
ENDPOINT_PUBLICACIONES = "/api/v1/publicaciones"
ENDPOINT_SUBASTAS = "/api/v1/subastas"

class TestAdminEstadisticas:

    def test_estadistica_iniciales_con_db_limpia(self, client):
        """Al iniciar limpia la bd, los contadores base deberían ser 0"""
        response = client.get(ENDPOINT_ADMIN_STATS)

        assert response.status_code == 200
        data = response.json()

        assert data["usuarios"] >= 0
        assert data["figuritas_publicadas"] == 0
        assert data["intercambios_aceptados"] == 0
        assert data["subastas_activas"] == 0
        assert data["top_selecciones"] == []

    def test_estadisticas_reflejan_datos_nuevos(sef, client, token_user1):
        """Al agregar y publicar figuritas, se tienen que incrementar las estadisticas"""

        #agrego figurita a la seleccion de argentina al album de pruebas
        resp_album = client.post(
            ENDPOINT_ALBUM,
            json={
                "numero": 10, "equipo":"Argentina", "jugador":"Lionel Messi", "cantidad": 2
            },
            headers = {"X-User-Token": token_user1},
        )
        assert resp_album.status_code == 201
        album_id = resp_album.json()["id"]
        
        #publiar la figurita para intercambio directo
        resp_pub = client.post(
            ENDPOINT_PUBLICACIONES,
            json={
                "figurita_personal_id": album_id,
                "tipo_intercambio": "intercambio_directo",
                "cantidad_disponible": 1,
            },
            headers = {"X-User-Token": token_user1},
        )
        assert resp_pub.status_code == 201

        #uso el endpoint de administración
        resp_stats = client.get(ENDPOINT_ADMIN_STATS)
        assert resp_stats.status_code == 200

        #verifico que las estadísticas se hatan actualizado en MongoDB
        data = resp_stats.json()
        assert data["figuritas_publicadas"] == 1
        assert len(data["top_selecciones"]) == 1
        assert data["top_selecciones"][0]["seleccion"] == "Argentina"
        assert data["top_selecciones"][0]["cantidad"] == 1

    def test_estadisticas_reflejan_subasta_activa(self, client, token_user1):
        """Al agregar una subasta, las estadístias deben mostrar una subasta activa"""
        import datetime as dt

        #agrego figurita al álbum
        resp_album = client.post(
            ENDPOINT_ALBUM,
            json={
                "numero":10,
                "equipo":"Argentina",
                "jugador":"Lionel Messi",
                "cantidad": 1
            },
            headers={"X-User-Token":token_user1}
        )
        assert resp_album.status_code == 201
        album_id = resp_album.json()["id"]

        #publicar como tipo subasta
        resp_pub = client.post(
            ENDPOINT_PUBLICACIONES,
            json={
                "figurita_personal_id":album_id,
                "tipo_intercambio": "subasta",
                "cantidad_disponible": 1,
            },
            headers={"X-User-Token": token_user1},
        )
        assert resp_pub.status_code == 201
        pub_id = resp_pub.json()["id"]

        #creo la subasta
        ahora = dt.datetime.now(dt.timezone.utc)
        payload_subasta = {
            "figurita_id": pub_id,
            "inicio": (ahora - dt.timedelta(minutes=5)).isoformat(),
            "fin": (ahora + dt.timedelta(hours=2)).isoformat(),
        }
        resp_sub = client.post(
            ENDPOINT_SUBASTAS,
            json=payload_subasta,
            headers={"X-User-Token":token_user1}
        )
        assert resp_sub.status_code == 201

        #verifico que las estadísticas del admin reflejen la subasta activa
        resp_status = client.get(ENDPOINT_ADMIN_STATS)
        assert resp_status.status_code == 200

        data = resp_status.json()
        assert data["subastas_activas"] == 1