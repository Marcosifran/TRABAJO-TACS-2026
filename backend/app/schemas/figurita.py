from pydantic import BaseModel, Field
from enum import Enum

'''
Esquemas para la creación y respuesta de las figuritas.
'''


class FiguritaCreate(BaseModel):
    numero: int = Field(..., ge=1, description="Número de figurita")
    equipo: str = Field(..., min_length=1, description="Selección, equipo o categoría")
    jugador: str = Field(..., min_length=1, description="Jugador o descripción de la figurita")
    cantidad: int = Field(..., ge=1, description="Cantidad disponible")
class FiguritaResponse(FiguritaCreate):
    id: int
    usuario_id: int

class SugerenciaResponse(BaseModel): #Representa una sugerencia de intercambio
    figurita: FiguritaResponse
    ofrecida_por: str
    cubre_tu_faltante: int
