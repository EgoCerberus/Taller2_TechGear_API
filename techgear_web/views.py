import unicodedata

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.cache import cache
from services import (
    api_listar_productos,
    api_login,
    api_registrar_usuario,
    api_crear_producto,
    api_eliminar_producto,
    api_actualizar_producto,
    api_listar_pedidos,         
    api_actualizar_estado_pedido,
    api_crear_pedido,
    api_actualizar_pedido_cliente,
    api_eliminar_pedido
)
try:
    from services import api_recuperar_password
except ImportError:
    api_recuperar_password = None


# ---------------------------------------------------------------------------
# Datos del catálogo (los mismos de techstore.html)
# ---------------------------------------------------------------------------

def _norm(texto):
    """Minúsculas y sin tildes, para comparar textos."""
    texto = unicodedata.normalize('NFD', str(texto or ''))
    return ''.join(c for c in texto if unicodedata.category(c) != 'Mn').lower()


# 'claves' sirven para ubicar los productos de la API en una categoría
CATEGORIAS = [
    {'nombre': 'Portátiles',  'icono': 'bi-laptop',     'claves': ['portat', 'laptop', 'notebook', 'comput']},
    {'nombre': 'Celulares',   'icono': 'bi-phone',      'claves': ['celular', 'movil', 'phone', 'tablet']},
    {'nombre': 'Gaming',      'icono': 'bi-controller', 'claves': ['gam', 'juego', 'consola']},
    {'nombre': 'Audio',       'icono': 'bi-headphones', 'claves': ['audio', 'audifon', 'parlante', 'sonido']},
    {'nombre': 'Wearables',   'icono': 'bi-smartwatch', 'claves': ['wear', 'reloj', 'watch']},
    {'nombre': 'Periféricos', 'icono': 'bi-keyboard',   'claves': ['perif', 'teclado', 'mouse', 'raton']},
    {'nombre': 'Cámaras',     'icono': 'bi-camera',     'claves': ['camara', 'foto']},
    {'nombre': 'Redes',       'icono': 'bi-router',     'claves': ['red', 'router', 'wifi']},
]

# Productos destacados de techstore.html (precio_anterior = precio sin descuento)
PRODUCTOS_DESTACADOS = [
    {'nombre': 'Portátil Pro 15"',        'categoria': 'Portátiles',  'precio': 3200000, 'precio_anterior': 3800000, 'etiqueta': 'Nuevo',  'color': '#3b82f6'},
    {'nombre': 'Smartphone X Ultra',      'categoria': 'Celulares',   'precio': 2400000, 'precio_anterior': 2700000, 'etiqueta': '-11%',   'color': '#8b5cf6'},
    {'nombre': 'Audífonos Wireless ANC', 'categoria': 'Audio',        'precio': 450000,  'precio_anterior': 600000,  'etiqueta': '-25%',   'color': '#0ea5e9'},
    {'nombre': 'Smartwatch Fit 5',        'categoria': 'Wearables',   'precio': 380000,  'precio_anterior': 450000,  'etiqueta': 'Top',    'color': '#10b981'},
    {'nombre': 'Teclado Mecánico RGB',   'categoria': 'Periféricos', 'precio': 260000,  'precio_anterior': 320000,  'etiqueta': '-19%',   'color': '#f59e0b'},
    {'nombre': 'Control Gamer Pro',       'categoria': 'Gaming',      'precio': 210000,  'precio_anterior': 260000,  'etiqueta': 'Gaming', 'color': '#ef4444'},
    {'nombre': 'Cámara 4K Action',        'categoria': 'Cámaras',     'precio': 520000,  'precio_anterior': 650000,  'etiqueta': '-20%',   'color': '#6366f1'},
    {'nombre': 'Router WiFi 6',           'categoria': 'Redes',       'precio': 290000,  'precio_anterior': 340000,  'etiqueta': 'Oferta', 'color': '#14b8a6'},
]


def _grupo_de(categoria):
    """Devuelve la categoría del catálogo que corresponde a un texto libre."""
    cat = _norm(categoria)
    if not cat:
        return None
    for c in CATEGORIAS:
        if _norm(c['nombre']) == cat or any(k in cat for k in c['claves']):
            return c
    return None


