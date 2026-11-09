# 🚀 TechGear - Plataforma E-Commerce Híbrida (Monorepo)

**TechGear** es una solución web de comercio electrónico moderna, rápida e integrada mediante una arquitectura desacoplada. Utiliza **FastAPI** como backend dinámico respaldado por **MongoDB Atlas**, y un frontend responsive en **Django** con integración fluida de Bootstrap y consumo de servicios RESTful.

---

## 🛠️ Arquitectura y Tecnologías

* **Backend (API REST):** [FastAPI](https://fastapi.tiangolo.com/) | Deployed on **Render**
* **Frontend (Web Application):** [Django](https://www.djangoproject.com/) | Deployed on **Vercel**
* **Base de Datos:** [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) (Colecciones `usuarios` y `productos`)
* **Autenticación:** Hashing de credenciales seguro con `Passlib` / `Bcrypt` y gestión de sesiones mediante roles (`es_admin`, `rol`).
* **Estilos:** Bootstrap 5, Bootstrap Icons y CSS customizado.

---

## ⚙️ Características Principales

1. **Catálogo Dinámico de Productos:**
   - Consulta dinámica de productos desde MongoDB Atlas a través de endpoints de FastAPI.
   - Filtrado interactivo por categorías, ordenamiento dinámico por precio/nombre y soporte de búsqueda en tiempo real.

2. **Flujo Completo de Autenticación:**
   - Registro de usuarios con encriptación de contraseñas.
   - Inicio de sesión validado mediante consumo de API (JSON Payload).
   - Control de acceso por roles para funciones de administración.

3. **Panel de Administración (CRUD):**
   - Creación, actualización y eliminación de productos restringido únicamente a usuarios administradores (`es_admin: true`).

---

## 📋 Variables de Entorno

### Backend (FastAPI / Render)
```env
MONGO_URI=mongodb+srv://<usuario>:<password>@<cluster>.mongodb.net/<dbname>?retryWrites=true&w=majority
SECRET_KEY=tu_clave_secreta_aqui
```

### Frontend (Django / Vercel)
```env
API_URL=https://taller2-techgear-api.onrender.com
SECRET_KEY=tu_django_secret_key
DEBUG=False
```

---

## 🚀 Despliegue en Producción

* **Backend API:** Disponible en Render. Documentación interactiva de endpoints accesible en `/docs` (Swagger UI).
* **Frontend Web:** Desplegado de forma continua en Vercel.

---

## 👨‍💻 Desarrollo Local

1. **Clonar repositorio:**
   ```bash
   git clone https://github.com/tu-usuario/techgear-monorepo.git
   cd techgear-monorepo
   ```

2. **Ejecutar Backend (FastAPI):**
   ```bash
   cd api
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

3. **Ejecutar Frontend (Django):**
   ```bash
   cd web
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py runserver
   ```

# 🛒 TechGear - E-commerce & Web Application

Proyecto desarrollado para el programa **Análisis y Desarrollo de Software (ADSO)** del **SENA**. Consiste en una plataforma de comercio electrónico orientada a la venta de tecnología, con una arquitectura híbrida de Django en el frontend/plantillas y conexión a base de datos y servicios backend.

---

## 🌐 Enlaces de Despliegue
* **Frontend (Vercel):** [https://taller2-tech-gear-api.vercel.app/](https://taller2-tech-gear-api.vercel.app/)
* **Backend / API (Render):** [https://taller2-tech-gear-api.onrender.com](https://taller2-tech-gear-api.onrender.com)

---

## 📱 Diseño Responsivo
El proyecto cuenta con un diseño **100% responsivo** implementado con **Bootstrap 5.3**, asegurando una experiencia de usuario fluida, adaptada y optimizada para dispositivos móviles, tablets y equipos de escritorio.

---

## 🗂️ Estructura del Proyecto (Encarpetado)

```text
Taller2_Python_TechGear/
│
└── techgear/
    └── techgear_web/
        ├── manage.py
        ├── techgear/               # Configuración principal de Django (settings, urls, wsgi)
        │   ├── __init__.py
        │   ├── settings.py
        │   ├── urls.py
        │   └── wsgi.py
        │
        └── Store/                  # Aplicación principal de la tienda
            ├── migrations/
            ├── static/
            │   └── img/            # Imágenes locales PNG transparentes (portatil, smartphone, etc.)
            ├── templates/          # Plantillas HTML (base.html, catalog.html, etc.)
            ├── admin.py
            ├── apps.py
            ├── models.py
            ├── urls.py
            └── views.py