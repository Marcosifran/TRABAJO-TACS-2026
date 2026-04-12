from pydantic import BaseModel
from app.schemas.figurita import SugerenciaResponse


# El token no se incluye acá: nunca debe volver en una respuesta de la API
class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str

class SugerenciasResponse(BaseModel):
    usuario_id: int
    sugerencias: list[SugerenciaResponse]
