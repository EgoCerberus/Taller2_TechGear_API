import requests

API_URL = "http://127.0.0.1:8000"  # URL base de tu FastAPI (o tu URL de Render)

def api_listar_productos():
    try:
        response = requests.get(f"{API_URL}/productos")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

def api_login(email, password):
    try:
        response = requests.post(f"{API_URL}/usuarios/login", json={"email": email, "password": password})
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

def api_registrar_usuario(nombre, email, password):
    try:
        response = requests.post(f"{API_URL}/usuarios/registro", json={
            "nombre": nombre,
            "email": email,
            "password": password
        })
        return response.status_code == 201, response.json()
    except Exception as e:
        return False, {"detail": str(e)}
    
def api_crear_producto(token, datos_producto):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(f"{API_URL}/productos", json=datos_producto, headers=headers)
        return response.status_code == 200 or response.status_code == 201, response.json()
    except Exception as e:
        return False, {"detail": str(e)}

def api_actualizar_producto(token, producto_id, datos_producto):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.put(f"{API_URL}/productos/{producto_id}", json=datos_producto, headers=headers)
        return response.status_code == 200, response.json()
    except Exception as e:
        return False, {"detail": str(e)}

def api_eliminar_producto(token, producto_id):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.delete(f"{API_URL}/productos/{producto_id}", headers=headers)
        return response.status_code == 200, response.json()
    except Exception as e:
        return False, {"detail": str(e)}