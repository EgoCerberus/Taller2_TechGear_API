import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# Carga el .env independientemente de dónde se ejecute uvicorn
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "techgear")

if not MONGODB_URI:
    raise RuntimeError("Falta la variable MONGODB_URI en el archivo .env")

client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]

productos_collection = db["productos"]
pedidos_collection = db["pedidos"]
usuarios_collection = db["usuarios"]


def verificar_conexion() -> bool:
    """Hace ping a Atlas para confirmar que la conexión funciona."""
    client.admin.command("ping")
    return True