def catalogo_view(request):
    usuario = request.session.get('usuario')

    # 1) Obtener productos de la API usando caché temporal (evita latencia excesiva y cold starts repetidos)
    productos_api = cache.get('productos_catalogo_cache')
    if not productos_api:
        productos_api = api_listar_productos() or []
        cache.set('productos_catalogo_cache', productos_api, 300) # Expira en 5 minutos

    productos = []
    for p in productos_api:
        if isinstance(p, dict):
            prod = dict(p)
            # Normalizar el ID para evitar guiones bajos en el template de Django
            if '_id' in prod and isinstance(prod['_id'], dict):
                prod['id'] = prod['_id'].get('$oid') or str(prod['_id'])
            elif '_id' in prod:
                prod['id'] = str(prod['_id'])
            
            grupo = _grupo_de(prod.get('categoria'))
            prod['grupo'] = grupo['nombre'] if grupo else prod.get('categoria', 'General')
            prod['icono'] = grupo['icono'] if grupo else 'bi-box-seam'
            if 'stock' not in prod:
                prod['stock'] = 0
            productos.append(prod)

    # 2) Búsqueda (?q=...)
    q = request.GET.get('q', '').strip()
    qn = _norm(q)
    if qn:
        productos = [
            p for p in productos
            if qn in _norm(p.get('nombre')) or qn in _norm(p.get('categoria'))
        ]

    # 3) Categorías y filtros
    categoria_sel = request.GET.get('categoria', '').strip()
    categorias = [
        {**c, 'cantidad': sum(1 for p in productos if p['grupo'] == c['nombre']),
         'activa': c['nombre'] == categoria_sel}
        for c in CATEGORIAS
    ]

    if categoria_sel:
        productos = [p for p in productos if p['grupo'] == categoria_sel]

    return render(request, 'catalog.html', {
        'productos': productos,
        'categorias': categorias,
        'categoria_sel': categoria_sel,
        'usuario': usuario,
        'q': q,
    })


# ---------------------------------------------------------------------------
# Resto de vistas
# ---------------------------------------------------------------------------

def home(request):
    usuario = request.session.get('usuario')
    return render(request, 'index.html', {'usuario': usuario})

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        data = api_login(email, password)
        if data and 'access_token' in data:
            # Guardar el token y los datos del usuario en la sesión de Django
            request.session['access_token'] = data['access_token']
            request.session['usuario'] = data['usuario']
            messages.success(request, f"¡Bienvenido, {data['usuario']['nombre']}!")
            return redirect('catalogo')
        else:
            messages.error(request, "Correo o contraseña incorrectos.")

    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        password = request.POST.get('password')

        exito, response = api_registrar_usuario(nombre, email, password)
        if exito:
            messages.success(request, "¡Registro exitoso! Ahora puedes iniciar sesión.")
            return redirect('login')
        else:
            error_msg = response.get('detail', 'Error en el registro.')
            messages.error(request, error_msg)

    return render(request, 'register.html')

def recuperar_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email and api_recuperar_password:
            api_recuperar_password(email)
        # Mismo mensaje siempre, exista o no el correo, para no revelar quién está registrado
        messages.info(request, "Si el correo está registrado, recibirás las instrucciones para recuperar tu cuenta.")
        return redirect('login')
    return render(request, 'recuperar.html')

def logout_view(request):
    request.session.flush()
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('catalogo')

def dashboard_view(request):
    token = request.session.get('access_token')
    usuario = request.session.get('usuario')

    # Validar que sea administrador (según el esquema de tu API)
    if not token or not usuario or not usuario.get('es_admin', False):
        messages.error(request, "Acceso denegado. Se requieren permisos de administrador.")
        return redirect('login')

    productos = api_listar_productos()
    return render(request, 'dashboard.html', {'productos': productos, 'usuario': usuario})

