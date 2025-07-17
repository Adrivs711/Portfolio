import requests
import streamlit as st
import time
import logging
from typing import Dict,Union, Any
import re

# Configuración de logging para facilitar la depuración
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes de configuración
URL = "http://localhost:8000"
TIMEOUT = 10  # Timeout para las peticiones en segundos

# ====================================================
# Funciones de API para comunicación con el backend
# ====================================================

def make_api_request(endpoint: str, data: Dict[str, Any], timeout: int = TIMEOUT) -> Dict[str, Any]:
    """
    Función centralizada para realizar peticiones a la API del backend.
    
    Args:
        endpoint: Ruta del endpoint a llamar (sin incluir la URL base)
        data: Diccionario con los datos a enviar en formato JSON
        timeout: Tiempo máximo de espera para la petición en segundos
        
    Returns:
        Respuesta JSON de la API o diccionario con error
        
    Raises:
        No lanza excepciones, pero devuelve un diccionario con status=False y mensaje de error
    """
    try:
        logger.info(f"Llamando a endpoint: {endpoint} con datos: {data}")
        response = requests.post(
            f"{URL}/{endpoint}",
            json=data,
            timeout=timeout
        )
        
        # Verificar si la respuesta fue exitosa
        if response.status_code == 200:
            logger.info(f"Respuesta exitosa de {endpoint}")
            return {"status": True, "data": response.json()}
        else:
            logger.error(f"Error en respuesta: {response.status_code} - {response.text}")
            return {"status": False, "error": f"Error {response.status_code}: {response.text}"}
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al conectar con {endpoint}")
        return {"status": False, "error": "El servidor no responde. Inténtalo más tarde."}
    except requests.exceptions.ConnectionError:
        logger.error(f"Error de conexión al llamar a {endpoint}")
        return {"status": False, "error": "No se pudo conectar con el servidor."}
    except Exception as e:
        logger.error(f"Error inesperado en {endpoint}: {str(e)}")
        return {"status": False, "error": f"Error: {str(e)}"}

def authenticate(email: str, password: str) -> bool:
    """
    Autentica un usuario en el sistema.
    
    Args:
        email: Email del usuario
        password: Contraseña del usuario
        
    Returns:
        True si la autenticación fue exitosa, False en caso contrario
    """
    response = make_api_request("login", {"email": email, "password": password})
    return response.get("status", False) and response.get("data", {}).get("status", False)

def register(email: str, password: str) -> Union[bool, str]:
    """
    Registra un nuevo usuario en el sistema.
    
    Args:
        email: Email del nuevo usuario
        password: Contraseña del nuevo usuario
        
    Returns:
        True si el registro fue exitoso, mensaje de error en caso contrario
    """
    response = make_api_request("register", {"email": email, "password": password})
    
    if response.get("status", False) and response.get("data", {}).get("status", False):
        return True
    else:
        return response.get("error", "Error desconocido al registrar")

def inscribirse(id_curso: str, *args) -> None:
    """
    Inscribe al usuario en un curso, actualizando su perfil de recomendaciones.
    Este proceso implica dos operaciones:
    1. Actualizar el embedding del usuario mezclándolo con el del curso
    2. Añadir el curso a la lista de cursos del usuario
    
    Args:
        id_curso: ID del curso a inscribir
        *args: Argumentos adicionales para compatibilidad con callbacks de Streamlit
    """
    # Verificar que el usuario tiene sesión activa
    if not st.session_state.get("email"):
        st.error("Debes iniciar sesión para inscribirte en un curso")
        return
    
    email = st.session_state.email
    
    # 1. Actualizar embedding del usuario
    embedding_result = make_api_request(
        "update_embeddings_user", 
        {"email": email, "id_curso": int(id_curso)}
    )
    
    if not embedding_result.get("status", False):
        st.error(f"Error al actualizar perfil: {embedding_result.get('error', 'Error desconocido')}")
        return
    
    # 2. Añadir curso a la lista del usuario
    courses_result = make_api_request(
        "update_courses_user", 
        {"email": email, "id_curso": int(id_curso)}
    )
    
    if not courses_result.get("status", False):
        st.error(f"Error al añadir curso: {courses_result.get('error', 'Error desconocido')}")
        return
    
    # Mostrar mensaje de éxito
    st.success("¡Inscripción exitosa!")
    time.sleep(1)  # Pequeña pausa para que el usuario pueda ver el mensaje

