from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from dotenv import load_dotenv
import os
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from pymongo import MongoClient

load_dotenv()

# ==================== CONFIGURACIÓN DE BASE DE DATOS ====================
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


# ==================== MODELOS PYDANTIC ====================

# Productos
class ProductoBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    categoria: str = Field(..., min_length=2, max_length=50)
    precio: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    categoria: Optional[str] = Field(None, min_length=2, max_length=50)
    precio: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)


class ProductoResponse(ProductoBase):
    id: str


# Pedidos
class ItemPedidoCreate(BaseModel):
    producto_id: str
    cantidad: int = Field(..., gt=0)


class ItemPedido(ItemPedidoCreate):
    nombre: str
    precio_unitario: float = Field(..., gt=0)


class PedidoCreate(BaseModel):
    cliente_nombre: str = Field(..., min_length=2, max_length=100)
    cliente_email: EmailStr
    items: List[ItemPedidoCreate] = Field(..., min_length=1)


class PedidoResponse(BaseModel):
    id: str
    cliente_nombre: str
    cliente_email: EmailStr
    items: List[ItemPedido]
    total: float
    fecha_creacion: datetime


# ==================== LIFECYCLE DE FASTAPI ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    verificar_conexion()
    print("Conectado a MongoDB Atlas")
    yield


app = FastAPI(
    title="TechGear API",
    description="API REST de catálogo de productos y pedidos de TechGear (Estructura unificada en main.py).",
    version="1.0.0",
    lifespan=lifespan,
)


# ==================== ENDPOINTS: ESTADO ====================
@app.get("/", tags=["Estado"])
def root():
    return {"mensaje": "TechGear API funcionando"}


# ==================== ENDPOINTS: PRODUCTOS (CRUD) ====================
@app.post("/productos", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED, tags=["Productos"])
def crear_producto(producto: ProductoCreate):
    producto_dict = producto.dict()
    resultado = productos_collection.insert_one(producto_dict)
    producto_criado = productos_collection.find_one({"_id": resultado.inserted_id})
    producto_criado["id"] = str(producto_criado["_id"])
    return producto_criado


@app.get("/productos", response_model=List[ProductoResponse], tags=["Productos"])
def listar_productos():
    productos = []
    for p in productos_collection.find():
        p["id"] = str(p["_id"])
        productos.append(p)
    return productos


@app.get("/productos/{id}", response_model=ProductoResponse, tags=["Productos"])
def obtener_producto(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    p = productos_collection.find_one({"_id": ObjectId(id)})
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    p["id"] = str(p["_id"])
    return p


@app.put("/productos/{id}", response_model=ProductoResponse, tags=["Productos"])
def actualizar_producto(id: str, producto_update: ProductoUpdate):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    datos = {k: v for k, v in producto_update.dict().items() if v is not None}
    if not datos:
        raise HTTPException(status_code=400, detail="No hay datos para actualizar")
    
    resultado = productos_collection.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$set": datos},
        return_document=True
    )
    if not resultado:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    resultado["id"] = str(resultado["_id"])
    return resultado


@app.delete("/productos/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Productos"])
def eliminar_producto(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    resultado = productos_collection.delete_one({"_id": ObjectId(id)})
    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return None


# ==================== ENDPOINTS: PEDIDOS ====================
@app.post("/pedidos", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED, tags=["Pedidos"])
def crear_pedido(pedido: PedidoCreate):
    items_calculados = []
    total = 0.0

    for item in pedido.items:
        if not ObjectId.is_valid(item.producto_id):
            raise HTTPException(status_code=400, detail=f"ID de producto inválido: {item.producto_id}")
        
        prod = productos_collection.find_one({"_id": ObjectId(item.producto_id)})
        if not prod:
            raise HTTPException(status_code=404, detail=f"Producto no encontrado: {item.producto_id}")
        
        if prod["stock"] < item.cantidad:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para el producto: {prod['nombre']}")
        
        precio = prod["precio"]
        subtotal = precio * item.cantidad
        total += subtotal

        # Descontar stock del producto en la base de datos
        productos_collection.update_one(
            {"_id": prod["_id"]},
            {"$inc": {"stock": -item.cantidad}}
        )

        items_calculados.append({
            "producto_id": item.producto_id,
            "cantidad": item.cantidad,
            "nombre": prod["nombre"],
            "precio_unitario": precio
        })

    nuevo_pedido = {
        "cliente_nombre": pedido.cliente_nombre,
        "cliente_email": pedido.cliente_email,
        "items": items_calculados,
        "total": total,
        "fecha_creacion": datetime.utcnow()
    }

    resultado = pedidos_collection.insert_one(nuevo_pedido)
    pedido_creado = pedidos_collection.find_one({"_id": resultado.inserted_id})
    pedido_creado["id"] = str(pedido_creado["_id"])
    return pedido_creado


@app.get("/pedidos", response_model=List[PedidoResponse], tags=["Pedidos"])
def listar_pedidos():
    pedidos = []
    for p in pedidos_collection.find():
        p["id"] = str(p["_id"])
        pedidos.append(p)
    return pedidos