from app.core.database import get_db


def _col():
    return get_db()["partidos"]


def count() -> int:
    return _col().count_documents({})


def get_all() -> list[dict]:
    return list(_col().find({}, {"_id": 0}).sort([("fecha", 1), ("hora", 1)]))


def replace_all(partidos: list[dict]) -> None:
    col = _col()
    col.delete_many({})
    if partidos:
        col.insert_many(partidos)


def drop() -> None:
    _col().delete_many({})
