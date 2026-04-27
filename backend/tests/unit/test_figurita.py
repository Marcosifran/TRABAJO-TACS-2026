"""
Tests unitarios — Álbum personal y Publicaciones

Testea directamente los repositorios y services sin pasar por HTTP.
Cubre:
- album_repo: create, get_by_id, get_by_usuario, buscar, delete, update_cantidad
- publicacion_repo: create, get_by_id, get_by_usuario, get_by_figurita_personal, buscar, delete
- album_service: agregar, listar, eliminar, campo en_intercambio
- publicacion_service: publicar, listar, retirar, sugerencias
"""

import pytest
from unittest.mock import patch

from app.repositories import album_repo, publicacion_repo
from app.schemas.album_sch import FiguritaAlbumCreate
from app.schemas.publicacion_sch import PublicacionCreate, TipoIntercambio


# ══════════════════════════════════════════
# Helpers para no repetir código en los tests
# ══════════════════════════════════════════

def _album_create(numero=10, equipo="Argentina", jugador="Messi", cantidad=2):
    return FiguritaAlbumCreate(
        numero=numero,
        equipo=equipo,
        jugador=jugador,
        cantidad=cantidad,
    )

def _publicacion_create(figurita_personal_id=1, tipo=TipoIntercambio.INTERCAMBIO_DIRECTO, cantidad=1):
    return PublicacionCreate(
        figurita_personal_id=figurita_personal_id,
        tipo_intercambio=tipo,
        cantidad_disponible=cantidad,
    )


# ══════════════════════════════════════════
# album_repo
# ══════════════════════════════════════════

class TestAlbumRepoCreate:

    def test_create_agrega_figurita_con_campos_correctos(self):
        """create() persiste la figurita con todos sus campos."""
        figurita = _album_create()

        resultado = album_repo.create(figurita, usuario_id=1)

        assert resultado["numero"] == 10
        assert resultado["equipo"] == "Argentina"
        assert resultado["jugador"] == "Messi"
        assert resultado["cantidad"] == 2
        assert resultado["usuario_id"] == 1

    def test_create_asigna_id_autoincrementado(self):
        """Los IDs asignados son secuenciales y únicos."""
        figurita = _album_create()

        primera = album_repo.create(figurita, usuario_id=1)
        segunda = album_repo.create(figurita, usuario_id=2)

        assert primera["id"] == 1
        assert segunda["id"] == 2

    def test_create_asocia_usuario_id(self):
        """La figurita queda vinculada al usuario que la agregó."""
        figurita = _album_create()

        resultado = album_repo.create(figurita, usuario_id=42)

        assert resultado["usuario_id"] == 42


class TestAlbumRepoGetYDelete:

    def test_get_all_retorna_lista_vacia_al_inicio(self):
        assert album_repo.get_all() == []

    def test_get_all_retorna_todas_las_figuritas(self):
        figurita = _album_create()
        album_repo.create(figurita, usuario_id=1)
        album_repo.create(figurita, usuario_id=2)

        assert len(album_repo.get_all()) == 2

    def test_get_by_id_retorna_figurita_correcta(self):
        figurita = _album_create(numero=7)
        creada = album_repo.create(figurita, usuario_id=1)

        resultado = album_repo.get_by_id(creada["id"])

        assert resultado is not None
        assert resultado["numero"] == 7

    def test_get_by_id_retorna_none_si_no_existe(self):
        assert album_repo.get_by_id(999) is None

    def test_get_by_usuario_retorna_solo_las_del_usuario(self):
        album_repo.create(_album_create(numero=1), usuario_id=1)
        album_repo.create(_album_create(numero=2), usuario_id=1)
        album_repo.create(_album_create(numero=3), usuario_id=2)

        resultado = album_repo.get_by_usuario(1)

        assert len(resultado) == 2
        assert all(f["usuario_id"] == 1 for f in resultado)

    def test_get_by_usuario_retorna_lista_vacia_si_no_tiene_figuritas(self):
        assert album_repo.get_by_usuario(99) == []

    def test_delete_elimina_figurita_existente(self):
        creada = album_repo.create(_album_create(), usuario_id=1)

        resultado = album_repo.delete(creada["id"])

        assert resultado is True
        assert album_repo.get_all() == []

    def test_delete_retorna_false_si_no_existe(self):
        assert album_repo.delete(999) is False


