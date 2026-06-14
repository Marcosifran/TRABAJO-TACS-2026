from app.repositories import usuario_repo
from app.core.security_passwords import hash_password, verify_password
from app.security import create_access_token
from app.schemas.auth_sch import LoginRequest, RegisterRequest, TokenResponse
from app.domain.errors import DomainAuthError, DomainConflictError


def _build_token_response(usuario: dict) -> TokenResponse:
    access_token = create_access_token(subject=usuario["id"], email=usuario["email"])
    return TokenResponse(access_token=access_token, usuario=usuario)


def login(data: LoginRequest) -> TokenResponse:
    usuario = usuario_repo.get_by_email(data.email)
    if not usuario or not verify_password(data.password, usuario.get("password_hash", "")):
        # Mensaje genérico: no revelar si el email existe.
        raise DomainAuthError("Credenciales inválidas")
    return _build_token_response(usuario)


def register(data: RegisterRequest) -> TokenResponse:
    if usuario_repo.get_by_email(data.email):
        raise DomainConflictError("Ya existe un usuario con ese email")
    usuario = usuario_repo.create_usuario(
        nombre=data.nombre,
        email=data.email,
        password_hash=hash_password(data.password),
        es_admin=False,
    )
    return _build_token_response(usuario)
