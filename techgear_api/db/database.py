import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "techgear")

if not MONGODB_URI:
    raise RuntimeError("Falta la variable MONGODB_URI en el archivo .env")

client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]

productos_collection = db["productos"]
pedidos_collection = db["pedidos"]


def verificar_conexion() -> bool:
    """Hace ping a Atlas para confirmar que la conexión funciona."""
    client.admin.command("ping")
    return True