class TestAlbumRepoBuscar:

    def _crear(self, numero, equipo, jugador, usuario_id=1):
        return album_repo.create(
            _album_create(numero=numero, equipo=equipo, jugador=jugador),
            usuario_id=usuario_id,
        )

    def test_buscar_sin_filtros_retorna_todas(self):
        self._crear(1, "Argentina", "Messi")
        self._crear(2, "Brasil", "Vinicius")

        assert len(album_repo.buscar(None, None, None)) == 2

    def test_buscar_por_numero_exacto(self):
        self._crear(1, "Argentina", "Messi")
        self._crear(2, "Brasil", "Neymar")

        resultado = album_repo.buscar(1, None, None)

        assert len(resultado) == 1
        assert resultado[0]["numero"] == 1

    def test_buscar_por_equipo_parcial_case_insensitive(self):
        self._crear(1, "Argentina", "Messi")
        self._crear(2, "Francia", "Mbappé")

        resultado = album_repo.buscar(None, "argen", None)

        assert len(resultado) == 1
        assert resultado[0]["equipo"] == "Argentina"

    def test_buscar_por_jugador_parcial(self):
        self._crear(1, "Argentina", "Messi")
        self._crear(2, "Brasil", "Vinicius")

        resultado = album_repo.buscar(None, None, "mess")

        assert len(resultado) == 1
        assert resultado[0]["jugador"] == "Messi"

    def test_buscar_filtra_por_usuario_si_se_pasa(self):
        self._crear(1, "Argentina", "Messi", usuario_id=1)
        self._crear(2, "Brasil", "Vinicius", usuario_id=2)

        resultado = album_repo.buscar(None, None, None, usuario_id=1)

        assert len(resultado) == 1
        assert resultado[0]["usuario_id"] == 1

    def test_buscar_numero_inexistente_retorna_lista_vacia(self):
        self._crear(1, "Argentina", "Messi")

        assert album_repo.buscar(99, None, None) == []


class TestAlbumRepoGetPorNumeroYUsuario:

    def test_retorna_figurita_cuando_coinciden(self):
        album_repo.create(_album_create(numero=10), usuario_id=1)

        resultado = album_repo.get_por_numero_y_usuario(10, 1)

        assert resultado is not None
        assert resultado["numero"] == 10

    def test_retorna_none_si_pertenece_a_otro_usuario(self):
        album_repo.create(_album_create(numero=10), usuario_id=2)

        assert album_repo.get_por_numero_y_usuario(10, 1) is None

    def test_retorna_none_si_numero_no_existe(self):
        assert album_repo.get_por_numero_y_usuario(99, 1) is None


# ══════════════════════════════════════════
# publicacion_repo
# ══════════════════════════════════════════

class TestPublicacionRepoCreate:

    def test_create_guarda_publicacion_con_datos_aplanados(self):
        """create() guarda los datos de la figurita aplanados en la publicación."""
        pub = _publicacion_create(figurita_personal_id=1)

        resultado = publicacion_repo.create(
            publicacion=pub,
            usuario_id=1,
            numero=10,
            equipo="Argentina",
            jugador="Messi",
        )

        assert resultado["numero"] == 10
        assert resultado["equipo"] == "Argentina"
        assert resultado["jugador"] == "Messi"
        assert resultado["figurita_personal_id"] == 1
        assert resultado["tipo_intercambio"] == "intercambio_directo"
        assert resultado["usuario_id"] == 1

    def test_create_asigna_id_autoincrementado(self):
        pub = _publicacion_create()

        primera = publicacion_repo.create(pub, usuario_id=1, numero=1, equipo="A", jugador="J1")
        segunda = publicacion_repo.create(pub, usuario_id=2, numero=2, equipo="B", jugador="J2")

        assert primera["id"] == 1
        assert segunda["id"] == 2


