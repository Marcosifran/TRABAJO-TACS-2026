from pydantic import BaseModel, Field

class OfertaCreate(BaseModel):
    figuritas_ofrecidas: list[str] = Field(..., description="IDs de las figuritas del álbum que se van a ofertar")
