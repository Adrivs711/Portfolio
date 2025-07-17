from fastapi import FastAPI, status, HTTPException
from instrucciones import *
from tools import generar_modelo
from clases import *
from operations import *
import logging
import json
import vertexai
from vertexai.language_models import TextEmbeddingModel
from qdrant_client import QdrantClient
from supabase import create_client
from firebase_admin import credentials, firestore
import firebase_admin
import os
from dotenv import load_dotenv

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv(dotenv_path='chatbot.env')

# Constantes para servicios externos
VERTEXAI_PROJECT = os.getenv("VERTEXAI_PROJECT")
VERTEXAI_LOCATION = os.getenv("VERTEXAI_LOCATION")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
CREDENCIALES_FIRESTORE = os.getenv("CREDENCIALES_FIRESTORE")
COLLECTION_NAME = "cursos"

def arranque():
    """
    Inicializa todos los modelos y clientes necesarios para la aplicación.
    - Inicializa VertexAI y carga los modelos de Gemini
    - Crea el modelo de embeddings
    - Inicializa clientes para Qdrant y Supabase
    
    Returns:
        None, pero establece variables globales para toda la aplicación
    
    Raises:
        ValueError: Si hay errores durante la inicialización de los servicios
    """
    try:
        global gemini_keywords, gemini_revision, text_embedding_model, gemini_general, qdrant_client, sup, db
        
        # Inicializar servicio de VertexAI
        logger.info("Inicializando VertexAI...")
        vertexai.init(project=VERTEXAI_PROJECT, location=VERTEXAI_LOCATION)
        
        # Cargar modelos de Gemini con sus respectivas instrucciones
        logger.info("Cargando modelos Gemini...")
        gemini_keywords = generar_modelo(instrucciones_keywords)
        gemini_revision = generar_modelo(instrucciones_revision)
        gemini_general = generar_modelo(instrucciones_general)
        
        # Cargar modelo de embeddings
        logger.info("Cargando modelo de embeddings...")
        text_embedding_model = TextEmbeddingModel.from_pretrained("text-multilingual-embedding-002")
        
        # Inicializar cliente Qdrant para búsqueda vectorial
        logger.info("Conectando a Qdrant...")
        qdrant_client = QdrantClient(
            url=QDRANT_URL, 
            api_key=QDRANT_API_KEY,
        )
        
        # Inicializar cliente Supabase para gestión de usuarios
        logger.info("Conectando a Supabase...")
        sup = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )
        
        # Inicializar cliente Firebase para histórico
        logger.info("Conectando a Firebase...")
        cred = credentials.Certificate(CREDENCIALES_FIRESTORE)  #Este archivo se descarga entero en la pestaña "Cuentas de servicio", haz clic en "Generar nueva clave privada"
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        logger.info("Inicialización completada con éxito")
    except Exception as e:
        logger.error(f"Error durante la inicialización: {e}")
        raise ValueError(f"Error al iniciar las conexiones: {e}")

# Crear la aplicación FastAPI con función de arranque
app = FastAPI(on_startup=[arranque])


@app.get("/get_history/{email}")
def extraer_historial(email:str) -> dict: 
    """
    Llama a la base de datos de histórico de conversaciones, filtra por usuario.
    Devuelve las conversaciones en un diccionario.
    """
    #Histórico de las conversaciones
    docs = db.collection("chat_history").document(email).get()
    print("docctype:",type(docs))
    print("docs: ",docs)
    return {docs.id:docs.to_dict()}