class TestPublicacionRepoGetYDelete:

    def _crear(self, figurita_personal_id=1, usuario_id=1, numero=10, tipo=TipoIntercambio.INTERCAMBIO_DIRECTO):
        return publicacion_repo.create(
            _publicacion_create(figurita_personal_id=figurita_personal_id, tipo=tipo),
            usuario_id=usuario_id,
            numero=numero,
            equipo="Argentina",
            jugador="Messi",
        )

    def test_get_all_retorna_lista_vacia_al_inicio(self):
        assert publicacion_repo.get_all() == []

    def test_get_by_id_retorna_publicacion_correcta(self):
        creada = self._crear()

        resultado = publicacion_repo.get_by_id(creada["id"])

        assert resultado is not None
        assert resultado["id"] == creada["id"]

    def test_get_by_id_retorna_none_si_no_existe(self):
        assert publicacion_repo.get_by_id(999) is None

    def test_get_by_usuario_retorna_solo_las_del_usuario(self):
        self._crear(figurita_personal_id=1, usuario_id=1, numero=10)
        self._crear(figurita_personal_id=2, usuario_id=2, numero=20)

        resultado = publicacion_repo.get_by_usuario(1)

        assert len(resultado) == 1
        assert resultado[0]["usuario_id"] == 1

    def test_get_by_figurita_personal_retorna_publicacion_activa(self):
        self._crear(figurita_personal_id=5)

        resultado = publicacion_repo.get_by_figurita_personal(5)

        assert resultado is not None
        assert resultado["figurita_personal_id"] == 5

    def test_get_by_figurita_personal_retorna_none_si_no_esta_publicada(self):
        assert publicacion_repo.get_by_figurita_personal(99) is None

    def test_delete_elimina_publicacion_existente(self):
        creada = self._crear()

        resultado = publicacion_repo.delete(creada["id"])

        assert resultado is True
        assert publicacion_repo.get_all() == []

    def test_delete_retorna_false_si_no_existe(self):
        assert publicacion_repo.delete(999) is False


class TestPublicacionRepoBuscar:

    def _crear(self, numero, usuario_id=1, tipo=TipoIntercambio.INTERCAMBIO_DIRECTO):
        return publicacion_repo.create(
            _publicacion_create(tipo=tipo),
            usuario_id=usuario_id,
            numero=numero,
            equipo="Argentina",
            jugador="Messi",
        )

    def test_buscar_sin_filtros_retorna_todas(self):
        self._crear(1)
        self._crear(2, usuario_id=2)

        assert len(publicacion_repo.buscar(None, None, None)) == 2

    def test_buscar_excluye_publicaciones_del_usuario_si_se_pasa_usuario_id(self):
        self._crear(1, usuario_id=1)
        self._crear(2, usuario_id=2)

        resultado = publicacion_repo.buscar(None, None, None, usuario_id=1)

        assert len(resultado) == 1
        assert resultado[0]["usuario_id"] == 2

    def test_buscar_por_numero_exacto(self):
        self._crear(10)
        self._crear(20)

        resultado = publicacion_repo.buscar(10, None, None)

        assert len(resultado) == 1
        assert resultado[0]["numero"] == 10

    def test_buscar_por_tipo_intercambio(self):
        self._crear(1, tipo=TipoIntercambio.INTERCAMBIO_DIRECTO)
        self._crear(2, usuario_id=2, tipo=TipoIntercambio.SUBASTA)

        resultado = publicacion_repo.buscar(None, None, None, tipo_intercambio="intercambio_directo")

        assert len(resultado) == 1
        assert resultado[0]["tipo_intercambio"] == "intercambio_directo"


# ══════════════════════════════════════════
# album_service
# ══════════════════════════════════════════

from app.services import album_service

