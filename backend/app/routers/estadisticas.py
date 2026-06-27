from fastapi import APIRouter
from app.core.database import get_db

router = APIRouter(prefix="/estadisticas", tags=["Estadísticas"])


@router.get(
    "/publicas",
    summary="Estadísticas públicas de la plataforma",
    description="Contadores globales visibles sin autenticación. Usados en la pantalla de login.",
)
def estadisticas_publicas():
    db = get_db()
    # Usuarios registrados en Mongo + 2 seed users en memoria
    usuarios = db["usuarios"].count_documents({}) + 2
    # Publicaciones activas (se eliminan al retirarse, por lo que el total = activas)
    publicaciones_activas = db["publicaciones"].count_documents({})
    # Intercambios completados (la colección puede no existir aún)
    intercambios_completados = db["intercambios"].count_documents({"estado": "aceptado"}) if "intercambios" in db.list_collection_names() else 0
    return {
        "usuarios": usuarios,
        "intercambios_completados": intercambios_completados,
        "publicaciones_activas": publicaciones_activas,
    }
