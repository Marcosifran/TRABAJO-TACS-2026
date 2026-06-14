from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exceptions import register_exceptions_handlers
from app.core.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, album, publicaciones, usuarios, intercambios, subastas, admin, maestro
from app.services import maestro_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_to_mongo()
    maestro_service.inicializar()
    yield
    close_mongo_connection()

# Creamos la aplicación FastAPI. El título y versión los toma desde config.py
app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

# Excepciones
register_exceptions_handlers(app)

# Seteamos CORS como middleware para permitir solicitudes desde cualquier origen.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registramos los routers con el prefijo /api/v1.
app.include_router(auth.router, prefix="/api/v1")
app.include_router(album.router, prefix="/api/v1")
app.include_router(publicaciones.router, prefix="/api/v1")
app.include_router(usuarios.router, prefix="/api/v1")
app.include_router(intercambios.router, prefix="/api/v1")
app.include_router(subastas.router, prefix="/api/v1")
app.include_router(admin.router,    prefix="/api/v1")
app.include_router(maestro.router,  prefix="/api/v1")

# Endpoint root para chequear estado del server.
@app.get("/")
def read_root():
    return {"Hello": "World"}
