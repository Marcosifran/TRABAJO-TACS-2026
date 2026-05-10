from pymongo import MongoClient
from app.core.config import settings

class Database:
    client : MongoClient = None
    db = None

db_instance = Database()

def connect_to_mongo():
    print("Conectando a mongodb")
    db_instance.client = MongoClient(settings.mongodb_url)
    db_instance.db = db_instance.client[settings.mongodb_db_name]
    # Hacemos un ping de prueba para asegurar que la conexión es exitosa
    db_instance.client.admin.command('ping')
    print("Conectado a mongodb")

def close_mongo_connection():
    print("Cerrando conexión")
    if db_instance.client:
        db_instance.client.close()

def get_db():
    return db_instance.db
