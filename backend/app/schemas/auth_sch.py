from pydantic import BaseModel, Field

from app.schemas.usuario import UsuarioResponse


class LoginRequest(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    nombre: str = Field(min_length=1)
    email: str = Field(min_length=3)
    password: str = Field(min_length=6)


# El token de acceso es un JWT firmado; el cliente lo envía como Authorization: Bearer.
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse
