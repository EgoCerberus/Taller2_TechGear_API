"""API REST de TechGear (FastAPI + MongoDB Atlas)."""
from datetime import datetime
from pathlib import Path
from typing import List
from pydantic import BaseModel

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.errors import DuplicateKeyError

# --- FUERZA LA CARGA DEL .ENV DESDE LA RUTA EXACTA ---
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)
# --------------------------------------------------------

from db.database import pedidos_collection, productos_collection, usuarios_collection
from models.models import (
    PedidoCreate,
    PedidoOut,
    ProductoCreate,
    ProductoOut,
    ProductoUpdate,
    Token,
    Usuario,
    UsuarioLogin,
    UsuarioOut,
)
from seguridad import (
    crear_token,
    decodificar_token,
    es_email_admin,
    hashear_password,
    verificar_password,
)

class EstadoUpdate(BaseModel):
    estado: str
    
app = FastAPI(title="TechGear API", version="1.2.0")
bearer = HTTPBearer(auto_error=False)

@app.get("/", tags=["General"])
def inicio():
    return {"mensaje": "TechGear API funcionando", "docs": "/docs"}

@app.on_event("startup")
def crear_indices():
    # Garantiza que el email sea único en la colección de usuarios
    try:
        usuarios_collection.create_index("email", unique=True)
    except Exception:
        pass


def to_oid(id_: str) -> ObjectId:
    try:
        return ObjectId(id_)
    except (InvalidId, TypeError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "ID inválido")


def serializar(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


def usuario_publico(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "nombre": doc["nombre"],
        "email": doc["email"],
        "rol": doc.get("rol", "cliente"),
        "es_admin": doc.get("es_admin", False),  
    }


def usuario_actual(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    """Dependencia: exige 'Authorization: Bearer <jwt>' y devuelve el usuario."""
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta el token")
    user_id = decodificar_token(cred.credentials)
    usuario = usuarios_collection.find_one({"_id": to_oid(user_id)})
    if not usuario:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario no existe")
    return usuario


def solo_admin(usuario: dict = Depends(usuario_actual)) -> dict:
    """Dependencia: deja pasar únicamente a usuarios con rol 'administrador' o 'admin'."""
    rol = usuario.get("rol", "")
    if rol not in ["admin", "administrador"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Se requiere rol de administrador")
    return usuario


# ---------- Productos (CRUD Protegido para Admins) ----------
@app.post(
    "/productos",
    response_model=ProductoOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Productos"],
)
def crear_producto(producto: ProductoCreate, _: dict = Depends(solo_admin)):
    res = productos_collection.insert_one(producto.model_dump())
    return serializar(productos_collection.find_one({"_id": res.inserted_id}))


@app.get("/productos", response_model=List[ProductoOut], tags=["Productos"])
def listar_productos():
    return [serializar(p) for p in productos_collection.find()]


@app.get("/productos/{producto_id}", response_model=ProductoOut, tags=["Productos"])
def obtener_producto(producto_id: str):
    producto = productos_collection.find_one({"_id": to_oid(producto_id)})
    if not producto:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    return serializar(producto)


@app.put("/productos/{producto_id}", response_model=ProductoOut, tags=["Productos"])
def actualizar_producto(
    producto_id: str, producto: ProductoUpdate, _: dict = Depends(solo_admin)
):
    cambios = producto.model_dump(exclude_unset=True)
    if not cambios:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No hay campos para actualizar")
    res = productos_collection.update_one(
        {"_id": to_oid(producto_id)}, {"$set": cambios}
    )
    if res.matched_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    return serializar(productos_collection.find_one({"_id": to_oid(producto_id)}))


@app.delete("/productos/{producto_id}", tags=["Productos"])
def eliminar_producto(producto_id: str, _: dict = Depends(solo_admin)):
    res = productos_collection.delete_one({"_id": to_oid(producto_id)})
    if res.deleted_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    return {"mensaje": "Producto eliminado"}


# ---------- Pedidos ----------
@app.post(
    "/pedidos",
    response_model=PedidoOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Pedidos"],
)
def registrar_pedido(pedido: PedidoCreate):
    total = 0.0
    actualizaciones = []
    items_guardar = []
    for item in pedido.items:
        producto = productos_collection.find_one({"_id": to_oid(item.producto_id)})
        if not producto:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, f"Producto {item.producto_id} no existe"
            )
        if producto["stock"] < item.cantidad:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Stock insuficiente para '{producto['nombre']}'",
            )
        total += producto["precio"] * item.cantidad
        actualizaciones.append((producto["_id"], item.cantidad))
        items_guardar.append({
            "producto_id": item.producto_id,
            "cantidad": item.cantidad,
            "nombre": producto["nombre"],
            "precio_unitario": producto["precio"],
        })

    for oid, cantidad in actualizaciones:
        productos_collection.update_one({"_id": oid}, {"$inc": {"stock": -cantidad}})

    data = pedido.model_dump()
    data["items"] = items_guardar
    data["total"] = round(total, 2)
    data["estado"] = "pendiente"
    data["fecha"] = datetime.utcnow()
    res = pedidos_collection.insert_one(data)
    return serializar(pedidos_collection.find_one({"_id": res.inserted_id}))


# =========================================================================
# ENDPOINT: LISTAR PEDIDOS
# Retorna todos los pedidos registrados en la base de datos.
# =========================================================================
@app.get("/pedidos", response_model=List[PedidoOut], tags=["Pedidos"])
def listar_pedidos():
    return [serializar(p) for p in pedidos_collection.find()]

@app.get("/pedidos/{pedido_id}", response_model=PedidoOut, tags=["Pedidos"])
def obtener_pedido(pedido_id: str, _: dict = Depends(usuario_actual)):
    """
    Obtiene el detalle completo de un pedido específico usando su ID.
    Exige autenticación activa (usuario logueado).
    """
    pedido = pedidos_collection.find_one({"_id": to_oid(pedido_id)})
    if not pedido:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
    return serializar(pedido)

# =========================================================================
# ENDPOINT: ACTUALIZAR PEDIDO (CLIENTE / ACUMULACIÓN)
# Permite actualizar un pedido existente (como acumular ítems o modificar estado).
# =========================================================================
@app.put("/pedidos/{pedido_id}", tags=["Pedidos"])
def actualizar_pedido(pedido_id: str, datos_actualizacion: dict):
    res = pedidos_collection.update_one(
        {"_id": to_oid(pedido_id)}, {"$set": datos_actualizacion}
    )
    if res.matched_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
    return {"mensaje": "Pedido actualizado exitosamente"}

@app.patch("/pedidos/{pedido_id}/estado", tags=["Pedidos"])
def actualizar_estado_pedido(
    pedido_id: str, datos: EstadoUpdate, _: dict = Depends(solo_admin)
):
    """
    Actualiza el estado de un pedido (ej: pendiente, enviado, completado, cancelado).
    Exige rol de administrador.
    """
    estados_validos = ["pendiente", "enviado", "completado", "cancelado"]
    if datos.estado not in estados_validos:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Estado inválido. Debe ser uno de: {', '.join(estados_validos)}"
        )
        
    res = pedidos_collection.update_one(
        {"_id": to_oid(pedido_id)},
        {"$set": {"estado": datos.estado}}
    )
    
    if res.matched_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
        
    return {"mensaje": f"Estado del pedido actualizado a '{datos.estado}' exitosamente"}

