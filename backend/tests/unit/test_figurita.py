"""
Tests unitarios — Figuritas

"""
import pytest
from unittest.mock import patch
from app.repositories import figurita_repo
from app.schemas.figurita import FiguritaCreate, TipoIntercambio


# ────────────────────
# Tests de repositorio
# ────────────────────

class TestFiguritaRepoCreate:

    def test_create_agrega_figurita_con_campos_correctos(self):
        """
        Caso de uso: Publicar figurita.
        create() debe persistir la figurita en memoria con todos sus campos originales.
        """
        figurita = FiguritaCreate(
            numero=10,
            equipo="Argentina",
            jugador="Messi",
            cantidad=2,
            tipo_intercambio=TipoIntercambio.INTERCAMBIO_DIRECTO,
        )

        resultado = figurita_repo.create(figurita, usuario_id=1)

        assert resultado["numero"] == 10
        assert resultado["equipo"] == "Argentina"
        assert resultado["jugador"] == "Messi"
        assert resultado["cantidad"] == 2
        assert resultado["tipo_intercambio"] == "intercambio_directo"

    def test_create_asigna_id_autoincrementado(self):
        """
        Caso de uso: Publicar figurita.
        El ID asignado debe ser secuencial (1 para la primera, 2 para la segunda, etc.).
        """
        figurita = FiguritaCreate(
            numero=1, equipo="Brasil", jugador="Vinicius",
            cantidad=1, tipo_intercambio=TipoIntercambio.SUBASTA,
        )

        primera = figurita_repo.create(figurita, usuario_id=1)
        segunda = figurita_repo.create(figurita, usuario_id=2)

        assert primera["id"] == 1
        assert segunda["id"] == 2

    def test_create_asocia_usuario_id(self):
        """
        Caso de uso: Publicar figurita.
        La figurita debe quedar vinculada al usuario que la publicó.
        """
        figurita = FiguritaCreate(
            numero=5, equipo="Francia", jugador="Mbappé",
            cantidad=1, tipo_intercambio=TipoIntercambio.INTERCAMBIO_DIRECTO,
        )

        resultado = figurita_repo.create(figurita, usuario_id=42)

        assert resultado["usuario_id"] == 42


# ────────────────────
# Tests de repositorio
# ────────────────────

class TestFiguritaRepoGetAllYDelete:

    def test_get_all_retorna_lista_vacia_si_no_hay_figuritas(self):
        """
        Caso de uso: Listar figuritas.
        get_all() sobre una DB vacía debe devolver una lista vacía.
        """
        assert figurita_repo.get_all() == []

    def test_get_all_retorna_todas_las_figuritas_creadas(self):
        """
        Caso de uso: Listar figuritas.
        get_all() debe devolver todas las figuritas en memoria.
        """
        figurita = FiguritaCreate(
            numero=1, equipo="Argentina", jugador="Messi",
            cantidad=1, tipo_intercambio=TipoIntercambio.INTERCAMBIO_DIRECTO,
        )
        figurita_repo.create(figurita, usuario_id=1)
        figurita_repo.create(figurita, usuario_id=2)

        assert len(figurita_repo.get_all()) == 2

    def test_delete_elimina_figurita_existente(self):
        """
        Caso de uso: Eliminar figurita.
        delete() debe eliminar la figurita y devolver True.
        """
        figurita = FiguritaCreate(
            numero=7, equipo="Italia", jugador="Del Piero",
            cantidad=1, tipo_intercambio=TipoIntercambio.INTERCAMBIO_DIRECTO,
        )
        creada = figurita_repo.create(figurita, usuario_id=1)

        resultado = figurita_repo.delete(creada["id"])

        assert resultado is True
        assert figurita_repo.get_all() == []

    def test_delete_retorna_false_si_no_existe(self):
        """
        Caso de uso: Eliminar figurita.
        delete() con un ID inexistente debe devolver False sin modificar en memoria.
        """
        resultado = figurita_repo.delete(999)

        assert resultado is False


# ────────────────────────────────────────────────
# Tests de repositorio — búsqueda por número y usuario
# ────────────────────────────────────────────────

