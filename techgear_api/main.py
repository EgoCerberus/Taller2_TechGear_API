from contextlib import asynccontextmanager
from fastapi import FastAPI
from db.database import verificar_conexion


@asynccontextmanager
async def lifespan(app: FastAPI):
    verificar_conexion()
    print("Conectado a MongoDB Atlas")
    yield


app = FastAPI(
    title="TechGear API",
    description="API REST de catálogo de productos y pedidos de TechGear.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(productos.router)
app.include_router(pedidos.router)


@app.get("/", tags=["Estado"])
def root():
    return {"mensaje": "TechGear API funcionando"}