def crear_producto_view(request):
    token = request.session.get('access_token')
    if request.method == 'POST':
        datos = {
            "nombre": request.POST.get('nombre'),
            "categoria": request.POST.get('categoria'),
            "precio": float(request.POST.get('precio', 0)),
            "stock": int(request.POST.get('stock', 0))
        }
        exito, _ = api_crear_producto(token, datos)
        if exito:
            cache.delete('productos_catalogo_cache')  # Limpiar caché al crear
            messages.success(request, "Producto creado exitosamente.")
        else:
            messages.error(request, "Error al crear el producto.")
        return redirect('dashboard')
    return render(request, 'crear_producto.html')

def eliminar_producto_view(request, producto_id):
    token = request.session.get('access_token')
    exito, _ = api_eliminar_producto(token, producto_id)
    if exito:
        cache.delete('productos_catalogo_cache')  # Limpiar caché al eliminar
        messages.success(request, "Producto eliminado correctamente.")
    else:
        messages.error(request, "No se pudo eliminar el producto.")
    return redirect('dashboard')

def editar_producto_view(request, producto_id):
    token = request.session.get('access_token')
    
    productos = api_listar_productos() or []
    producto_actual = None
    for p in productos:
        p_id = p.get('id') or (p.get('_id', {}).get('$oid') if isinstance(p.get('_id'), dict) else str(p.get('_id', '')))
        if str(p_id) == str(producto_id):
            producto_actual = p
            break

    if request.method == 'POST':
        datos = {
            "nombre": request.POST.get('nombre'),
            "categoria": request.POST.get('categoria'),
            "precio": float(request.POST.get('precio', 0)),
            "stock": int(request.POST.get('stock', 0))
        }
        exito, _ = api_actualizar_producto(token, producto_id, datos)
        if exito:
            cache.delete('productos_catalogo_cache')  # Limpiar caché al actualizar
            messages.success(request, "Producto actualizado correctamente.")
        else:
            messages.error(request, "Error al actualizar el producto.")
        return redirect('dashboard')

    return render(request, 'editar_producto.html', {
        'producto_id': producto_id,
        'producto': producto_actual,
        'usuario': request.session.get('usuario')  
    })

# ---------------------------------------------------------------------------
# Gestión de Pedidos (Administrador)
# ---------------------------------------------------------------------------

def lista_pedidos_view(request):
    token = request.session.get('access_token')
    usuario = request.session.get('usuario')

    # Validar permisos de administrador
    if not token or not usuario or not usuario.get('es_admin', False):
        messages.error(request, "Acceso denegado. Se requieren permisos de administrador.")
        return redirect('login')

    todos_pedidos = api_listar_pedidos(token) or []

    # Calcular contadores reales basados en los datos de la API
    conteo_todos = len(todos_pedidos)
    conteo_pendientes = sum(1 for p in todos_pedidos if p.get('estado') == 'Pendiente')
    conteo_enviados = sum(1 for p in todos_pedidos if p.get('estado') == 'Enviado')
    conteo_entregados = sum(1 for p in todos_pedidos if p.get('estado') == 'Entregado')
    conteo_cancelados = sum(1 for p in todos_pedidos if p.get('estado') == 'Cancelado')

    # Filtrar según el parámetro GET (?estado=...)
    estado_filtro = request.GET.get('estado', 'todos').lower()
    if estado_filtro != 'todos':
        pedidos = [p for p in todos_pedidos if p.get('estado', '').lower() == estado_filtro]
    else:
        pedidos = todos_pedidos

    return render(request, 'pedidos.html', {
        'pedidos': pedidos,
        'usuario': usuario,
        'estado_filtro': estado_filtro,
        'conteo_todos': conteo_todos,
        'conteo_pendientes': conteo_pendientes,
        'conteo_enviados': conteo_enviados,
        'conteo_entregados': conteo_entregados,
        'conteo_cancelados': conteo_cancelados,
    })

