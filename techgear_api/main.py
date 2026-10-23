from contextlib import asynccontextmanager
from fastapi import FastAPI
from db.database import verificar_conexion


@asynccontextmanager
async def lifespan(app: FastAPI):
    verificar_conexion()
    print("Conectado a MongoDB Atlas")
    yield


app = FastAPI(title="TechGear API", lifespan=lifespan)


@app.get("/")
def root():
    return {"mensaje": "TechGear API funcionando"}