class TestAlbumService:

    def test_agregar_al_album_llama_a_repo_create(self):
        """agregar_al_album() delega en album_repo.create()."""
        figurita = _album_create()
        fake_result = {"id": 1, "numero": 10, "usuario_id": 1, "en_intercambio": False}

        with patch("app.services.album_service.album_repo.create", return_value=fake_result) as mock:
            resultado = album_service.agregar_al_album(figurita, usuario_id=1)

        mock.assert_called_once_with(figurita, 1)
        assert resultado == fake_result

    def test_listar_album_agrega_campo_en_intercambio(self):
        """
        listar_album() enriquece cada figurita con el campo en_intercambio.
        Si la figurita tiene publicación activa, en_intercambio es True.
        """
        figurita_en_repo = {"id": 1, "numero": 10, "usuario_id": 1}
        publicacion_activa = {"id": 1, "figurita_personal_id": 1}

        with patch("app.services.album_service.album_repo.get_by_usuario", return_value=[figurita_en_repo]), \
             patch("app.services.album_service.publicacion_repo.get_by_figurita_personal", return_value=publicacion_activa):

            resultado = album_service.listar_album(usuario_id=1)

        assert resultado[0]["en_intercambio"] is True

    def test_listar_album_en_intercambio_false_si_no_tiene_publicacion(self):
        figurita_en_repo = {"id": 1, "numero": 10, "usuario_id": 1}

        with patch("app.services.album_service.album_repo.get_by_usuario", return_value=[figurita_en_repo]), \
             patch("app.services.album_service.publicacion_repo.get_by_figurita_personal", return_value=None):

            resultado = album_service.listar_album(usuario_id=1)

        assert resultado[0]["en_intercambio"] is False

    def test_eliminar_falla_con_409_si_tiene_publicacion_activa(self):
        """No se puede eliminar una figurita que está publicada."""
        from fastapi import HTTPException

        figurita = {"id": 1, "usuario_id": 1, "numero": 10}
        publicacion = {"id": 1, "figurita_personal_id": 1}

        with patch("app.services.album_service.album_repo.get_by_id", return_value=figurita), \
             patch("app.services.album_service.publicacion_repo.get_by_figurita_personal", return_value=publicacion):

            with pytest.raises(HTTPException) as exc:
                album_service.eliminar_del_album(figurita_id=1, usuario_id=1)

        assert exc.value.status_code == 409

    def test_eliminar_retorna_none_si_no_es_duenio(self):
        figurita_de_otro = {"id": 1, "usuario_id": 99, "numero": 10}

        with patch("app.services.album_service.album_repo.get_by_id", return_value=figurita_de_otro), \
             patch("app.services.album_service.publicacion_repo.get_by_figurita_personal", return_value=None):

            resultado = album_service.eliminar_del_album(figurita_id=1, usuario_id=1)

        assert resultado is None

    def test_eliminar_retorna_false_si_no_existe(self):
        with patch("app.services.album_service.album_repo.get_by_id", return_value=None):
            resultado = album_service.eliminar_del_album(figurita_id=999, usuario_id=1)

        assert resultado is False


# ══════════════════════════════════════════
# publicacion_service
# ══════════════════════════════════════════

from app.services import publicacion_service