# =========================================================================
# ENDPOINT: ELIMINAR / CANCELAR PEDIDO (ADMIN O CLIENTE DUEÑO) + STOCK
# =========================================================================
@app.delete("/pedidos/{pedido_id}", tags=["Pedidos"])
def eliminar_pedido(pedido_id: str, usuario: dict = Depends(usuario_actual)):
    oid = to_oid(pedido_id)
    pedido = pedidos_collection.find_one({"_id": oid})
    
    if not pedido:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
    
    # Validar permisos: es admin O es el dueño del pedido
    rol = usuario.get("rol", "")
    es_admin = rol in ["admin", "administrador"] or usuario.get("es_admin", False)
    
    email_usuario = usuario.get("email", "").lower()
    email_pedido = (pedido.get("cliente_email") or pedido.get("usuario_email") or "").lower()
    
    es_dueno = email_usuario == email_pedido
    estado_pedido = str(pedido.get("estado", "")).lower()

    # Si no es admin, exigimos que sea el dueño Y que el pedido esté pendiente
    if not es_admin:
        if not es_dueno:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tienes permisos para cancelar este pedido")
        if estado_pedido != "pendiente":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Solo se pueden cancelar pedidos en estado pendiente")

    # REINTEGRO DE STOCK: Devuelve la cantidad comprada al inventario del producto
    for item in pedido.get("items", []):
        prod_id = item.get("producto_id")
        cantidad = item.get("cantidad", 0)
        if prod_id and cantidad > 0:
            try:
                productos_collection.update_one(
                    {"_id": to_oid(prod_id)},
                    {"$inc": {"stock": cantidad}}
                )
            except Exception:
                pass # Evita que falle si el producto original fue borrado de la BD

    # Procedemos a eliminar el pedido
    res = pedidos_collection.delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
        
    return {"mensaje": "Pedido eliminado y stock reintegrado exitosamente"}

# ---------- Usuarios (registro, login con JWT, perfil) ----------
@app.post(
    "/usuarios/registro",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Usuarios"],
)
def registrar_usuario(usuario: Usuario):
    rol = "admin" if es_email_admin(usuario.email) else "cliente"
    doc = {
        "nombre": usuario.nombre,
        "email": usuario.email.lower(),
        "password": hashear_password(usuario.password),
        "rol": rol,
    }
    try:
        res = usuarios_collection.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está registrado")
    return usuario_publico(usuarios_collection.find_one({"_id": res.inserted_id}))


@app.post("/usuarios/login", response_model=Token, tags=["Usuarios"])
def login(datos: UsuarioLogin):
    usuario = usuarios_collection.find_one({"email": datos.email.lower()})
    if not usuario or not verificar_password(datos.password, usuario["password"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email o contraseña incorrectos")
    
    if es_email_admin(usuario["email"]) and usuario.get("rol") != "admin":
        usuarios_collection.update_one({"_id": usuario["_id"]}, {"$set": {"rol": "admin"}})
        usuario["rol"] = "admin"
        
    return {
        "access_token": crear_token(str(usuario["_id"])),
        "token_type": "bearer",
        "usuario": usuario_publico(usuario),
    }


@app.get("/usuarios/me", response_model=UsuarioOut, tags=["Usuarios"])
def mi_perfil(usuario: dict = Depends(usuario_actual)):
    return usuario_publico(usuario)

class RecuperarPasswordRequest(BaseModel):
    email: str

@app.post("/usuarios/recuperar", tags=["Usuarios"])
def recuperar_password(datos: RecuperarPasswordRequest):
    """Procesa la solicitud de recuperación de contraseña."""
    usuario = usuarios_collection.find_one({"email": datos.email.lower()})
    
    # Por seguridad (para evitar filtración de correos registrados), 
    # devolvemos el mismo mensaje de éxito exista o no el usuario en la BD.
    return {
        "mensaje": "Si el correo está registrado, recibirás las instrucciones para recuperar tu cuenta."
    }