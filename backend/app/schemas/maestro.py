from pydantic import BaseModel


class JugadorMaestroResponse(BaseModel):
    numero: int
    equipo: str
    jugador: str
    posicion: str
    numero_camiseta: int
