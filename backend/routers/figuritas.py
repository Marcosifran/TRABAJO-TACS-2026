from fastapi import APIRouter, HTTPException
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

@router.delete("/{figurita_id}")
async def eliminar_figurita(figurita_id: int):
    for index, figu in enumerate(db_figuritas):
        if figu["id"] == figurita_id:
            db_figuritas.pop(index)
            return {"message": "Figurita eliminada"}
    raise HTTPException(status_code=404, detail="Figurita no encontrada")