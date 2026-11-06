from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


# --- Productos ---
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


class ProductoOut(ProductoBase):
    id: str


# --- Pedidos ---
class ItemPedidoCreate(BaseModel):
    producto_id: str
    cantidad: int = Field(..., gt=0)


class ItemPedidoOut(ItemPedidoCreate):
    nombre: str
    precio_unitario: float = Field(..., gt=0)


class PedidoCreate(BaseModel):
    cliente_nombre: str = Field(..., min_length=2, max_length=100)
    cliente_email: EmailStr
    items: List[ItemPedidoCreate] = Field(..., min_length=1)


class PedidoOut(BaseModel):
    id: str
    cliente_nombre: str
    cliente_email: EmailStr
    items: List[ItemPedidoOut]
    total: float
    estado: str
    fecha: datetime


# --- Usuarios y Autenticación ---
class Usuario(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str


class UsuarioOut(BaseModel):
    id: str
    nombre: str
    email: str
    rol: str = "cliente"
    es_admin: bool = False 


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut