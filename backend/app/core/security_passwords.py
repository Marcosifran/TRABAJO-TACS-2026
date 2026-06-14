"""Hashing y verificación de contraseñas con bcrypt.

Centraliza el manejo de contraseñas para que servicios y repositorios no
dependan directamente de la librería de hashing.
"""
from __future__ import annotations

import bcrypt


def hash_password(plain: str) -> str:
    """Devuelve el hash bcrypt (codificado en utf-8) de una contraseña en texto plano."""
    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Compara una contraseña en texto plano contra su hash bcrypt."""
    if not plain or not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        # hash con formato inválido
        return False
