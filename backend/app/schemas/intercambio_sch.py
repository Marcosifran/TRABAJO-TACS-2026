from pydantic import BaseModel, Field


class IntercambioCreate(BaseModel):
    figurita_ofrecida_numero: int = Field(..., description="Numero de la figurita que se ofrece")
    figurita_solicitada_numero: int = Field(..., description="Numero de la figurita que se solicita")
    solicitado_a_id: int = Field(..., description="ID del usuario al que se propone el intercambio")

class IntercambioResponse(IntercambioCreate):
    id: int
    propuesto_por: int
    estado: str

