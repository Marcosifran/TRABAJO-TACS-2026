from fastapi import APIRouter
from database import db_figuritas
from schemas import Figurita

router = APIRouter(prefix="/figuritas", tags=["Figuritas"])

@router.post("/")
def publicar_figuritas(figu: Figurita):
    figu.id = len(db_figuritas) +1
    nueva_figurita = figu.model_dump() #convierte el objeto pydantic en un diccionario
    db_figuritas.append(nueva_figurita)
    return {"mensaje": "Figurita publicada", "data": nueva_figurita}

@router.get("/")
def obtener_figuritas():
    return {"disponibles": db_figuritas}