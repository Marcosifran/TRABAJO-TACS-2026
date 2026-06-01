from dataclasses import dataclass

from app.schemas import EstadoIntercambio


@dataclass(frozen=True, slots=True)
class Intercambio:
    id: str
    propuesto_por: int
    solicitado_a: int
    figuritas_ofrecidas: list[int]
    figurita_solicitada: int
    estado: EstadoIntercambio
