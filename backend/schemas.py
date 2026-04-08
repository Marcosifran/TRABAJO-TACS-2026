from pydantic import BaseModel

class Figurita(BaseModel):
    id: int | None = None
    numero: int
    equipo: str
    jugador: str
    cantidad: int
    permite_subasta: bool

class Faltante(BaseModel):
    usuario_id: int
    numero_figurita: int