def actualizar_estado_pedido_view(request, pedido_id):
    token = request.session.get('access_token')
    usuario = request.session.get('usuario')

    if not token or not usuario or not usuario.get('es_admin', False):
        return redirect('login')

    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        exito, _ = api_actualizar_estado_pedido(token, pedido_id, nuevo_estado)
        if exito:
            messages.success(request, "Estado del pedido actualizado correctamente.")
        else:
            messages.error(request, "Error al actualizar el estado del pedido.")

    return redirect('lista_pedidos')

def mis_pedidos_view(request):
    """
    Vista encargada de listar los pedidos del usuario actual.
    L limpia, normaliza y formatea todos los datos para evitar errores en la plantilla.
    """
    token = request.session.get('access_token')
    usuario = request.session.get('usuario')

    if not token or not usuario:
        return redirect('login')

    pedidos_api = api_listar_pedidos(token) or []
    pedidos = []
    
    for p in pedidos_api:
        if isinstance(p, dict):
            ped = dict(p)
            
            # Normalizar ID del pedido
            if '_id' in ped and isinstance(ped['_id'], dict):
                ped['id'] = ped['_id'].get('$oid') or str(ped['_id'])
            elif '_id' in ped:
                ped['id'] = str(ped['_id'])
                
            # Código de pedido limpio
            codigo_raw = ped.get('numero_pedido') or ped.get('id') or 'TG-0000'
            ped['codigo_limpio'] = str(codigo_raw)[:8].upper()
                
            # Formatear fecha de forma segura
            raw_fecha = ped.get('fecha') or ped.get('created_at') or ''
            if raw_fecha:
                ped['fecha_formateada'] = str(raw_fecha).replace('T', ' - ')[:19].replace('-', '/')
            else:
                ped['fecha_formateada'] = 'Fecha no disponible'

            # Normalizar dirección y teléfono (si no hay, mostrar texto amigable)
            ped['direccion_limpia'] = ped.get('direccion') if ped.get('direccion') and ped.get('direccion') != 'Dirección no registrada' else 'Dirección no disponible'
            ped['telefono_limpio'] = ped.get('telefono') if ped.get('telefono') and ped.get('telefono') != 'S/N' else 'No registrado'

            # Normalizar ítems del pedido para asegurar que tengan nombre y precio limpios
            items_limpios = []
            for item in ped.get('items', []):
                i_limpio = dict(item)
                i_limpio['nombre_mostrar'] = i_limpio.get('nombre') or i_limpio.get('producto_nombre') or 'Producto TechGear'
                i_limpio['precio_unitario'] = float(i_limpio.get('precio_unitario') or i_limpio.get('precio') or 0)
                i_limpio['cantidad'] = int(i_limpio.get('cantidad', 1))
                items_limpios.append(i_limpio)
            ped['items_limpios'] = items_limpios

            pedidos.append(ped)
    
    # Filtrar por usuario y excluir totalmente los pedidos cancelados
    usuario_email = usuario.get('email')
    es_admin = usuario.get('es_admin', False)

    pedidos_filtrados = []
    for p in pedidos:
        # Omitir pedidos que estén cancelados
        if p.get('estado', '').lower() == 'cancelado':
            continue
            
        if not es_admin:
            if p.get('cliente_email') == usuario_email or p.get('usuario_email') == usuario_email:
                pedidos_filtrados.append(p)
        else:
            pedidos_filtrados.append(p)

    pedidos = pedidos_filtrados

    return render(request, 'mis_pedidos.html', {'pedidos': pedidos, 'usuario': usuario})

