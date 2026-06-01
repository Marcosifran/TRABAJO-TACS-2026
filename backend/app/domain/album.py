from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FiguritaAlbum:
    id: str
    usuario_id: int
    numero: int
    equipo: str
    jugador: str
    cantidad: int
