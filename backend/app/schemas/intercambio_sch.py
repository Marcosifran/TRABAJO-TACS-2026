from pydantic import BaseModel, Field
from enum import Enum

class EstadoRespuestaIntercambio(str, Enum):
    ACEPTADO = "aceptado"
    RECHAZADO = "rechazado"

class IntercambioCreate(BaseModel):
    figurita_ofrecida_numero: int = Field(..., description="Numero de la figurita que se ofrece")
    figurita_solicitada_numero: int = Field(..., description="Numero de la figurita que se solicita")
    solicitado_a_id: int = Field(..., description="ID del usuario al que se propone el intercambio")


class IntercambioDecision(BaseModel):
    estado: EstadoRespuestaIntercambio = Field(..., description="Respuesta del receptor: aceptado o rechazado")

class IntercambioResponse(IntercambioCreate):
    id: int
    propuesto_por: int
    estado: EstadoRespuestaIntercambio

