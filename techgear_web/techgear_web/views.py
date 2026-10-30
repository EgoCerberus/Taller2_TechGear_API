from django.shortcuts import render, redirect
from django.contrib import messages
from .services import api_listar_productos, api_login, api_registrar_usuario

def catalogo_view(request):
    productos = api_listar_productos()
    usuario = request.session.get('usuario')
    return render(request, 'catalog.html', {'productos': productos, 'usuario': usuario})

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