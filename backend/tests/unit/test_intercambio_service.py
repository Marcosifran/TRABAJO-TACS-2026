"""
Unit tests — intercambio_service.

Cubre las funciones de validación y la lógica de transferencia de figuritas.
Usa mocks para aislar de la base de datos; no necesita TestClient.
"""
import pytest
from unittest.mock import patch
from app.services import intercambio_service
from app.schemas import IntercambioCreate, TipoIntercambio
from app.domain.album import FiguritaAlbum
from app.domain.publicacion import Publicacion
from app.domain.errors import DomainValidationError, DomainNotFoundError


def _intercambio_create(**kwargs) -> IntercambioCreate:
    defaults = {
        "figuritas_ofrecidas_numero": [1, 2],
        "figurita_solicitada_numero": 3,
        "solicitado_a_id": 2,
    }
    defaults.update(kwargs)
    return IntercambioCreate(**defaults)


def _figurita_album(**kwargs) -> FiguritaAlbum:
    defaults = {
        "id": "fig1",
        "usuario_id": 1,
        "numero": 10,
        "equipo": "ARG",
        "jugador": "Messi",
        "cantidad": 1,
    }
    defaults.update(kwargs)
    return FiguritaAlbum(**defaults)


def _publicacion(**kwargs) -> Publicacion:
    defaults = {
        "id": "p1",
        "usuario_id": 1,
        "figurita_personal_id": "fig1",
        "tipo_intercambio": TipoIntercambio.INTERCAMBIO_DIRECTO,
        "cantidad_disponible": 1,
        "numero": 10,
        "equipo": "ARG",
        "jugador": "Messi",
    }
    defaults.update(kwargs)
    return Publicacion(**defaults)


# ══════════════════════════════════════════
# validar_intercambio - misma figurita
# ══════════════════════════════════════════

class TestValidarIntercambioMismaFigurita:

    @patch("app.services.intercambio_service.validar_usuario_destino")
    @patch("app.services.intercambio_service.obtener_publicaciones_para_intercambio")
    @patch("app.services.intercambio_service.album_repo.get_by_user")
    @patch("app.services.intercambio_service.validar_cantidad_disponible")
    def test_falla_si_solicitada_es_la_misma_figurita_exacta(
        self, mock_cant, mock_get_user, mock_get_pubs, mock_val_dest
    ):
        pub_solicitada = _publicacion(numero=10, equipo="ARG", jugador="Messi")
        
        intercambio = _intercambio_create(
            figuritas_ofrecidas_numero=[10],
            figurita_solicitada_numero=10,
        )
        
        fig_ofrecida = _figurita_album(numero=10, equipo="ARG", jugador="Messi")
        
        mock_get_pubs.return_value = ([], pub_solicitada)
        mock_get_user.return_value = [fig_ofrecida]
        
        with pytest.raises(DomainValidationError) as exc:
            intercambio_service.validar_intercambio(intercambio, usuario_id=1)
        assert "La figurita solicitada no puede estar incluida entre las ofrecidas" in str(exc.value)

    @patch("app.services.intercambio_service.validar_usuario_destino")
    @patch("app.services.intercambio_service.obtener_publicaciones_para_intercambio")
    @patch("app.services.intercambio_service.album_repo.get_by_user")
    @patch("app.services.intercambio_service.validar_cantidad_disponible")
    def test_pasa_si_mismo_numero_pero_diferente_figurita(
        self, mock_cant, mock_get_user, mock_get_pubs, mock_val_dest
    ):
        pub_solicitada = _publicacion(numero=10, equipo="BRA", jugador="Neymar")
        
        intercambio = _intercambio_create(
            figuritas_ofrecidas_numero=[10],
            figurita_solicitada_numero=10,
        )
        
        fig_ofrecida = _figurita_album(numero=10, equipo="ARG", jugador="Messi")
        
        mock_get_pubs.return_value = ([], pub_solicitada)
        mock_get_user.return_value = [fig_ofrecida]
        
        intercambio_service.validar_intercambio(intercambio, usuario_id=1)


# ══════════════════════════════════════════
# validar_usuario_destino
# ══════════════════════════════════════════

