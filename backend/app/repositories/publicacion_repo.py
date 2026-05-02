from app.schemas.publicacion_sch import PublicacionCreate

_db: list[dict] = []
_next_id = 1

"""Repositorio de publicaciones, maneja las operaciones relacionadas con las publicaciones de intercambio."""

def get_all() -> list[dict]:
    """Obtiene todas las publicaciones de intercambio."""
    return _db

def get_by_id(publicacion_id: int) -> dict | None:
    """Obtiene una publicación por su ID."""
    return next((publicacion for publicacion in _db if publicacion["id"] == publicacion_id), None)

def get_by_usuario(usuario_id: int) -> list[dict]:
    """Obtiene todas las publicaciones de un usuario específico."""
    return [publicacion for publicacion in _db if publicacion["usuario_id"] == usuario_id]

def get_by_figurita_personal(figurita_personal_id: int) -> dict | None:
    """Obtiene todas las publicaciones que ofrecen una figurita personal específica."""
    return next((publicacion for publicacion in _db if publicacion["figurita_personal_id"] == figurita_personal_id), None)

def buscar(
        numero: int | None,
        equipo: str | None,
        jugador: str | None,
        tipo_intercambio: str | None = None,
        usuario_id: int | None = None,
) -> list[dict]:
    """Busca publicaciones por número, equipo, jugador o usuario."""
    resultado = _db
    if numero is not None:
        resultado = [p for p in resultado if p["numero"] == numero]
    if equipo is not None:
        resultado = [p for p in resultado if equipo.lower() in p["equipo"].lower()]
    if jugador is not None:
        resultado = [p for p in resultado if jugador.lower() in p["jugador"].lower()]
    if tipo_intercambio is not None:
        resultado = [p for p in resultado if p["tipo_intercambio"].lower() == tipo_intercambio.lower()]
    if usuario_id is not None:
        resultado = [p for p in resultado if p["usuario_id"] != usuario_id]
    return resultado

def create(
        publicacion: PublicacionCreate, 
        usuario_id: int,
        numero:int,
        equipo:str,
        jugador:str
) -> dict:
    """Crea una nueva publicación de intercambio."""
    global _next_id
    nueva = {
        "id": _next_id,
        "usuario_id": usuario_id,
        "figurita_personal_id": publicacion.figurita_personal_id,
        "tipo_intercambio": publicacion.tipo_intercambio.value,
        "cantidad_disponible": publicacion.cantidad_disponible,
        "numero": numero,
        "equipo": equipo,
        "jugador": jugador
    }
    _next_id += 1
    _db.append(nueva)
    return nueva

def delete(publicacion_id: int) -> bool:
    """Elimina una publicación de intercambio. Retorna True si se eliminó correctamente, False si no se encontró la publicación."""
    for index, publicacion in enumerate(_db):
        if publicacion["id"] == publicacion_id:
            _db.pop(index)
            return True
    return False   


