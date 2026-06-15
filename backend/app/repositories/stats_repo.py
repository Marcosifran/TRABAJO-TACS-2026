from datetime import datetime
from typing import Any
from bson import ObjectId
from pymongo import ASCENDING

from app.core.database import get_db


def _get_collection():
    """Obtiene la colección de estadísticas históricas"""
    return get_db()["stats_historicos"]


def _ensure_indexes():
    """Crea índices para optimizar consultas"""
    collection = _get_collection()
    collection.create_index([("fecha", ASCENDING)])
    collection.create_index([("periodo", ASCENDING)])
    collection.create_index([("fecha", ASCENDING), ("periodo", ASCENDING)])


def save_daily_snapshot(datos: dict[str, Any]) -> str:
    """
    Guarda un snapshot diario de estadísticas.

    Args:
        datos: Diccionario con métricas del día

    Returns:
        ID del documento insertado
    """
    _ensure_indexes()
    collection = _get_collection()

    doc = {
        "_id": ObjectId(),
        "fecha": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
        "periodo": "daily",
        "datos": datos,
    }

    result = collection.insert_one(doc)
    return str(result.inserted_id)


def get_snapshots(fecha_inicio: datetime, fecha_fin: datetime) -> list[dict[str, Any]]:
    """
    Obtiene snapshots dentro de un rango de fechas.

    Args:
        fecha_inicio: Fecha de inicio (inclusive)
        fecha_fin: Fecha de fin (inclusive)

    Returns:
        Lista de snapshots
    """
    _ensure_indexes()
    collection = _get_collection()

    query = {
        "fecha": {
            "$gte": fecha_inicio,
            "$lte": fecha_fin,
        },
        "periodo": "daily",
    }

    snapshots = list(collection.find(query).sort("fecha", -1))
    return [
        {
            "fecha": doc["fecha"],
            "datos": doc.get("datos", {}),
        }
        for doc in snapshots
    ]


def get_timeline_dias(fecha_inicio: datetime, fecha_fin: datetime, dias: int = 30) -> list[dict[str, Any]]:
    """
    Obtiene timeline de últimos N días.

    Args:
        fecha_inicio: Fecha de inicio
        fecha_fin: Fecha de fin
        dias: Cantidad de días a retornar (default 30)

    Returns:
        Lista de datos diarios
    """
    _ensure_indexes()
    collection = _get_collection()

    query = {
        "fecha": {
            "$gte": fecha_inicio,
            "$lte": fecha_fin,
        },
        "periodo": "daily",
    }

    snapshots = list(
        collection.find(query, projection={"fecha": 1, "datos": 1})
        .sort("fecha", 1)
        .limit(dias)
    )

    return [
        {
            "fecha": doc["fecha"].strftime("%Y-%m-%d"),
            "usuarios": doc.get("datos", {}).get("usuarios_totales", 0),
            "figuritas_publicadas": doc.get("datos", {}).get("figuritas_publicadas", 0),
            "intercambios_aceptados": doc.get("datos", {}).get("intercambios_aceptados", 0),
            "subastas_activas": doc.get("datos", {}).get("subastas_activas", 0),
        }
        for doc in snapshots
    ]


def limpiar_snapshots_antiguos(dias_retencion: int = 90) -> int:
    """
    Elimina snapshots más antiguos que N días.

    Args:
        dias_retencion: Cantidad de días a retener (default 90)

    Returns:
        Cantidad de documentos eliminados
    """
    collection = _get_collection()
    fecha_limite = datetime.utcnow()
    fecha_limite = fecha_limite.replace(
        day=fecha_limite.day - dias_retencion,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    query = {"fecha": {"$lt": fecha_limite}}
    result = collection.delete_many(query)
    return result.deleted_count
