from dataclasses import dataclass

from app.schemas import TipoIntercambio


@dataclass(frozen=True, slots=True)
class Publicacion:
    id: str
    usuario_id: int
    figurita_personal_id: str
    tipo_intercambio: TipoIntercambio
    cantidad_disponible: int
    numero: int
    equipo: str
    jugador: str