class TestValidarUsuarioDestino:

    def test_falla_si_se_propone_a_si_mismo(self):
        intercambio = _intercambio_create(solicitado_a_id=1)
        with pytest.raises(DomainValidationError):
            intercambio_service.validar_usuario_destino(intercambio, usuario_id=1)

    def test_falla_si_destinatario_no_existe(self):
        intercambio = _intercambio_create(solicitado_a_id=99)
        with patch("app.services.intercambio_service.usuario_repo.get_by_id", return_value=None):
            with pytest.raises(DomainNotFoundError):
                intercambio_service.validar_usuario_destino(intercambio, usuario_id=1)

    def test_pasa_si_destinatario_existe_y_es_distinto(self):
        intercambio = _intercambio_create(solicitado_a_id=2)
        with patch("app.services.intercambio_service.usuario_repo.get_by_id", return_value={"id": 2}):
            intercambio_service.validar_usuario_destino(intercambio, usuario_id=1)


# ══════════════════════════════════════════
# validar_cantidad_disponible
# ══════════════════════════════════════════

class TestValidarCantidadDisponible:

    def test_falla_si_ofrecida_sin_stock(self):
        with pytest.raises(DomainValidationError):
            intercambio_service.validar_cantidad_disponible(
                [_publicacion(cantidad_disponible=0)],
                _publicacion(cantidad_disponible=1),
            )

    def test_falla_si_solicitada_sin_stock(self):
        with pytest.raises(DomainValidationError):
            intercambio_service.validar_cantidad_disponible(
                [_publicacion(cantidad_disponible=1)],
                _publicacion(cantidad_disponible=0),
            )

    def test_pasa_si_todas_tienen_stock(self):
        intercambio_service.validar_cantidad_disponible(
            [_publicacion(cantidad_disponible=2), _publicacion(cantidad_disponible=1)],
            _publicacion(cantidad_disponible=1),
        )


# ══════════════════════════════════════════
# _transferir_figurita
# ══════════════════════════════════════════

class TestTransferirFigurita:

    def test_elimina_figurita_del_cedente_cuando_queda_sin_stock(self):
        fig_cedente = _figurita_album(cantidad=1)

        with patch("app.services.intercambio_service.album_repo.get_by_number_and_user", side_effect=[fig_cedente, None]), \
             patch("app.services.intercambio_service.album_repo.adjust_cantidad", return_value=None) as mock_adjust, \
             patch("app.services.intercambio_service.publicacion_repo.get_all", return_value=[]), \
             patch("app.services.intercambio_service.album_repo.create"), \
             patch("app.services.intercambio_service.faltante_repo.remove_missing"):

            intercambio_service._transferir_figurita(10, de_usuario_id=1, a_usuario_id=2)

        mock_adjust.assert_called_once_with("fig1", -1)

    def test_crea_entrada_en_album_del_receptor_si_no_la_tiene(self):
        fig_cedente = _figurita_album(cantidad=1)

        with patch("app.services.intercambio_service.album_repo.get_by_number_and_user", side_effect=[fig_cedente, None]), \
             patch("app.services.intercambio_service.album_repo.adjust_cantidad", return_value=None), \
             patch("app.services.intercambio_service.publicacion_repo.get_all", return_value=[]), \
             patch("app.services.intercambio_service.album_repo.create") as mock_create, \
             patch("app.services.intercambio_service.faltante_repo.remove_missing"):

            intercambio_service._transferir_figurita(10, de_usuario_id=1, a_usuario_id=2)

        mock_create.assert_called_once()

    def test_elimina_faltante_del_receptor(self):
        fig_cedente = _figurita_album(cantidad=1)

        with patch("app.services.intercambio_service.album_repo.get_by_number_and_user", side_effect=[fig_cedente, None]), \
             patch("app.services.intercambio_service.album_repo.adjust_cantidad", return_value=None), \
             patch("app.services.intercambio_service.publicacion_repo.get_all", return_value=[]), \
             patch("app.services.intercambio_service.album_repo.create"), \
             patch("app.services.intercambio_service.faltante_repo.remove_missing") as mock_remove:

            intercambio_service._transferir_figurita(10, de_usuario_id=1, a_usuario_id=2)

        mock_remove.assert_called_once_with(2, 10)