class TestFiguritaRepoBuscarPorNumeroYUsuario:

    def _crear(self, numero, usuario_id):
        f = FiguritaCreate(
            numero=numero, equipo="Equipo", jugador="Jugador",
            cantidad=1, tipo_intercambio=TipoIntercambio.INTERCAMBIO_DIRECTO,
        )
        return figurita_repo.create(f, usuario_id=usuario_id)

    def test_retorna_figurita_cuando_numero_y_usuario_coinciden(self):
        """
        buscar_por_numero_y_usuario() debe devolver la figurita cuando el número
        y el usuario_id corresponden a una figurita existente.
        """
        self._crear(numero=10, usuario_id=1)

        resultado = figurita_repo.buscar_por_numero_y_usuario(10, 1)

        assert resultado is not None
        assert resultado["numero"] == 10
        assert resultado["usuario_id"] == 1

    def test_retorna_none_si_el_numero_pertenece_a_otro_usuario(self):
        """
        buscar_por_numero_y_usuario() debe devolver None si la figurita con ese número
        existe pero pertenece a un usuario distinto.
        """
        self._crear(numero=10, usuario_id=2)

        resultado = figurita_repo.buscar_por_numero_y_usuario(10, 1)

        assert resultado is None

    def test_retorna_none_si_el_numero_no_existe(self):
        """
        buscar_por_numero_y_usuario() debe devolver None si no hay ninguna figurita
        con ese número en la base de datos.
        """
        resultado = figurita_repo.buscar_por_numero_y_usuario(99, 1)

        assert resultado is None


# ────────────────────────────────────────────
# Tests de repositorio — figuritas por usuario
# ────────────────────────────────────────────

class TestFiguritaRepoGetByUsuarioId:

    def _crear(self, numero, usuario_id):
        f = FiguritaCreate(
            numero=numero, equipo="Equipo", jugador="Jugador",
            cantidad=1, tipo_intercambio=TipoIntercambio.INTERCAMBIO_DIRECTO,
        )
        return figurita_repo.create(f, usuario_id=usuario_id)

    def test_retorna_solo_las_figuritas_del_usuario(self):
        """
        get_by_usuario_id() debe devolver únicamente las figuritas publicadas
        por el usuario indicado, ignorando las de otros usuarios.
        """
        self._crear(numero=1, usuario_id=1)
        self._crear(numero=2, usuario_id=1)
        self._crear(numero=3, usuario_id=2)

        resultado = figurita_repo.get_by_usuario_id(1)

        assert len(resultado) == 2
        assert all(f["usuario_id"] == 1 for f in resultado)

    def test_retorna_lista_vacia_si_el_usuario_no_tiene_figuritas(self):
        """
        get_by_usuario_id() debe devolver lista vacía si el usuario no publicó nada.
        """
        resultado = figurita_repo.get_by_usuario_id(99)

        assert resultado == []


# ───────────────────────────────
# Tests de repositorio — búsqueda
# ───────────────────────────────

