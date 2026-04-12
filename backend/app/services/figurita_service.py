from app.schemas.figurita import FiguitaCreate
from app.repositories import figurita_repo


def listar() -> list[dict]:
    return figurita_repo.get_all()


def publicar(figurita: FiguitaCreate) -> dict:
    return figurita_repo.create(figurita)


def eliminar(figurita_id: int) -> bool:
    return figurita_repo.delete(figurita_id)
