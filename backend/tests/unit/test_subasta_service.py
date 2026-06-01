"""
Unit tests — subasta_service.

Cubre _esta_activa y las validaciones de crear_subasta / ofertar.
Usa mocks para aislar de la base de datos; no necesita TestClient.
"""
import datetime as dt
import pytest
from unittest.mock import patch
from app.services import subasta_service
from app.schemas import SubastaCreate, EstadoSubasta, TipoIntercambio
from app.schemas import OfertaCreate
from app.domain.subasta import Subasta
from app.domain.publicacion import Publicacion
from app.domain.oferta import Oferta
from app.domain.errors import (
    DomainNotFoundError,
    DomainValidationError,
    DomainPermissionError,
    DomainConflictError,
)


def _ahora() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _subasta_create(figurita_id: str = "abc123", horas: int = 1) -> SubastaCreate:
    ahora = _ahora()
    return SubastaCreate(
        figurita_id=figurita_id,
        inicio=ahora - dt.timedelta(minutes=5),
        fin=ahora + dt.timedelta(hours=horas),
    )


def _subasta(**kwargs) -> Subasta:
    ahora = _ahora()
    defaults = {
        "id": "sub1",
        "figurita_id": "abc123",
        "usuario_id": 1,
        "inicio": ahora - dt.timedelta(minutes=5),
        "fin": ahora + dt.timedelta(hours=1),
        "estado": EstadoSubasta.ACTIVA,
    }
    defaults.update(kwargs)
    return Subasta(**defaults)


def _publicacion(**kwargs) -> Publicacion:
    defaults = {
        "id": "pub1",
        "usuario_id": 1,
        "figurita_personal_id": "fig1",
        "tipo_intercambio": TipoIntercambio.SUBASTA,
        "cantidad_disponible": 1,
        "numero": 10,
        "equipo": "ARG",
        "jugador": "Messi",
    }
    defaults.update(kwargs)
    return Publicacion(**defaults)


# ══════════════════════════════════════════
# _esta_activa
# ══════════════════════════════════════════

class TestEstaActiva:

    def test_retorna_false_si_estado_no_es_activa(self):
        subasta = _subasta(estado=EstadoSubasta.INACTIVA)
        assert subasta_service._esta_activa(subasta) is False

    def test_retorna_true_dentro_del_rango(self):
        subasta = _subasta(fin=_ahora() + dt.timedelta(hours=1))
        assert subasta_service._esta_activa(subasta) is True

    def test_retorna_false_si_subasta_vencida(self):
        subasta = _subasta(fin=_ahora() - dt.timedelta(hours=1))
        assert subasta_service._esta_activa(subasta) is False


# ══════════════════════════════════════════
# crear_subasta — validaciones
# ══════════════════════════════════════════

class TestCrearSubasta:

    def test_falla_si_publicacion_no_existe(self):
        with patch("app.services.subasta_service.publicacion_repo.get_by_id", return_value=None):
            with pytest.raises(DomainNotFoundError):
                subasta_service.crear_subasta(_subasta_create(), usuario_id=1)

    def test_falla_si_publicacion_pertenece_a_otro_usuario(self):
        pub = _publicacion(usuario_id=2)
        with patch("app.services.subasta_service.publicacion_repo.get_by_id", return_value=pub):
            with pytest.raises(DomainPermissionError):
                subasta_service.crear_subasta(_subasta_create(), usuario_id=1)

    def test_falla_si_tipo_no_es_subasta(self):
        pub = _publicacion(tipo_intercambio=TipoIntercambio.INTERCAMBIO_DIRECTO)
        with patch("app.services.subasta_service.publicacion_repo.get_by_id", return_value=pub):
            with pytest.raises(DomainValidationError):
                subasta_service.crear_subasta(_subasta_create(), usuario_id=1)

    def test_falla_si_ya_existe_subasta_activa_para_esa_figurita(self):
        pub = _publicacion()
        with patch("app.services.subasta_service.publicacion_repo.get_by_id", return_value=pub), \
             patch("app.services.subasta_service.subasta_repo.get_by_figurita", return_value=_subasta()):
            with pytest.raises(DomainConflictError):
                subasta_service.crear_subasta(_subasta_create(), usuario_id=1)


# ══════════════════════════════════════════
# ofertar — validaciones
# ══════════════════════════════════════════

class TestOfertar:

    def _oferta_create(self, ids: list[str] | None = None) -> OfertaCreate:
        return OfertaCreate(figuritas_ofrecidas=ids or ["fig1"])

    def test_falla_si_subasta_no_existe(self):
        with patch("app.services.subasta_service.subasta_repo.get_by_id", return_value=None):
            with pytest.raises(DomainNotFoundError):
                subasta_service.ofertar("sub1", self._oferta_create(), usuario_id=2)

    def test_falla_si_subasta_no_esta_activa(self):
        subasta = _subasta(fin=_ahora() - dt.timedelta(hours=1))
        with patch("app.services.subasta_service.subasta_repo.get_by_id", return_value=subasta):
            with pytest.raises(DomainValidationError):
                subasta_service.ofertar("sub1", self._oferta_create(), usuario_id=2)

    def test_falla_si_usuario_oferta_en_su_propia_subasta(self):
        subasta = _subasta()
        with patch("app.services.subasta_service.subasta_repo.get_by_id", return_value=subasta):
            with pytest.raises(DomainPermissionError):
                subasta_service.ofertar("sub1", self._oferta_create(), usuario_id=1)

    def test_falla_si_lista_de_figuritas_vacia(self):
        subasta = _subasta()
        with patch("app.services.subasta_service.subasta_repo.get_by_id", return_value=subasta), \
             patch("app.services.subasta_service.oferta_repo.get_by_auction", return_value=[]):
            with pytest.raises(DomainValidationError):
                subasta_service.ofertar("sub1", OfertaCreate(figuritas_ofrecidas=[]), usuario_id=2)

    def test_falla_si_usuario_ya_tiene_oferta_en_esa_subasta(self):
        subasta = _subasta()
        oferta_existente = [Oferta(id="o1", subasta_id="sub1", usuario_id=2, ofrecidas=["fig1"])]
        with patch("app.services.subasta_service.subasta_repo.get_by_id", return_value=subasta), \
             patch("app.services.subasta_service.oferta_repo.get_by_auction", return_value=oferta_existente):
            with pytest.raises(DomainConflictError):
                subasta_service.ofertar("sub1", self._oferta_create(), usuario_id=2)