def agregar_pedido_view(request):
    """
    Gestiona la adición de productos al pedido. Si el usuario ya tiene un pedido
    en estado 'Pendiente', acumula el producto en ese mismo pedido en lugar de crear uno nuevo.
    """
    token = request.session.get('access_token')
    usuario = request.session.get('usuario')

    if not token or not usuario:
        messages.error(request, "Debes iniciar sesión para realizar un pedido.")
        return redirect('login')

    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        producto_nombre = request.POST.get('producto_nombre')
        precio = float(request.POST.get('precio', 0))
        cantidad = int(request.POST.get('cantidad', 1))

        # 1. Obtenemos los pedidos actuales del usuario desde la API
        pedidos_existentes = api_listar_pedidos(token) or []
        usuario_email = usuario.get('email')
        
        # Buscamos si ya tiene un pedido activo en estado 'Pendiente'
        pedido_pendiente = None
        for p in pedidos_existentes:
            if p.get('estado', '').lower() == 'pendiente' and (
                p.get('cliente_email') == usuario_email or p.get('usuario_email') == usuario_email
            ):
                pedido_pendiente = p
                break

        if pedido_pendiente:
            # Si ya existe un pedido pendiente, actualizamos sus ítems
            pedido_id = pedido_pendiente.get('id') or pedido_pendiente.get('_id')
            items = pedido_pendiente.get('items', [])
            
            # Verificamos si el producto ya estaba en el pedido para sumar la cantidad
            encontrado = False
            for item in items:
                if str(item.get('producto_id')) == str(producto_id):
                    item['cantidad'] = int(item.get('cantidad', 1)) + cantidad
                    encontrado = True
                    break
            
            if not encontrado:
                items.append({
                    "producto_id": str(producto_id),
                    "nombre": producto_nombre,
                    "producto_nombre": producto_nombre,
                    "cantidad": cantidad,
                    "precio_unitario": precio
                })
            
            # Recalculamos el total del pedido
            nuevo_total = sum(float(i.get('precio_unitario', 0)) * int(i.get('cantidad', 1)) for i in items)
            
            datos_actualizados = {
                "cliente_nombre": usuario.get('nombre', 'Cliente'),
                "cliente_email": usuario_email,
                "items": items,
                "total": nuevo_total,
                "estado": "Pendiente",
                "direccion": usuario.get('direccion', 'Dirección no registrada'),
                "telefono": usuario.get('telefono', 'S/N')
            }
            
            # Llamamos al servicio para actualizar el pedido existente en la API
            exito, _ = api_actualizar_pedido_cliente(token, pedido_id, datos_actualizados)
            if exito:
                messages.success(request, f"¡Se actualizó tu pedido con {producto_nombre}!")
            else:
                messages.error(request, "No se pudo actualizar el pedido.")
                
        else:
            # Si no tiene pedido pendiente, creamos uno nuevo con un número de pedido generado
            import random
            numero_generado = f"TG-{random.randint(10000, 99999)}"
            
            datos_nuevo_pedido = {
                "numero_pedido": numero_generado,
                "cliente_nombre": usuario.get('nombre', 'Cliente'),
                "cliente_email": usuario_email,
                "items": [
                    {
                        "producto_id": str(producto_id),
                        "nombre": producto_nombre,
                        "producto_nombre": producto_nombre,
                        "cantidad": cantidad,
                        "precio_unitario": precio
                    }
                ],
                "total": precio * cantidad,
                "estado": "Pendiente",
                "direccion": usuario.get('direccion', 'Dirección no registrada'),
                "telefono": usuario.get('telefono', 'S/N')
            }

            exito, _ = api_crear_pedido(token, datos_nuevo_pedido)
            if exito:
                messages.success(request, f"¡Nuevo pedido creado con {producto_nombre}!")
            else:
                messages.error(request, "No se pudo registrar el pedido. Inténtalo de nuevo.")

    return redirect('mis_pedidos')

def eliminar_pedido_admin_view(request, pedido_id):
    """
    =================================================================
    VISTA: ELIMINAR PEDIDO ADMINISTRADOR
    Valida que el usuario sea administrador y procede a eliminar 
    el pedido seleccionado llamando al servicio de la API.
    =================================================================
    """
    token = request.session.get('access_token')
    usuario = request.session.get('usuario')

    # Validación de seguridad: debe ser administrador autenticado
    if not token or not usuario or not usuario.get('es_admin', False):
        messages.error(request, "No tienes permisos de administrador para realizar esta acción.")
        return redirect('login')

    # Ejecuta la eliminación a través de la API de FastAPI
    exito, _ = api_eliminar_pedido(token, pedido_id)
    
    if exito:
        messages.success(request, "El pedido fue eliminado exitosamente del sistema.")
    else:
        messages.error(request, "No se pudo eliminar el pedido en la API.")

    # Redirige de regreso al dashboard del administrador de forma segura
    return redirect('dashboard')  # Asegúrate de que esta URL coincida con tu urls.py

