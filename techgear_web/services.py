import requests

# URL base de tu FastAPI (o tu URL de Render)
# API_URL = "http://127.0.0.1:8001" 
API_URL = "https://taller2-techgear-api.onrender.com"
# API_URL = "http://127.0.0.1:8000" 

def api_listar_productos():
    try:
        response = requests.get(f"{API_URL}/productos") 
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error de conexión: {e}")
    return []

def api_login(email, password):
    try:
        response = requests.post(f"{API_URL}/usuarios/login", json={"email": email, "password": password})
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print("ERROR:", e)
    return None

def api_registrar_usuario(nombre, email, password):
    try:
        response = requests.post(
            f"{API_URL}/usuarios/registro", 
            json={
                "nombre": nombre,
                "email": email,
                "password": password
            },
            timeout=5
        )
        
        # Imprime en la consola de Django lo que realmente respondió FastAPI
        print("STATUS CODE DE FASTAPI:", response.status_code)
        print("TEXTO RESPUESTA DE FASTAPI:", response.text)
        
        # Si la respuesta está vacía o no es JSON, evitamos que explote
        if not response.text.strip():
            return response.status_code in [200, 201], {"detail": "Respuesta vacía de la API"}
            
        return response.status_code in [200, 201], response.json()
    except Exception as e:
        print("ERROR EN SERVICES:", str(e))
        return False, {"detail": str(e)}

def api_recuperar_password(email):
    """Envía la solicitud de recuperación de contraseña a la API"""
    try:
        response = requests.post(f"{API_URL}/usuarios/recuperar", json={"email": email}, timeout=5)
        return response.status_code in [200, 201], response.json() if response.text.strip() else {}
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
    
    # PEDIDOS #
    
def api_listar_pedidos(token):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{API_URL}/pedidos/", headers=headers)
        return response.json() if response.status_code == 200 else []
    except Exception:
        return []

def api_actualizar_estado_pedido(token, pedido_id, nuevo_estado):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.patch(
            f"{API_URL}/pedidos/{pedido_id}/estado",
            json={"estado": nuevo_estado},
            headers=headers
        )
        return response.status_code == 200, response.json()
    except Exception:
        return False, {}
    
def api_crear_pedido(token, datos_pedido):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(f"{API_URL}/pedidos/", json=datos_pedido, headers=headers, timeout=5)
        print("STATUS CREAR PEDIDO:", response.status_code)
        print("RESPUESTA CREAR PEDIDO:", response.text)
        return response.status_code in [200, 201], response.json() if response.text.strip() else {}
    except Exception as e:
        print("ERROR EN api_crear_pedido:", str(e))
        return False, {"detail": str(e)}
    
def api_actualizar_pedido_cliente(token, pedido_id, datos_pedido):
    """
    Envía una solicitud PUT para actualizar un pedido existente en la API 
    (útil cuando el cliente acumula o modifica productos en su pedido pendiente).
    """
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.put(f"{API_URL}/pedidos/{pedido_id}", json=datos_pedido, headers=headers, timeout=5)
        return response.status_code in [200, 201], response.json() if response.text.strip() else {}
    except Exception as e:
        return False, {"detail": str(e)}
    
def api_eliminar_pedido(token, pedido_id):
    """
    =================================================================
    SERVICIO: ELIMINAR PEDIDO (ADMIN)
    Envía una petición DELETE a la API para borrar un pedido específico.
    =================================================================
    """
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.delete(f"{API_URL}/pedidos/{pedido_id}", headers=headers)
        # Retorna True si se elimina con éxito (200 OK o 204 No Content)
        return response.status_code in [200, 204], response.json() if response.content else {}
    except Exception as e:
        return False, {"detail": str(e)}
    
def api_eliminar_pedido(token, pedido_id):
    """
    =================================================================
    SERVICIO: ELIMINAR PEDIDO (ADMIN)
    Envía una petición DELETE a la API de FastAPI para eliminar 
    un pedido específico del sistema de forma permanente.
    Incluye trazas de depuración (print) para identificar errores en consola.
    =================================================================
    """
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.delete(f"{API_URL}/pedidos/{pedido_id}", headers=headers)
        return response.status_code in [200, 204], response.json() if response.content else {}
    except Exception as e:
        return False, {"detail": str(e)}
        
        # Imprime en la consola de Django la respuesta exacta de FastAPI
        print(f"DEBUG DELETE RESPUESTA - Status: {response.status_code}")
        print(f"DEBUG DELETE RESPUESTA - Body: {response.text}")
        
        # Retorna True si el código es exitoso (200 OK o 204 No Content)
        if response.status_code in [200, 204]:
            return True, response.json() if response.text.strip() else {}
        else:
            return False, response.json() if response.text.strip() else {"detail": response.text}
            
    except Exception as e:
        print(f"DEBUG DELETE EXCEPTION: {e}")
        return False, {"detail": str(e)}