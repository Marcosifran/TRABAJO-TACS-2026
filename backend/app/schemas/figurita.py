from pydantic import BaseModel, Field
from enum import Enum

'''
Esquemas para la creación y respuesta de las figuritas.
'''

class TipoIntercambio(str, Enum):
    INTERCAMBIO_DIRECTO = "intercambio_directo"
    SUBASTA = "subasta"

class FiguritaCreate(BaseModel):
    # Con ge se valida que el número sea mayor o igual a 1.
    numero: int = Field(..., ge=1, description="Número de figurita")
    equipo: str = Field(..., min_length=1, description="Selección, equipo o categoría")
    jugador: str = Field(..., min_length=1, description="Jugador o descripción de la figurita")
    cantidad: int = Field(..., ge=1, description="Cantidad disponible")
    tipo_intercambio: TipoIntercambio = Field(..., description="Modalidad de intercambio: intercambio_directo o subasta")

class FiguritaResponse(FiguritaCreate):
    id: int
    usuario_id: int

class SugerenciaResponse(BaseModel): #Representa una sugerencia de intercambio
    figurita: FiguritaResponse
    ofrecida_por: str
    cubre_tu_faltante: int
