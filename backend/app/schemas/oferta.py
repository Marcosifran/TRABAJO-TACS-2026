from enum import Enum

from pydantic import BaseModel, Field


class EstadoOferta(str, Enum):
    ACEPTADA = "aceptada"
    RECHAZADA = "rechazada"


class OfertaCreate(BaseModel):
    figuritas_ofrecidas: list[str] = Field(..., description="IDs de las figuritas del álbum que se van a ofertar")


class OfertaDecision(BaseModel):
    estado: EstadoOferta = Field(..., description="Decisión sobre la oferta: 'aceptada' o 'rechazada'")


class OfertaResponse(BaseModel):
    id: str
    subasta_id: str
    usuario_id: int
    ofrecidas: list[str]