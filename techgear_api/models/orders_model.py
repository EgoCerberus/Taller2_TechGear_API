from datetime import datetime
from typing import List
from pydantic import BaseModel, EmailStr, Field


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