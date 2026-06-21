import re

from app.core.database import get_db


def _col():
    return get_db()["maestro_figuritas"]


def count() -> int:
    return _col().count_documents({})


def get_all() -> list[dict]:
    return list(_col().find({}, {"_id": 0}).sort("numero", 1))


def get_by_number(numero: int) -> dict | None:
    return _col().find_one({"numero": numero}, {"_id": 0})


def get_teams() -> list[str]:
    return sorted(_col().distinct("equipo"))


def get_by_team(equipo: str) -> list[dict]:
    return list(
        _col()
        .find({"equipo": {"$regex": f"^{equipo}$", "$options": "i"}}, {"_id": 0})
        .sort("numero_camiseta", 1)
    )


def search_by_name(nombre: str, equipo: str | None = None, limit: int = 10) -> list[dict]:
    query: dict = {"jugador": {"$regex": re.escape(nombre), "$options": "i"}}
    if equipo:
        query["equipo"] = {"$regex": f"^{re.escape(equipo)}$", "$options": "i"}
    return list(_col().find(query, {"_id": 0}).sort("jugador", 1).limit(limit))


def bulk_insert(jugadores: list[dict]) -> None:
    if jugadores:
        _col().insert_many(jugadores)


def drop() -> None:
    _col().delete_many({})
