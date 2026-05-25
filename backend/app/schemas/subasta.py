from pydantic import BaseModel, Field
import datetime as dt

class SubastaCreate(BaseModel):
    figurita_id: str = Field(..., description="ID de la publicación que se pondrá en subasta")
    inicio: dt.datetime = Field(..., description="Fecha de inicio de la subasta")
    fin: dt.datetime = Field(..., description="Fecha de fin de la subasta")

class SubastaResponse(BaseModel):
    id: str
    figurita_id: str
    usuario_id: int
    estado: str = Field(..., description="Estado de la subasta")
