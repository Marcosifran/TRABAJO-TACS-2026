from fastapi import FastAPI
from pydantic import BaseModel
from routers import figuritas
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Mundial Figuritas TACS", version="2026.1")


# 2. Le damos permiso a cualquier frontend para que se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # El asterisco significa "dejar pasar a todos"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(figuritas.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}