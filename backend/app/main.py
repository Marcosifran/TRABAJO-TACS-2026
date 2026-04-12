from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import figuritas, usuarios, intercambios

# Creamos la aplicación FastAPI. El título y versión los toma desde config.py
app = FastAPI(title=settings.app_name, version=settings.app_version)

# Seteamos CORS como middleware para permitir solicitudes desde cualquier origen.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registramos los routers con el prefijo /api/v1.
app.include_router(figuritas.router, prefix="/api/v1")
app.include_router(usuarios.router, prefix="/api/v1")
app.include_router(intercambios.router, prefix="/api/v1")

# Endpoint root para chequear estado del server.
@app.get("/")
def read_root():
    return {"Hello": "World"}
