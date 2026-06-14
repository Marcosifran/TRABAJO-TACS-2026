from pydantic import BaseModel, Field
from enum import Enum
import datetime as dt

class EstadoSubasta(str, Enum):
    ACTIVA = "activa"
    INACTIVA = "inactiva"
    FINALIZADA = "finalizada"
    CANCELADA = "cancelada"

class SubastaCreate(BaseModel):
    figurita_id: str = Field(..., description="ID de la publicación que se pondrá en subasta")
    inicio: dt.datetime = Field(..., description="Fecha de inicio de la subasta")
    fin: dt.datetime = Field(..., description="Fecha de fin de la subasta")

class SubastaResponse(BaseModel):
    id: str
    figurita_id: str
    usuario_id: int
    inicio: dt.datetime
    fin: dt.datetime
    estado: EstadoSubasta
    figurita_jugador: str | None = None
    figurita_equipo: str | None = None
    figurita_numero: int | None = None
    oferta_ganadora_id: str | None = None
