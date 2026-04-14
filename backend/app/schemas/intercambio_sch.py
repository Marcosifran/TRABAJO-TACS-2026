from pydantic import BaseModel, Field
from enum import Enum

class EstadoRespuestaIntercambio(str, Enum):
    ACEPTADO = "aceptado"
    RECHAZADO = "rechazado"

class IntercambioCreate(BaseModel):
    figuritas_ofrecidas_numero: list[int] = Field(..., description="Numeros de las figuritas que se ofrecen")
    figurita_solicitada_numero: int = Field(..., description="Numero de la figurita que se solicita")
    solicitado_a_id: int = Field(..., description="ID del usuario al que se propone el intercambio")


class IntercambioDecision(BaseModel):
    estado: EstadoRespuestaIntercambio = Field(..., description="Respuesta del receptor: aceptado o rechazado")


class IntercambioResponse(BaseModel):
    id: int
    propuesto_por: int
    solicitado_a: int
    figuritas_ofrecidas: list[int]
    figurita_solicitada: int
    estado: EstadoRespuestaIntercambio

