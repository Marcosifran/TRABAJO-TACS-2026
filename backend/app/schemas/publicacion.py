from pydantic import BaseModel, Field
from enum import Enum


class TipoIntercambio(str, Enum):
    """Enum para representar los tipos de intercambio disponibles."""
    INTERCAMBIO_DIRECTO = "intercambio_directo"
    SUBASTA = "subasta"


class PublicacionCreate(BaseModel):
    """Datos para poner una figurita del álbum en intercambio."""
    figurita_personal_id: str = Field(..., description="ID de la figurita del álbum que se está ofreciendo")
    tipo_intercambio: TipoIntercambio = Field(..., description="Tipo de intercambio que se desea realizar", alias="tipo")
    cantidad_disponible: int = Field(..., ge=1, description="Cantidad de figuritas disponibles para intercambio")

    model_config = {"populate_by_name": True}


class PublicacionResponse(BaseModel):
    """Respuesta al consultar una publicacion, incluye datos de la oferta mas la info de la figurita."""
    id: str
    usuario_id: int
    figurita_personal_id: str
    tipo_intercambio: TipoIntercambio
    cantidad_disponible: int
    numero: int
    equipo: str
    jugador: str


class SugerenciaResponse(BaseModel):
    """Representa una sugerencia automatica de intercambio desde una publicacion de otro usuario."""
    publicacion: PublicacionResponse
    ofrecida_por: str
    cubre_tu_faltante: int
