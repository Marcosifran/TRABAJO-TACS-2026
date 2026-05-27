from pydantic import BaseModel, Field

class OfertaCreate(BaseModel):
    figuritas_ofrecidas: list[str] = Field(..., description="IDs de las figuritas del álbum que se van a ofertar")

class OfertaDecision(BaseModel):
    estado: str = Field(..., description="Decisión sobre la oferta: 'aceptada' o 'rechazada'")