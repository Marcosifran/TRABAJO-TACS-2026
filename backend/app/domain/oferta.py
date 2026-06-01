from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Oferta:
    id: str
    subasta_id: str
    usuario_id: int
    ofrecidas: list[str]
