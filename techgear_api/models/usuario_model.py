from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


class RolUsuario(str, Enum):
    cliente = "cliente"
    administrador = "administrador"
    

class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    rol: RolUsuario = RolUsuario.cliente


class UsuarioCreate(UsuarioBase):
    """Datos de entrada al registrar un usuario (esquema; sin endpoints aún)."""
    password: str = Field(..., min_length=8, max_length=128)
    

class UsuarioResponse(UsuarioBase):
    """Datos de salida: nunca incluye la contraseña."""
    id: str
    fecha_creacion: datetime