# ====================================================
# Funciones de la interfaz de usuario
# ====================================================

def display_course(course: Dict[str, Any], show_inscription: bool = True, unique_id: str = "") -> None:
    """
    Muestra la información de un curso en un formato expandible.
    
    Args:
        course: Diccionario con la información del curso
        show_inscription: Si se debe mostrar o no el botón de inscripción
        unique_id: Identificador adicional para garantizar claves únicas en widgets
    """
    # Obtener el título del curso - puede estar en 'name' o 'nombre' según el endpoint
    course_title = course.get("name", course.get("nombre", "Curso sin título"))
    
    with st.expander(course_title):
        st.write(f"**Instructor:** {course.get('instructor', 'No especificado')}")
        st.write(f"**Fecha de inicio:** {course.get('fecha_inicio', 'No especificada')}")
        st.write(f"**Nivel:** {course.get('nivel', 'No especificado')}")
        st.write(f"**Duración:** {course.get('duracion', 'No especificada')}")
        st.write(f"**Formato:** {course.get('formato', 'No especificado')}")
        st.write(f"**Descripción:** {course.get('descripcion', 'Sin descripción')}")
        
        if show_inscription:
            course_id = str(course.get("id", "0"))
            button_key = f"inscribir_{course_id}_{unique_id}"
            if st.button("Inscribirse", key=button_key, on_click=inscribirse, args=(course_id,)):
                st.rerun()

