from pydantic import BaseModel


class FaltanteCreate(BaseModel):
    numero_figurita: int


class FaltanteResponse(FaltanteCreate):
    id: int
    usuario_id: int
