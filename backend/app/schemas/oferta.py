from pydantic import BaseModel, Field

class OfertaCreate(BaseModel):
    figuritas_ofrecidas: list[int] = Field(..., description="ID de las figuritas que se va a ofertar")


class OfertaDecision(BaseModel):
    estado: str = Field(..., description="Decisión sobre la oferta: 'aceptada' o 'rechazada'")