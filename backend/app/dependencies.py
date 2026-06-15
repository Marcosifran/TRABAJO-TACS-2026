from fastapi import Header, HTTPException, Query
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


# Extrae el usuario autenticado del header Authorization: Bearer <jwt>.
def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict:
    if not authorization:
        raise HTTPException(
            status_code=422,
            detail="Debe enviarse Authorization: Bearer <token>",
        )

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

    return {
        "id": usuario_id,
        "email": payload.get("email"),
        "nombre": payload.get("nombre"),
        "es_admin": payload.get("es_admin", False),
    }
