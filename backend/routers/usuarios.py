from fastapi import APIRouter, HTTPException
from schemas import Faltante
from database import db_usuarios, db_faltantes

router = APIRouter(prefix = "/usuarios", tags = ["Usuarios y Faltantes"])

@router.post("/{usuario_id}/faltantes")
def registrar_faltante(usuario_id: int, faltante: Faltante):
    #verifico que el usuario exista en la base de datos
    usuario_existe = any(u["id"] == usuario_id for u in db_usuarios)
    if not usuario_existe:
        #si no existe, retornamos un error 404 (not found)
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    #le asignamos los ids
    faltante.id = len(db_faltantes) + 1
    faltante.usuario_id = usuario_id

    #guardo en memoria
    nuevo_faltante = faltante.model_dump()
    db_faltantes.append(nuevo_faltante)

    return {"message": "Faltante registrado", "data": nuevo_faltante}

@router.get("/{usuario_id}/faltantes")
def listar_faltantes(usuario_id: int):
    #devuelvo solo solo las que le faltan al id
    faltantes_usuario = [f for f in db_faltantes if f["usuario_id"] == usuario_id]
    return {"usuario_id": usuario_id, "faltantes": faltantes_usuario}