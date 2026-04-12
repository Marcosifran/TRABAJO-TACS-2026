from pydantic import BaseModel, Field
from typing import Optional


class FaltanteCreate(BaseModel):
    numero_figurita: int = Field(..., ge=1, description="Número de la figurita faltante")
    equipo: Optional[str] = Field(None, description="Selección, equipo o categoría (opcional)")
    jugador: Optional[str] = Field(None, description="Jugador o descripción (opcional)")


class FaltanteResponse(FaltanteCreate):
    id: int
    usuario_id: int

class FaltanteRegistradoResponse(BaseModel):
    mensaje: str
    data: FaltanteResponse

class ListarFaltantesResponse(BaseModel):
    usuario_id: int
    faltantes: list[FaltanteResponse]
