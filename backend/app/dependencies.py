from fastapi import Header, HTTPException, Query
from app.repositories import usuario_repo
from app.security import verify_access_token


def page_params(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    return {"limit": limit, "offset": offset}


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _extract_bearer_token(authorization: str) -> str | None:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


# Extrae el usuario del header Authorization: Bearer <token>.
# Mantiene compatibilidad temporal con X-User-Token.
def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_user_token: str | None = Header(default=None, description="Token de identificación del usuario"),
) -> dict:
    if authorization:
        token = _extract_bearer_token(authorization)
        if token is None:
            raise _unauthorized("Formato de Authorization inválido")

        try:
            payload = verify_access_token(token)
        except Exception:
            raise _unauthorized("Token inválido o inexistente")

        subject = payload.get("sub")
        if subject is None:
            raise _unauthorized("Token inválido o inexistente")

        try:
            usuario_id = int(subject)
        except (TypeError, ValueError):
            raise _unauthorized("Token inválido o inexistente")

        usuario = usuario_repo.get_by_id(usuario_id)
        if not usuario:
            raise _unauthorized("Token inválido o inexistente")
        return usuario

    if x_user_token is not None:
        if not x_user_token:
            raise _unauthorized("Token inválido o inexistente")

        usuario = usuario_repo.get_by_token(x_user_token)
        if not usuario:
            raise _unauthorized("Token inválido o inexistente")
        return usuario

    raise HTTPException(
        status_code=422,
        detail="Debe enviarse Authorization: Bearer <token> o X-User-Token",
    )