def modificar_item_pedido_view(request, pedido_id, producto_id, accion):
    """
    Permite al cliente sumar, restar o eliminar un producto específico 
    de su pedido pendiente directamente desde 'Mis pedidos'.
    """
    token = request.session.get('access_token')
    usuario = request.session.get('usuario')

    if not token or not usuario:
        return redirect('login')

    pedidos_existentes = api_listar_pedidos(token) or []
    pedido_encontrado = None
    
    for p in pedidos_existentes:
        p_id = p.get('id') or p.get('_id')
        if str(p_id) == str(pedido_id) and p.get('estado', '').lower() == 'pendiente':
            pedido_encontrado = p
            break

    if not pedido_encontrado:
        messages.error(request, "No se encontró el pedido o ya no está pendiente.")
        return redirect('mis_pedidos')

    items = pedido_encontrado.get('items', [])
    nuevos_items = []

    for item in items:
        i_prod_id = str(item.get('producto_id') or item.get('_id', ''))
        if i_prod_id == str(producto_id):
            cantidad_actual = int(item.get('cantidad', 1))
            
            if accion == 'sumar':
                item['cantidad'] = cantidad_actual + 1
                nuevos_items.append(item)
            elif accion == 'restar':
                if cantidad_actual > 1:
                    item['cantidad'] = cantidad_actual - 1
                    nuevos_items.append(item)
            elif accion == 'eliminar':
                pass # Se omite para borrarlo
        else:
            nuevos_items.append(item)

    # Si el pedido se queda sin ítems, lo actualizamos a estado "Cancelado"
    if not nuevos_items:
        datos_cancelado = {
            "cliente_nombre": pedido_encontrado.get('cliente_nombre', usuario.get('nombre')),
            "cliente_email": pedido_encontrado.get('cliente_email', usuario.get('email')),
            "items": [],
            "total": 0,
            "estado": "Cancelado",
            "direccion": pedido_encontrado.get('direccion', 'Dirección no registrada'),
            "telefono": pedido_encontrado.get('telefono', 'S/N')
        }
        api_actualizar_pedido_cliente(token, pedido_id, datos_cancelado)
        messages.info(request, "Tu pedido se quedó sin productos y fue cancelado.")
        return redirect('mis_pedidos')

    # Recalculamos el total
    nuevo_total = sum(float(i.get('precio_unitario', 0)) * int(i.get('cantidad', 1)) for i in nuevos_items)

    datos_actualizados = {
        "cliente_nombre": pedido_encontrado.get('cliente_nombre', usuario.get('nombre')),
        "cliente_email": pedido_encontrado.get('cliente_email', usuario.get('email')),
        "items": nuevos_items,
        "total": nuevo_total,
        "estado": "Pendiente",
        "direccion": pedido_encontrado.get('direccion', 'Dirección no registrada'),
        "telefono": pedido_encontrado.get('telefono', 'S/N')
    }

    exito, _ = api_actualizar_pedido_cliente(token, pedido_id, datos_actualizados)
    if exito:
        messages.success(request, "Pedido actualizado exitosamente.")
    else:
        messages.error(request, "Error al actualizar el pedido.")

    return redirect('mis_pedidos')

def cancelar_pedido_cliente_view(request, pedido_id):
    """
    Permite al cliente cancelar su propio pedido si está en estado Pendiente,
    liberando el stock y removiéndolo de su vista.
    """
    token = request.session.get('access_token')
    usuario = request.session.get('usuario')

    if not token or not usuario:
        return redirect('login')

    # Llamamos a la API para eliminar/cancelar el pedido del cliente
    exito, _ = api_eliminar_pedido(token, pedido_id)
    
    if exito:
        messages.success(request, "Tu pedido ha sido cancelado exitosamente y los productos regresaron al stock.")
    else:
        messages.error(request, "No se pudo cancelar el pedido. Inténtalo de nuevo.")

    return redirect('mis_pedidos')