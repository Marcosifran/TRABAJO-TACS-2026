from pydantic import BaseModel, Field


class _FaltanteFields(BaseModel):
    numero_figurita: int = Field(..., ge=1, description="Número de la figurita faltante")
    equipo: str | None = Field(default=None, description="Selección, equipo o categoría (opcional)")
    jugador: str | None = Field(default=None, description="Jugador o descripción (opcional)")


class FaltanteCreate(_FaltanteFields):
    """Request body para registrar un faltante."""


class FaltanteResponse(_FaltanteFields):
    """Response body para endpoints de faltantes."""

    id: str
    usuario_id: int


class FaltanteUpdate(BaseModel):
    """PATCH body — cada campo es opcional."""

    equipo: str | None = Field(default=None, min_length=1)
    jugador: str | None = Field(default=None, min_length=1)
