import datetime as dt
from dataclasses import dataclass

from app.schemas import EstadoSubasta


@dataclass(frozen=True, slots=True)
class Subasta:
    id: str
    figurita_id: str
    usuario_id: int
    inicio: dt.datetime
    fin: dt.datetime
    estado: EstadoSubasta
    figurita_jugador: str | None = None
    figurita_equipo: str | None = None
    figurita_numero: int | None = None
    oferta_ganadora_id: str | None = None
