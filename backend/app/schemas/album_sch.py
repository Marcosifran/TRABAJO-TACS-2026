from pydantic import BaseModel, Field
from typing import Optional


class FiguritaAlbumCreate(BaseModel):
    """Esquema para representar una figurita de álbum."""

    numero: int = Field(..., ge=1, description="Número de la figurita en el álbum")
    equipo: str = Field(..., min_length=1, description="Nombre del equipo al que pertenece la figurita")
    jugador: str = Field(..., min_length=1, description="Nombre del jugador o descripción de la figurita")
    cantidad: int = Field(..., ge=1, description="Cantidad de esta figurita")


class FiguritaAlbumResponse(FiguritaAlbumCreate):
    """Esquema para la respuesta de una figurita de álbum, incluyendo el ID y el ID del usuario."""

    id: int
    usuario_id: int
    en_intercambio: bool = Field(default=False, description="Indica si la figurita está actualmente en intercambio")

    