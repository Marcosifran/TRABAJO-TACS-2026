from pydantic import BaseModel, Field
from enum import Enum


class TipoIntercambio(str, Enum):
    """Enum para representar los tipos de intercambio disponibles."""
    INTERCAMBIO_DIRECTO = "intercambio_directo"
    SUBASTA = "subasta" 


class PublicacionCreate(BaseModel):
    """Datos para poner una figurita del álbum en intercambio, el album_id es qué figurita del álbum se está ofreciendo."""
    figurita_personal_id: int = Field(..., ge=1, description="ID de la figurita del álbum que se está ofreciendo")
    tipo_intercambio: TipoIntercambio = Field(..., description="Tipo de intercambio que se desea realizar")
    cantidad_disponible: int = Field(..., ge=1, description="Cantidad de figuritas disponibles para intercambio")


class PublicacionResponse(PublicacionCreate):
    """Respuesta al consultar una publicacion, incluye datos de la oferta mas la info de la figurita."""
    id: int
    usuario_id: int
    figurita_personal_id: int
    tipo_intercambio: TipoIntercambio
    cantidad_disponible: int
    
    # Información adicional de la figurita del álbum
    numero: int
    equipo: str
    jugador: str


class SugerenciaResponse(BaseModel):
    """Representa una sugerencia automatica de intercambio desde una publicacion de otro usuaraio que cubre una faltante de el usuario actual."""
    publicacion: PublicacionResponse
    ofrecida_por: str
    cubre_tu_faltante: int