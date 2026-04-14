from pydantic import BaseModel, Field


class CalificacionCreate(BaseModel):
    puntuacion: int = Field(..., ge=1, le=5, description="Puntuación de 1 a 5")
    comentario: str | None = Field(
        default=None,
        max_length=500,
        description="Comentario opcional sobre la contraparte",
    )


class CalificacionResponse(BaseModel):
    id: int
    intercambio_id: int
    calificador_id: int
    calificado_id: int
    puntuacion: int
    comentario: str | None = None


class ReputacionResponse(BaseModel):
    usuario_id: int
    cantidad_calificaciones: int
    promedio_puntuacion: float | None = Field(
        default=None,
        description="Promedio de puntuaciones recibidas; null si no hay calificaciones",
    )
