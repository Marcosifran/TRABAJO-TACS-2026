from pydantic import BaseModel, Field
from enum import Enum


class TipoIntercambio(str, Enum):
    """Enum para representar los tipos de intercambio disponibles."""
    INTERCAMBIO_DIRECTO = "intercambio_directo"
    SUBASTA = "subasta"


class PublicacionCreate(BaseModel):
    """Datos para poner una figurita del álbum en intercambio."""
    figurita_personal_id: str = Field(..., description="ID de la figurita del álbum que se está ofreciendo")
    # Accept both JSON/body keys `tipo` (used in unit tests) and `tipo_intercambio` (used by API clients)
    tipo_intercambio: TipoIntercambio = Field(..., description="Tipo de intercambio que se desea realizar", alias="tipo")
    cantidad_disponible: int = Field(..., ge=1, description="Cantidad de figuritas disponibles para intercambio")

    # Use Pydantic v2 model_config to allow population by field name so code
    # and HTTP clients can send either `tipo_intercambio` (field name) or
    # `tipo` (alias used in older code/tests).
    model_config = {"populate_by_name": True}


class PublicacionResponse(BaseModel):
    """Respuesta al consultar una publicacion, incluye datos de la oferta mas la info de la figurita."""
    id: str
    usuario_id: int
    figurita_personal_id: str
    tipo_intercambio: TipoIntercambio
    cantidad_disponible: int

    # Información adicional de la figurita del álbum
    numero: int
    equipo: str
    jugador: str


class SugerenciaResponse(BaseModel):
    """Representa una sugerencia automatica de intercambio desde una publicacion de otro usuario."""
    publicacion: PublicacionResponse
    ofrecida_por: str
    cubre_tu_faltante: int