class TestFiguritaRepoBuscar:

    def _crear(self, numero, equipo, jugador, usuario_id=1):
        f = FiguritaCreate(
            numero=numero, equipo=equipo, jugador=jugador,
            cantidad=1, tipo_intercambio=TipoIntercambio.INTERCAMBIO_DIRECTO,
        )
        return figurita_repo.create(f, usuario_id=usuario_id)

    def test_buscar_sin_filtros_retorna_todas(self):
        """
        Caso de uso: Buscar figuritas.
        Sin filtros, buscar() devuelve todas las figuritas disponibles.
        """
        self._crear(1, "Argentina", "Messi")
        self._crear(2, "Brasil", "Vinicius")

        resultado = figurita_repo.buscar(None, None, None)

        assert len(resultado) == 2

    def test_buscar_por_numero_exacto(self):
        """
        Caso de uso: Buscar figuritas por número.
        buscar(numero=1) solo devuelve figuritas con ese número exacto.
        """
        self._crear(1, "Argentina", "Messi")
        self._crear(2, "Brasil", "Neymar")

        resultado = figurita_repo.buscar(1, None, None)

        assert len(resultado) == 1
        assert resultado[0]["numero"] == 1

    def test_buscar_por_equipo_parcial_case_insensitive(self):
        """
        Caso de uso: Buscar figuritas por equipo.
        La búsqueda por equipo es parcial y no distingue mayúsculas/minúsculas.
        """
        self._crear(1, "Argentina", "Messi")
        self._crear(2, "Francia", "Mbappé")

        resultado = figurita_repo.buscar(None, "argen", None)

        assert len(resultado) == 1
        assert resultado[0]["equipo"] == "Argentina"

    def test_buscar_por_jugador_parcial(self):
        """
        Caso de uso: Buscar figuritas por jugador.
        La búsqueda por jugador es parcial: 'mess' encuentra 'Messi'.
        """
        self._crear(1, "Argentina", "Messi")
        self._crear(2, "Brasil", "Vinicius")

        resultado = figurita_repo.buscar(None, None, "mess")

        assert len(resultado) == 1
        assert resultado[0]["jugador"] == "Messi"

    def test_buscar_numero_inexistente_retorna_lista_vacia(self):
        """
        Caso de uso: Buscar figuritas.
        Si ninguna figurita cumple el filtro, devuelve lista vacía.
        """
        self._crear(1, "Argentina", "Messi")

        resultado = figurita_repo.buscar(99, None, None)

        assert resultado == []


# ──────────────────────────────────
# Tests de repositorio — sugerencias
# ──────────────────────────────────

class TestFiguritaRepoGetSugerencias:

    def _crear(self, numero, usuario_id):
        f = FiguritaCreate(
            numero=numero, equipo="Equipo", jugador="Jugador",
            cantidad=1, tipo_intercambio=TipoIntercambio.INTERCAMBIO_DIRECTO,
        )
        return figurita_repo.create(f, usuario_id=usuario_id)

    def test_retorna_figuritas_de_otros_usuarios_que_cubren_faltantes(self):
        """
        Caso de uso: Sugerencias de intercambio.
        Solo deben aparecer figuritas publicadas por otros usuarios que coincidan con los números faltantes.
        """
        self._crear(numero=10, usuario_id=2)  # otro usuario tiene la #10
        self._crear(numero=5,  usuario_id=2)  # otro usuario tiene la #5

        resultado = figurita_repo.get_sugerencias(numeros_faltantes=[10], usuario_id=1)

        assert len(resultado) == 1
        assert resultado[0]["numero"] == 10

    def test_excluye_figuritas_del_propio_usuario(self):
        """
        Caso de uso: Sugerencias de intercambio.
        No tiene sentido sugerir una figurita que el propio usuario ya publicó.
        """
        self._crear(numero=10, usuario_id=1)  # el propio usuario tiene la #10

        resultado = figurita_repo.get_sugerencias(numeros_faltantes=[10], usuario_id=1)

        assert resultado == []

    def test_retorna_lista_vacia_si_nadie_tiene_los_faltantes(self):
        """
        Caso de uso: Sugerencias de intercambio.
        Si ningún otro usuario publicó figuritas que cubran los faltantes, devuelve vacío.
        """
        self._crear(numero=99, usuario_id=2)

        resultado = figurita_repo.get_sugerencias(numeros_faltantes=[10, 20], usuario_id=1)

        assert resultado == []


# ─────────────────
# Tests de servicio
# ─────────────────

from app.services import figurita_service

