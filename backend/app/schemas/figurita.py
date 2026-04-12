from pydantic import BaseModel

'''
Esquemas para la creación y respuesta de las figuritas.
'''

class FiguitaCreate(BaseModel):
    numero: int
    equipo: str
    jugador: str
    cantidad: int
    permite_subasta: bool

class FiguitaResponse(FiguitaCreate):
    id: int
