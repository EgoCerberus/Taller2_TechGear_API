"""
URL configuration for techgear_web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
import views # Importa las vistas desde el mismo directorio

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('catalogo/', views.catalogo_view, name='catalogo'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('recuperar/', views.recuperar_view, name='recuperar'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/crear/', views.crear_producto_view, name='crear_producto'),
    path('dashboard/eliminar/<str:producto_id>/', views.eliminar_producto_view, name='eliminar_producto'),
    path('dashboard/editar/<str:producto_id>/', views.editar_producto_view, name='editar_producto'),
    path('dashboard/pedidos/', views.lista_pedidos_view, name='lista_pedidos'),
    path('dashboard/pedidos/actualizar/<str:pedido_id>/', views.actualizar_estado_pedido_view, name='actualizar_estado_pedido'),
    path('mis-pedidos/', views.mis_pedidos_view, name='mis_pedidos'),
    path('catalogo/agregar/', views.agregar_pedido_view, name='agregar_pedido'),
    path('admin-pedidos/eliminar/<str:pedido_id>/', views.eliminar_pedido_admin_view, name='eliminar_pedido_admin'),
    path('mis-pedidos/item/<str:pedido_id>/<str:producto_id>/<str:accion>/', views.modificar_item_pedido_view, name='modificar_item_pedido'),
    path('mis-pedidos/cancelar/<str:pedido_id>/', views.cancelar_pedido_cliente_view, name='cancelar_pedido_cliente'),
]

# Servir archivos estáticos en desarrollo (DEBUG = True)
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()