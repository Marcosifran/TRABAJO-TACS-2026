from app.schemas.figurita import FiguritaCreate
from app.repositories import figurita_repo


def listar() -> list[dict]:
    return figurita_repo.get_all()

def publicar(figurita: FiguritaCreate, usuario_id: int) -> dict:
    return figurita_repo.create(figurita, usuario_id)

def eliminar(figurita_id: int) -> bool:
    return figurita_repo.delete(figurita_id)
