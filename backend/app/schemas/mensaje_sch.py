from pydantic import BaseModel, Field
import datetime as dt

class MensajeCreate(BaseModel):
    contenido: str = Field(..., min_length=1, max_length=1000, description="Texto del mensaje")

class MensajeResponse(BaseModel):
    id: int
    intercambio_id: int
    remitente_id: int
    contenido: str
    fecha_envio: dt.datetime

