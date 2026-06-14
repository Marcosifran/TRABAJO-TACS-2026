from pydantic import BaseModel, Field

from app.schemas.publicacion import TipoIntercambio


class _FiguritaFields(BaseModel):
    numero: int = Field(..., ge=1, description="Número de figurita")
    equipo: str = Field(..., min_length=1, description="Selección, equipo o categoría")
    jugador: str = Field(..., min_length=1, description="Jugador o descripción de la figurita")
    cantidad: int = Field(..., ge=1, description="Cantidad disponible")
    tipo_intercambio: TipoIntercambio = Field(..., description="Modalidad de intercambio: intercambio_directo o subasta")


class FiguritaCreate(_FiguritaFields):
    """Request body para POST /figuritas/."""


class FiguritaResponse(_FiguritaFields):
    """Response body para endpoints de figuritas."""

    id: str
    usuario_id: int


class FiguritaUpdate(BaseModel):
    """PATCH body — cada campo es opcional."""

    equipo: str | None = Field(default=None, min_length=1)
    jugador: str | None = Field(default=None, min_length=1)
    cantidad: int | None = Field(default=None, ge=1)