class TestPublicacionService:

    def test_publicar_falla_404_si_figurita_no_existe_en_album(self):
        from fastapi import HTTPException

        pub = _publicacion_create(figurita_personal_id=999)

        with patch("app.services.publicacion_service.album_repo.get_by_id", return_value=None):
            with pytest.raises(HTTPException) as exc:
                publicacion_service.publicar_figurita(pub, usuario_id=1)

        assert exc.value.status_code == 404

    def test_publicar_falla_403_si_figurita_no_pertenece_al_usuario(self):
        from fastapi import HTTPException

        pub = _publicacion_create(figurita_personal_id=1)
        figurita_de_otro = {"id": 1, "usuario_id": 99, "numero": 10, "cantidad": 1}

        with patch("app.services.publicacion_service.album_repo.get_by_id", return_value=figurita_de_otro):
            with pytest.raises(HTTPException) as exc:
                publicacion_service.publicar_figurita(pub, usuario_id=1)

        assert exc.value.status_code == 403

    def test_publicar_falla_409_si_ya_esta_publicada(self):
        from fastapi import HTTPException

        pub = _publicacion_create(figurita_personal_id=1)
        figurita = {"id": 1, "usuario_id": 1, "numero": 10, "cantidad": 2}
        publicacion_existente = {"id": 1}

        with patch("app.services.publicacion_service.album_repo.get_by_id", return_value=figurita), \
             patch("app.services.publicacion_service.publicacion_repo.get_by_figurita_personal", return_value=publicacion_existente):

            with pytest.raises(HTTPException) as exc:
                publicacion_service.publicar_figurita(pub, usuario_id=1)

        assert exc.value.status_code == 409

    def test_publicar_falla_400_si_cantidad_supera_album(self):
        from fastapi import HTTPException

        pub = _publicacion_create(figurita_personal_id=1, cantidad=5)
        figurita = {"id": 1, "usuario_id": 1, "numero": 10, "cantidad": 1}

        with patch("app.services.publicacion_service.album_repo.get_by_id", return_value=figurita), \
             patch("app.services.publicacion_service.publicacion_repo.get_by_figurita_personal", return_value=None):

            with pytest.raises(HTTPException) as exc:
                publicacion_service.publicar_figurita(pub, usuario_id=1)

        assert exc.value.status_code == 400

    def test_publicar_llama_a_repo_create_con_datos_aplanados(self):
        """publicar_figurita() crea la publicación con los datos de la figurita aplanados."""
        pub = _publicacion_create(figurita_personal_id=1, cantidad=1)
        figurita = {"id": 1, "usuario_id": 1, "numero": 10, "equipo": "Argentina", "jugador": "Messi", "cantidad": 2}
        fake_result = {"id": 1}

        with patch("app.services.publicacion_service.album_repo.get_by_id", return_value=figurita), \
             patch("app.services.publicacion_service.publicacion_repo.get_by_figurita_personal", return_value=None), \
             patch("app.services.publicacion_service.publicacion_repo.create", return_value=fake_result) as mock_create:

            publicacion_service.publicar_figurita(pub, usuario_id=1)

        mock_create.assert_called_once_with(
            publicacion=pub,
            usuario_id=1,
            numero=10,
            equipo="Argentina",
            jugador="Messi",
        )

    def test_retirar_retorna_none_si_no_es_duenio(self):
        publicacion_de_otro = {"id": 1, "usuario_id": 99}

        with patch("app.services.publicacion_service.publicacion_repo.get_by_id", return_value=publicacion_de_otro):
            resultado = publicacion_service.retirar_publicacion(publicacion_id=1, usuario_id=1)

        assert resultado is None

    def test_retirar_retorna_false_si_no_existe(self):
        with patch("app.services.publicacion_service.publicacion_repo.get_by_id", return_value=None):
            resultado = publicacion_service.retirar_publicacion(publicacion_id=999, usuario_id=1)

        assert resultado is False

    def test_obtener_sugerencias_retorna_vacio_si_no_hay_faltantes(self):
        """Sin faltantes registrados, no hay sugerencias posibles."""
        with patch("app.services.publicacion_service.usuario_repo.get_faltantes", return_value=[]) as mock_faltantes, \
             patch("app.services.publicacion_service.publicacion_repo.buscar") as mock_buscar:

            resultado = publicacion_service.obtener_sugerencias(usuario_id=1)

        mock_faltantes.assert_called_once_with(1)
        mock_buscar.assert_not_called()
        assert resultado == []

    def test_obtener_sugerencias_cruza_faltantes_con_publicaciones(self):
        """Con faltantes y publicaciones que coinciden, devuelve las sugerencias correctas."""
        faltantes = [{"numero_figurita": 10}]
        publicacion_candidata = {
            "id": 1, "numero": 10, "equipo": "Brasil",
            "jugador": "Neymar", "usuario_id": 2,
            "tipo_intercambio": "intercambio_directo",
        }
        oferente = {"id": 2, "nombre": "jeronimo"}

        with patch("app.services.publicacion_service.usuario_repo.get_faltantes", return_value=faltantes), \
             patch("app.services.publicacion_service.publicacion_repo.buscar", return_value=[publicacion_candidata]), \
             patch("app.services.publicacion_service.usuario_repo.get_by_id", return_value=oferente):

            resultado = publicacion_service.obtener_sugerencias(usuario_id=1)

        assert len(resultado) == 1
        assert resultado[0]["publicacion"] == publicacion_candidata
        assert resultado[0]["ofrecida_por"] == "jeronimo"
        assert resultado[0]["cubre_tu_faltante"] == 10