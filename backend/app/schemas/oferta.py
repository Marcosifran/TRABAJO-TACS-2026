from pydantic import BaseModel, Field

class OfertaCreate(BaseModel):
    figurita_ofrecida_id: int = Field(..., description="ID de la figurita que se va a intercambiar")