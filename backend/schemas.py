from pydantic import BaseModel

class Figurita(BaseModel):
    id: int | None = None
    numero: int
    equipo: str
    jugador: str
    cantidad: int
    permite_subasta: bool

class Faltante(BaseModel):
    id: int | None = None
    usuario_id: int | None = None
    numero_figurita: int
