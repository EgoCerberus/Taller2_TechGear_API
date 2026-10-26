from typing import Optional
from pydantic import BaseModel, Field


class ProductoBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    categoria: str = Field(..., min_length=2, max_length=50)
    precio: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)


class ProductoCreate(ProductoBase):
    """Datos de entrada al crear un producto."""
    pass


class ProductoUpdate(BaseModel):
    """Todos los campos opcionales para actualizaciones parciales."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    categoria: Optional[str] = Field(None, min_length=2, max_length=50)
    precio: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)


class ProductoResponse(ProductoBase):
    """Datos de salida: incluye el id de Mongo convertido a texto."""
    id: str