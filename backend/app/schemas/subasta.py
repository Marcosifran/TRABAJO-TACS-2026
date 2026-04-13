from pydantic import BaseModel, Field

class SubastaCreate(BaseModel):
    figurita_id: int = Field(..., description="ID de la figurita que se pondrá en subasta")

class SubastaResponse(BaseModel):
    id: int
    figurita_id: int
    usuario_id: int
    estado: str = Field(..., description="Estado de la subasta")
