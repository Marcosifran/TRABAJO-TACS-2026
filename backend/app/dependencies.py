from fastapi import Header, HTTPException
from app.repositories import usuario_repo


# Extrae el usuario del header X-User-Token.
# Si el token no existe o es inválido, corta con 401.
def get_current_user(x_user_token: str = Header(..., description="Token de identificación del usuario")) -> dict:
    usuario = usuario_repo.get_by_token(x_user_token)
    if not usuario:
        raise HTTPException(status_code=401, detail="Token inválido o inexistente")
    return usuario
