from pydantic import BaseModel, Field


class _FiguritaAlbumFields(BaseModel):
    numero: int = Field(..., ge=1, description="Número de la figurita en el álbum")
    equipo: str = Field(..., min_length=1, description="Nombre del equipo al que pertenece la figurita")
    jugador: str = Field(..., min_length=1, description="Nombre del jugador o descripción de la figurita")
    cantidad: int = Field(..., ge=1, description="Cantidad de esta figurita")


class FiguritaAlbumCreate(_FiguritaAlbumFields):
    """Request body para POST /album/."""


class FiguritaAlbumResponse(_FiguritaAlbumFields):
    """Response body para endpoints de álbum."""

    id: str
    usuario_id: int
    en_intercambio: bool = Field(default=False, description="Indica si la figurita está actualmente en intercambio")


class FiguritaAlbumUpdate(BaseModel):
    """PATCH body — cada campo es opcional."""

    equipo: str | None = Field(default=None, min_length=1)
    jugador: str | None = Field(default=None, min_length=1)
    cantidad: int | None = Field(default=None, ge=1)
