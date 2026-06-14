from fastapi import APIRouter

from app.schemas.auth_sch import LoginRequest, RegisterRequest, TokenResponse
from app.services import auth_service

# Router público: el login y el registro no requieren autenticación previa.
router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        200: {"description": "Login exitoso, devuelve el JWT de acceso"},
        401: {"description": "Credenciales inválidas"},
    },
)
def login(data: LoginRequest):
    return auth_service.login(data)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    responses={
        201: {"description": "Usuario registrado, devuelve el JWT de acceso"},
        409: {"description": "Ya existe un usuario con ese email"},
    },
)
def register(data: RegisterRequest):
    return auth_service.register(data)
