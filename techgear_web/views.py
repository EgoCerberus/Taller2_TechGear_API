import unicodedata

from django.shortcuts import render, redirect
from django.contrib import messages
from services import (
    api_listar_productos,
    api_login,
    api_registrar_usuario,
    api_crear_producto,
    api_eliminar_producto,
    api_actualizar_producto
)

try:
    from services import api_recuperar_password
except ImportError:
    api_recuperar_password = None  # todavía no existe en services.py


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
    {'nombre': 'Portátil Pro 15"',       'categoria': 'Portátiles',  'precio': 3200000, 'precio_anterior': 3800000, 'etiqueta': 'Nuevo',  'color': '#3b82f6'},
    {'nombre': 'Smartphone X Ultra',     'categoria': 'Celulares',   'precio': 2400000, 'precio_anterior': 2700000, 'etiqueta': '-11%',   'color': '#8b5cf6'},
    {'nombre': 'Audífonos Wireless ANC', 'categoria': 'Audio',       'precio': 450000,  'precio_anterior': 600000,  'etiqueta': '-25%',   'color': '#0ea5e9'},
    {'nombre': 'Smartwatch Fit 5',       'categoria': 'Wearables',   'precio': 380000,  'precio_anterior': 450000,  'etiqueta': 'Top',    'color': '#10b981'},
    {'nombre': 'Teclado Mecánico RGB',   'categoria': 'Periféricos', 'precio': 260000,  'precio_anterior': 320000,  'etiqueta': '-19%',   'color': '#f59e0b'},
    {'nombre': 'Control Gamer Pro',      'categoria': 'Gaming',      'precio': 210000,  'precio_anterior': 260000,  'etiqueta': 'Gaming', 'color': '#ef4444'},
    {'nombre': 'Cámara 4K Action',       'categoria': 'Cámaras',     'precio': 520000,  'precio_anterior': 650000,  'etiqueta': '-20%',   'color': '#6366f1'},
    {'nombre': 'Router WiFi 6',          'categoria': 'Redes',       'precio': 290000,  'precio_anterior': 340000,  'etiqueta': 'Oferta', 'color': '#14b8a6'},
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

    # 1) Destacados de techstore + productos reales de la API
    destacados = [dict(p) for p in PRODUCTOS_DESTACADOS]
    nombres_destacados = {_norm(p['nombre']) for p in destacados}
    api = [
        dict(p) for p in (api_listar_productos() or [])
        if isinstance(p, dict) and _norm(p.get('nombre')) not in nombres_destacados
    ]
    productos = destacados + api

    # 2) Ubicar cada producto en una categoría del catálogo
    for p in productos:
        grupo = _grupo_de(p.get('categoria'))
        p['grupo'] = grupo['nombre'] if grupo else ''
        p['icono'] = grupo['icono'] if grupo else 'bi-box-seam'

    # 3) Búsqueda (?q=...)
    q = request.GET.get('q', '').strip()
    qn = _norm(q)
    if qn:
        productos = [
            p for p in productos
            if qn in _norm(p.get('nombre')) or qn in _norm(p.get('categoria'))
        ]

    # 4) Categorías con su cantidad de productos (después de buscar)
    categoria_sel = request.GET.get('categoria', '').strip()
    categorias = [
        {**c, 'cantidad': sum(1 for p in productos if p['grupo'] == c['nombre']),
         'activa': c['nombre'] == categoria_sel}
        for c in CATEGORIAS
    ]

    # 5) Filtro por categoría (?categoria=...)
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
            messages.success(request, "Producto creado exitosamente.")
        else:
            messages.error(request, "Error al crear el producto.")
        return redirect('dashboard')
    return render(request, 'crear_producto.html')

def eliminar_producto_view(request, producto_id):
    token = request.session.get('access_token')
    exito, _ = api_eliminar_producto(token, producto_id)
    if exito:
        messages.success(request, "Producto eliminado correctamente.")
    else:
        messages.error(request, "No se pudo eliminar el producto.")
    return redirect('dashboard')

def editar_producto_view(request, producto_id):
    token = request.session.get('access_token')
    if request.method == 'POST':
        datos = {
            "nombre": request.POST.get('nombre'),
            "categoria": request.POST.get('categoria'),
            "precio": float(request.POST.get('precio', 0)),
            "stock": int(request.POST.get('stock', 0))
        }
        exito, _ = api_actualizar_producto(token, producto_id, datos)
        if exito:
            messages.success(request, "Producto actualizado correctamente.")
        else:
            messages.error(request, "Error al actualizar el producto.")
        return redirect('dashboard')

    return render(request, 'editar_producto.html', {'producto_id': producto_id})