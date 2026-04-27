from app.schemas.album_sch import FiguritaAlbumResponse, FiguritaAlbumCreate

_db: list[dict] = []
_next_id = 1

"""Repositorio para manejar las operaciones relacionadas con las figuritas del álbum."""

def get_all() -> list[dict]:
    """Obtiene todas las figuritas en general"""
    return _db

def get_by_id(figurita_id: int) -> dict | None:
    """Obtiene una figurita por su ID."""
    return next((figurita for figurita in _db if figurita["id"] == figurita_id), None)

def get_by_usuario(usuario_id: int) -> list[dict]:
    """Obtiene todas las figuritas de un usuario específico."""
    return [figurita for figurita in _db if figurita["usuario_id"] == usuario_id]

def buscar(
    numero: int | None,
    equipo: str | None,
    jugador: str | None,
    usuario_id: int | None = None,
) -> list[dict]:
    resultado = list(_db)
    if usuario_id is not None:
        resultado = [f for f in resultado if f["usuario_id"] == usuario_id]
    if numero is not None:
        resultado = [f for f in resultado if f["numero"] == numero]
    if equipo is not None:
        resultado = [f for f in resultado if equipo.lower() in f["equipo"].lower()]
    if jugador is not None:
        resultado = [f for f in resultado if jugador.lower() in f["jugador"].lower()]
    return resultado

def create(figurita: FiguritaAlbumCreate, usuario_id: int) -> dict:
    """Agrega una figurita al album personal de un usuario."""
    global _next_id
    nueva = figurita.model_dump()
    nueva["id"] = _next_id
    nueva["usuario_id"] = usuario_id
    _next_id += 1
    _db.append(nueva)
    return nueva

def update_cantidad(figurita_id:int, cantidad: int) -> dict | None:
    """Actualiza la cantidad de una figurita en el album personal de un usuario. Retorna la cantidad disponible o None si no se encuentra la figurita."""
    figurita = get_by_id(figurita_id)
    if not figurita:
        return None
    figurita["cantidad"] = cantidad
    return figurita

def delete(figurita_id: int) -> bool:
    """Elimina una figurita del album personal de un usuario. Retorna True si se eliminó correctamente, False si no se encontró la figurita."""
    for index, figurita in enumerate(_db):
        if figurita["id"] == figurita_id:
            _db.pop(index)
            return True
    return False

def get_por_numero_y_usuario(numero: int, usuario_id: int) -> dict | None:
    return next(
        (f for f in _db if f["numero"] == numero and f["usuario_id"] == usuario_id),
        None,
    )