def login_screen() -> None:
    """
    Muestra la pantalla de inicio de sesión y registro.
    Maneja el proceso completo de autenticación y registro de usuarios.
    """
    st.title("Inicio de sesión")
    
    tab1, tab2 = st.tabs(["Iniciar sesión", "Registrarse"])
    
    # Pestaña de inicio de sesión
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Contraseña", type="password", key="login_password")
        
        if st.button("Iniciar sesión"):
            if not email or not password:
                st.error("Por favor completa todos los campos")
            else:
                with st.spinner("Verificando credenciales..."):
                    auth_result = authenticate(email, password)
                
                if auth_result:
                    st.session_state.logged_in = True
                    st.session_state.email = email
                    st.success(f"Bienvenido, {email}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
    
    # Pestaña de registro
    with tab2:
        reg_email = st.text_input("Email", key="register_email")
        reg_password = st.text_input("Contraseña", type="password", key="register_password")
        confirm_password = st.text_input("Confirmar contraseña", type="password")
        
        if st.button("Registrarse"):
            if not reg_email or not reg_password:
                st.error("Por favor completa todos los campos")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", reg_email):
                st.error("Por favor ingresa un email válido")
            elif reg_password != confirm_password:
                st.error("Las contraseñas no coinciden")
            else:
                with st.spinner("Registrando usuario..."):
                    result = register(reg_email, reg_password)
                
                if result is True:
                    st.success("Usuario registrado exitosamente!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Error al registrar el usuario: {result}")

def chat_tab() -> None:
    """
    Muestra la pestaña de chat e implementa la funcionalidad de conversación con el asistente.
    """
    if "messages" not in st.session_state:
        print(f"st.session_state.email: {st.session_state.email}")
        try:
            response = requests.get(f"{URL}/get_history/{st.session_state.email}")
            if len(response.json()[str(st.session_state.email)]["hist"]) == 0:
                st.session_state.messages = [{"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte hoy?"}]
            else:
                st.session_state.messages = response.json()[str(st.session_state.email)]["hist"]
        except:
            st.session_state.messages = [{"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte hoy?"}]

    # Mostrar mensajes anteriores
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada del usuario
    input_user = st.chat_input("Haz una pregunta")
    if input_user:
        # Obtener contexto de conversación toda la conversacion
        contexto = st.session_state.messages[:]
        
        # Mostrar mensaje del usuario
        with st.chat_message("user"):
            st.markdown(input_user)
            st.session_state.messages.append({"role": "user", "content": input_user})

        # Procesar y mostrar respuesta del asistente
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                response = make_api_request("chat", {"message": input_user, "contexto": contexto, "email": st.session_state.email})
            
            if not response.get("status", False):
                st.error(f"Error al conectar con el servidor: {response.get('error', 'Error desconocido')}")
                return
            
            data = response.get("data", {})
            
            # Determinar tipo de respuesta: texto o cursos
            if "coursesCount" not in data:
                # Respuesta de texto
                ai_response = data.get("respuesta", "Lo siento, no pude generar una respuesta.")
                st.markdown(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
            elif data.get("coursesCount", 0) > 0:
                # Mostrar cursos encontrados
                st.write("Cursos disponibles:")
                for i, course in enumerate(data.get("courses", [])):
                    display_course(course, unique_id=f"chat_{len(st.session_state.messages)}_{i}")
            else:
                # No se encontraron cursos
                message = "Lo siento pero no he encontrado cursos que puedan ayudarte"
                st.markdown(message)
                st.session_state.messages.append({"role": "assistant", "content": message})

    # Botón para limpiar historial
    if st.button("Limpiar historial"):
        try:
            response = requests.delete(f"{URL}/clear_history/{st.session_state.email}")
            if response.status_code == 200:
                del st.session_state.messages
                st.success("Historial borrado exitosamente")
                st.rerun()
            else:
                st.error("Error al borrar el historial")
        except Exception as e:
            st.error(f"Error al conectar con el servidor: {str(e)}")

def recommended_courses_tab() -> None:
    """
    Muestra la pestaña de cursos recomendados para el usuario.
    """
    st.write("Cursos recomendados")
    
    with st.spinner("Cargando recomendaciones..."):
        response = make_api_request(
            "recommended_courses", 
            {"email": st.session_state.email}
        )
    
    if not response.get("status", False):
        st.error(f"Error al obtener recomendaciones: {response.get('error', 'Error desconocido')}")
        return
    
    # Mostrar cursos recomendados
    courses = response.get("data", {}).get("courses", [])
    if not courses:
        st.info("No hay recomendaciones disponibles por el momento.")
        return
    
    # Mostrar cada curso recomendado
    for course in courses:
        display_course(course)

def my_courses_tab() -> None:
    """
    Muestra la pestaña con los cursos en los que está inscrito el usuario.
    """
    st.write("Mis cursos")
    
    with st.spinner("Cargando tus cursos..."):
        response = make_api_request(
            "my_courses", 
            {"email": st.session_state.email}
        )
    
    if not response.get("status", False):
        st.error(f"Error al obtener tus cursos: {response.get('error', 'Error desconocido')}")
        return
    
    # Mostrar cursos inscritos
    courses = response.get("data", {}).get("courses", [])
    if not courses:
        st.info("No estás inscrito en ningún curso todavía.")
        return
    
    # Mostrar cada curso inscrito (sin botón de inscripción)
    for course in courses:
        display_course(course, show_inscription=False)

# ====================================================
# Aplicación principal
# ====================================================

def main():
    """
    Función principal de la aplicación.
    Gestiona la autenticación y muestra la interfaz adecuada según el estado de sesión.
    """
    # Inicializar estado de sesión si es necesario
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.email = None

    # Mostrar pantalla de login o la aplicación principal según el estado de sesión
    if not st.session_state.logged_in:
        login_screen()
    else:
        st.title("Ayudante CFTIC")
        tab3, tab4, tab5 = st.tabs(["Chat", "Cursos recomendados", "Mis cursos"])
        
        with tab3:
            chat_tab()
        
        with tab4:
            recommended_courses_tab()
        
        with tab5:
            my_courses_tab()

# Iniciar la aplicación cuando se ejecuta el script
if __name__ == "__main__":
    main()