from pydantic import BaseModel, Field, field_validator
from enum import Enum


class EstadoIntercambio(str, Enum):
    PENDIENTE = "pendiente"
    ACEPTADO = "aceptado"
    RECHAZADO = "rechazado"


class EstadoRespuestaIntercambio(str, Enum):
    ACEPTADO = "aceptado"
    RECHAZADO = "rechazado"


class IntercambioCreate(BaseModel):
    figuritas_ofrecidas_numero: list[int] = Field(..., min_length=1, description="Numeros de las figuritas que se ofrecen")
    figurita_solicitada_numero: int = Field(..., ge=1, description="Numero de la figurita que se solicita")
    solicitado_a_id: int = Field(..., description="ID del usuario al que se propone el intercambio")

    @field_validator("figuritas_ofrecidas_numero")
    @classmethod
    def sin_repetidos(cls, v: list[int]) -> list[int]:
        if len(v) != len(set(v)):
            raise ValueError("No podés repetir figuritas en la oferta")
        return v


class IntercambioDecision(BaseModel):
    estado: EstadoRespuestaIntercambio = Field(..., description="Respuesta del receptor: aceptado o rechazado")


class IntercambioResponse(BaseModel):
    id: str
    propuesto_por: int
    solicitado_a: int
    figuritas_ofrecidas: list[int]
    figurita_solicitada: int
    estado: EstadoRespuestaIntercambio
