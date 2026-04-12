from pydantic import BaseModel


# El token no se incluye acá: nunca debe volver en una respuesta de la API
class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str
