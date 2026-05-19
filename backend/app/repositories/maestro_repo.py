from app.core.database import get_db


def _col():
    return get_db()["maestro_figuritas"]


def count() -> int:
    return _col().count_documents({})


def get_all() -> list[dict]:
    return list(_col().find({}, {"_id": 0}).sort("numero", 1))


def get_by_numero(numero: int) -> dict | None:
    return _col().find_one({"numero": numero}, {"_id": 0})


def get_equipos() -> list[str]:
    return sorted(_col().distinct("equipo"))


def get_by_equipo(equipo: str) -> list[dict]:
    return list(
        _col()
        .find({"equipo": {"$regex": f"^{equipo}$", "$options": "i"}}, {"_id": 0})
        .sort("numero_camiseta", 1)
    )


def bulk_insert(jugadores: list[dict]) -> None:
    if jugadores:
        _col().insert_many(jugadores)


def drop() -> None:
    _col().delete_many({})
