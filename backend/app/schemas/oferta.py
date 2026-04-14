from pydantic import BaseModel, Field

class OfertaCreate(BaseModel):
    figuritas_ofrecidas: list[int] = Field(..., description="ID de las figuritas que se va a ofertar")