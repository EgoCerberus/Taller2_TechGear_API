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