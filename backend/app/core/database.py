from pymongo import MongoClient
from app.core.config import settings

class Database:
    client: MongoClient | None = None
    db = None

db_instance = Database()

def connect_to_mongo(url: str | None = None, db_name: str | None = None):
    if db_instance.client is not None:
        return
    print("Conectando a mongodb")
    db_instance.client = MongoClient(url or settings.mongodb_url)
    db_instance.db = db_instance.client[db_name or settings.mongodb_db_name]
    db_instance.client.admin.command('ping')
    print("Conectado a mongodb")

def close_mongo_connection():
    print("Cerrando conexión")
    if db_instance.client:
        db_instance.client.close()

def get_db():
    return db_instance.db