class TestFiguritaServiceDelegacion:

    def test_publicar_llama_a_repo_create(self):
        """
        Caso de uso: Publicar figurita.
        figurita_service.publicar() debe delegar en figurita_repo.create() y retornar su resultado.
        """
        figurita = FiguritaCreate(
            numero=1, equipo="Argentina", jugador="Messi",
            cantidad=1, tipo_intercambio=TipoIntercambio.INTERCAMBIO_DIRECTO,
        )
        fake_result = {"id": 1, "numero": 1, "usuario_id": 5}

        with patch("app.services.figurita_service.figurita_repo.create", return_value=fake_result) as mock_create:
            resultado = figurita_service.publicar(figurita, usuario_id=5)

        mock_create.assert_called_once_with(figurita, 5)
        assert resultado == fake_result

    def test_eliminar_llama_a_repo_delete(self):
        """
        Caso de uso: Eliminar figurita.
        figurita_service.eliminar() debe delegar en figurita_repo.delete() y retornar su resultado.
        """
        with patch("app.services.figurita_service.figurita_repo.delete", return_value=True) as mock_delete:
            resultado = figurita_service.eliminar(figurita_id=7)

        mock_delete.assert_called_once_with(7)
        assert resultado is True

    def test_buscar_llama_a_repo_buscar(self):
        """
        Caso de uso: Buscar figuritas.
        figurita_service.buscar() debe delegar en figurita_repo.buscar() con los mismos filtros.
        """
        fake_lista = [{"id": 1, "numero": 10}]

        with patch("app.services.figurita_service.figurita_repo.buscar", return_value=fake_lista) as mock_buscar:
            resultado = figurita_service.buscar(numero=10, equipo=None, jugador=None)

        mock_buscar.assert_called_once_with(10, None, None)
        assert resultado == fake_lista

    def test_sugerir_intercambios_retorna_vacio_si_usuario_no_tiene_faltantes(self):
        """
        Caso de uso: Sugerencias de intercambio.
        Si el usuario no tiene faltantes registrados, el servicio devuelve lista vacía
        sin consultar las figuritas disponibles.
        """
        with patch("app.services.figurita_service.usuario_repo.get_faltantes", return_value=[]) as mock_faltantes, \
             patch("app.services.figurita_service.figurita_repo.get_sugerencias") as mock_sugerencias:

            resultado = figurita_service.sugerir_intercambios(usuario_id=1)

        mock_faltantes.assert_called_once_with(1)
        mock_sugerencias.assert_not_called()
        assert resultado == []

    def test_listar_llama_a_repo_get_all(self):
        """
        Caso de uso: Listar figuritas.
        figurita_service.listar() debe delegar en figurita_repo.get_all() y retornar su resultado.
        """
        fake_lista = [{"id": 1, "numero": 10}]

        with patch("app.services.figurita_service.figurita_repo.get_all", return_value=fake_lista) as mock_get_all:
            resultado = figurita_service.listar()

        mock_get_all.assert_called_once()
        assert resultado == fake_lista

    def test_buscar_por_usuario_llama_a_repo_get_by_usuario_id(self):
        """
        Caso de uso: Ver mis figuritas publicadas.
        figurita_service.buscar_por_usuario() debe delegar en figurita_repo.get_by_usuario_id()
        y retornar su resultado.
        """
        fake_lista = [{"id": 1, "numero": 5, "usuario_id": 3}]

        with patch("app.services.figurita_service.figurita_repo.get_by_usuario_id", return_value=fake_lista) as mock_get:
            resultado = figurita_service.buscar_por_usuario(usuario_id=3)

        mock_get.assert_called_once_with(3)
        assert resultado == fake_lista

    def test_sugerir_intercambios_arma_sugerencias_con_info_del_oferente(self):
        """
        Caso de uso: Sugerencias de intercambio.
        Si el usuario tiene faltantes y otros usuarios tienen esas figuritas,
        el servicio debe devolver las sugerencias con la figurita, el nombre del oferente
        y el número que cubre el faltante.
        """
        faltantes = [{"usuario_id": 1, "numero_figurita": 10}]
        figurita_candidata = {
            "id": 5, "numero": 10, "equipo": "Brasil", "jugador": "Neymar",
            "cantidad": 1, "tipo_intercambio": "intercambio_directo", "usuario_id": 2,
        }
        oferente = {"id": 2, "nombre": "jeronimo"}

        with patch("app.services.figurita_service.usuario_repo.get_faltantes", return_value=faltantes), \
             patch("app.services.figurita_service.figurita_repo.get_sugerencias", return_value=[figurita_candidata]), \
             patch("app.services.figurita_service.usuario_repo.get_by_id", return_value=oferente):

            resultado = figurita_service.sugerir_intercambios(usuario_id=1)

        assert len(resultado) == 1
        sugerencia = resultado[0]
        assert sugerencia["figurita"] == figurita_candidata
        assert sugerencia["ofrecida_por"] == "jeronimo"
        assert sugerencia["cubre_tu_faltante"] == 10