@app.delete("/clear_history/{email}")
def clear_history(email: str):
    try:
        db.collection("chat_history").document(email).update({"hist": [{"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte hoy?"}]})
        return {"content": "Historial borrado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



def handle_error(e: Exception, operation: str, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR):
    """
    Maneja errores de forma centralizada para reducir código duplicado.
    
    Args:
        e: La excepción capturada
        operation: Descripción de la operación que falló
        status_code: Código de estado HTTP a devolver
    
    Raises:
        HTTPException: Con el mensaje y código de estado apropiados
    """
    logger.error(f"Error en {operation}: {e}")
    raise HTTPException(status_code=status_code, detail=f"Error en {operation}")

@app.post("/chat")
def chat(message: Mensaje):
    """
    Endpoint para procesar mensajes del usuario y devolver cursos relevantes.
    Sigue un pipeline de procesamiento:
    1. Extrae keywords y tipo de búsqueda del mensaje
    2. Si es búsqueda general, consulta a Gemini directamente
    3. Para búsquedas específicas, realiza búsqueda vectorial
    4. Revisa resultados con LLM para filtrar los más relevantes
    5. Adapta la respuesta al formato esperado por el cliente
    
    Args:
        message: Objeto Mensaje con el texto del usuario y contexto
    
    Returns:
        FinalOutput: Lista de cursos relevantes
    """
    try:
        # Preparar prompt con el contexto y la consulta actual
        mensaje = message.message
        contexto = message.contexto
        email = message.email
        logger.info(f"Recibida consulta: {mensaje[:50]}...")
        prompt = f"###Conversación previa que debes tener en cuenta para responder: {str(contexto)}\n###Consulta actual: {mensaje}"
    except Exception as e:
        return handle_error(e, "preparación del mensaje")

    try:
        # Extraer keywords y determinar tipo de búsqueda con Gemini
        logger.info("Extrayendo keywords y tipo de búsqueda...")
        search_result = search_keywords(prompt=prompt, gemini_keywords=gemini_keywords)
        keywords = search_result["keywords"]
        tipo_busqueda = search_result["busqueda"]
        logger.info(f"Keywords extraídas: {keywords}")
        logger.info(f"Tipo de búsqueda: {tipo_busqueda}")
    except Exception as e:
        return handle_error(e, "extracción de keywords")

    # Si es búsqueda general, usar modelo general sin búsqueda vectorial
    if tipo_busqueda == "busqueda general":
        logger.info("Ejecutando búsqueda general con Gemini...")
        try:
            respuesta = gemini_general.generate_content([prompt])
            # Actualizar historial, incluye la pregunta actual del usuario y la respuesta del LLM
            nuevos_mensajes = [ {"role": "user", "content": mensaje}, {"role": "assistant", "content":json.loads(respuesta.text)["respuesta"]}]
            doc_ref = db.collection("chat_history").document(email)
            doc_ref.update({"hist": firestore.ArrayUnion(nuevos_mensajes)})
            print("Historial actualizado") 
            return json.loads(respuesta.text)
        except Exception as e:
            return handle_error(e, "generación de respuesta general")

    try:
        # Buscar cursos relevantes mediante búsqueda vectorial
        logger.info("Realizando búsqueda vectorial...")
        resultados = busqueda_vectorial(
            keywords=keywords, 
            embedding_model=text_embedding_model, 
            qdrant_client=qdrant_client
        )
        
        if not resultados:
            logger.info("No se encontraron cursos relevantes")
            return FinalOutput(coursesCount=0, courses=[])
    except Exception as e:
        return handle_error(e, "búsqueda de cursos")

    try:
        # Revisar resultados con LLM para filtrar los más relevantes
        logger.info("Revisando resultados con LLM...")
        cursos_seleccionados = revision_llm(
            prompt=prompt,
            productos=resultados,
            gemini_revision=gemini_revision
        )
        
        if not cursos_seleccionados:
            logger.info("No se seleccionaron cursos después de la revisión")
            nuevos_mensajes = [ {"role": "user", "content": mensaje}, {"role": "assistant", "content":"Lo siento pero no he encontrado cursos que puedan ayudarte"}]
            doc_ref = db.collection("chat_history").document(email)
            doc_ref.update({"hist": firestore.ArrayUnion(nuevos_mensajes)})
            print("Historial actualizado") 
            return FinalOutput(coursesCount=0, courses=[])
    except Exception as e:
        return handle_error(e, "revisión de cursos con LLM")
    
    # Adaptar los resultados al formato esperado por el cliente
    logger.info("Adaptando respuesta al formato final...")
    # Usa list comprehension para convertir resultados en formato Course
    salida_final = [
        Course(
            id=str(i),
            name=j["nombre"],
            score=j["score"],
            instructor=j["instructor"],
            fecha_inicio=j["fecha_inicio"],
            nivel=j["nivel"],
            duracion=j["duracion"],
            formato=j["formato"],
            descripcion=j["descripcion"]
        ) 
        for i in cursos_seleccionados 
        for j in resultados 
        if str(i) == str(j["id"])
    ]
    
    # Crear la estructura final de respuesta
    salida_adaptada = FinalOutput(
        coursesCount=len(salida_final), 
        courses=salida_final
    )
    
    logger.info(f"Respuesta generada con {len(salida_final)} cursos")
    salida_final_str = str([f"Curso: {i.name}" for i in salida_final])
     # Actualizar historial, incluye la pregunta actual del usuario y la respuesta del LLM
    nuevos_mensajes = [ {"role": "user", "content": mensaje}, {"role": "assistant", "content": salida_final_str}]
    doc_ref = db.collection("chat_history").document(email)
    doc_ref.update({"hist": firestore.ArrayUnion(nuevos_mensajes)})

    return salida_adaptada


@app.post("/login")
def log_in(user: User):
    """
    Autentica a un usuario verificando sus credenciales en Supabase.
    
    Args:
        user: Objeto User con email y password
        
    Returns:
        dict: Estado de la operación
        
    Raises:
        HTTPException: Si las credenciales son incorrectas o hay un error
    """
    try:
        email = user.email
        password = user.password
        logger.info(f"Intento de login para: {email}")
    except Exception as e:
        return handle_error(e, "obtención de datos de usuario")
    
    try:
        # Verificar credenciales en Supabase
        user_exists = verify_user_in_supabase(email, password, sup)
        if not user_exists:
            logger.warning(f"Intento de login fallido para: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Usuario o contraseña incorrectos"
            )
            
        logger.info(f"Login exitoso para: {email}")
        return {"status": True}
    except HTTPException:
        # Reenviar excepciones HTTP tal cual
        raise
    except Exception as e:
        return handle_error(e, "autenticación")


@app.post("/register")
def register(user: User):
    """
    Registra un nuevo usuario en Supabase.
    
    Args:
        user: Objeto User con email y password
        
    Returns:
        dict: Estado de la operación
        
    Raises:
        HTTPException: Si el usuario ya existe o hay un error
    """
    try:
        email = user.email
        password = user.password
        logger.info(f"Intento de registro para: {email}")
    except Exception as e:
        return handle_error(e, "obtención de datos de usuario")
    
    try:
        # Crear nuevo usuario en Supabase
        user_created = create_user_in_supabase(email, password, sup)
        conversation_created  = create_conversation_in_firestore(email, db)
        if not user_created:
            logger.warning(f"Error al crear usuario: {email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="Usuario ya registrado"
            )
        if not conversation_created:
            logger.warning(f"Error al crear conversación: {email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="Error al crear conversación"
            )
            
        logger.info(f"Usuario registrado con éxito: {email}")
        return {"status": True}
    except ValueError as e:
        # Manejar error específico cuando el usuario ya existe
        logger.warning(f"Usuario ya existe: {email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=str(e)
        )
    except HTTPException:
        # Reenviar excepciones HTTP tal cual
        raise
    except Exception as e:
        return handle_error(e, "registro de usuario")


@app.post("/recommended_courses")
def get_recommended_courses(user: User):
    """
    Obtiene cursos recomendados para un usuario específico basados en su embedding.
    
    Args:
        user: Objeto User con email
        
    Returns:
        FinalOutput: Lista de cursos recomendados
    """
    try:
        email = user.email
        logger.info(f"Obteniendo recomendaciones para: {email}")
    except Exception as e:
        return handle_error(e, "obtención de datos de usuario")
    
    try:
        # Obtener recomendaciones basadas en embedding del usuario
        resultados = recommended(email, qdrant_client, sup)
        logger.info(f"Se encontraron {len(resultados)} cursos recomendados")
        
        # Convertir resultados al formato esperado por el cliente
        salida_final = [
            Course(
                id=str(j["id"]),
                name=j["nombre"],
                score=j["score"],
                instructor=j["instructor"],
                fecha_inicio=j["fecha_inicio"],
                nivel=j["nivel"],
                duracion=j["duracion"],
                formato=j["formato"],
                descripcion=j["descripcion"]
            ) 
            for j in resultados
        ]
        
        # Crear estructura final de respuesta
        salida_adaptada = FinalOutput(
            coursesCount=len(salida_final), 
            courses=salida_final
        )
        
        return salida_adaptada
    except Exception as e:
        return handle_error(e, "obtención de recomendaciones")


@app.post("/update_embeddings_user")
def update(user: User):
    """
    Actualiza el embedding de un usuario basado en un curso seleccionado.
    Esto mejora las recomendaciones futuras.
    
    Args:
        user: Objeto User con email y id_curso
        
    Returns:
        bool: True si la actualización fue exitosa
    """
    try:
        email = user.email
        id_curso = user.id_curso
        logger.info(f"Actualizando embedding para usuario {email} con curso {id_curso}")
    except Exception as e:
        return handle_error(e, "obtención de datos de usuario")
    
    try:
        # Actualizar embedding del usuario basado en el curso seleccionado
        success = update_embedding_user(email, id_curso, qdrant_client, sup)
        if success:
            logger.info(f"Embedding actualizado con éxito para: {email}")
            return True
        else:
            logger.warning(f"Fallo al actualizar embedding para: {email}")
            return False
    except Exception as e:
        return handle_error(e, "actualización de embedding")


@app.post("/update_courses_user")
def update_courses_user(user: User):
    """
    Añade un curso a la lista de cursos inscritos de un usuario.
    
    Args:
        user: Objeto User con email y id_curso
        
    Returns:
        bool: True si la actualización fue exitosa
    """
    try:
        email = user.email
        id_curso = user.id_curso
        logger.info(f"Añadiendo curso {id_curso} para usuario {email}")
    except Exception as e:
        return handle_error(e, "obtención de datos de usuario")
    
    try:
        # Añadir curso a la lista de cursos del usuario
        success = update_course_user(email, id_curso, sup)
        if success:
            logger.info(f"Curso añadido con éxito para usuario: {email}")
            return True
        else:
            logger.warning(f"Fallo al añadir curso para usuario: {email}")
            return False
    except Exception as e:
        return handle_error(e, "actualización de cursos")


@app.post("/my_courses")
def my__courses(user: User):
    """
    Obtiene la lista de cursos en los que está inscrito un usuario.
    
    Args:
        user: Objeto User con email
        
    Returns:
        dict: Lista de cursos inscritos
    """
    try:
        email = user.email
        logger.info(f"Obteniendo cursos para usuario: {email}")
    except Exception as e:
        return handle_error(e, "obtención de datos de usuario")
    
    try:
        # Obtener lista de cursos del usuario
        cursos = my_courses(email, qdrant_client, sup)
        logger.info(f"Se encontraron {len(cursos)} cursos para usuario: {email}")
        return {"courses": cursos}
    except Exception as e:
        return handle_error(e, "obtención de cursos")