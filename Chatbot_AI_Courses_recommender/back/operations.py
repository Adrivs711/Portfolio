import json
import logging
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from vertexai.language_models import TextEmbeddingInput
from datetime import datetime
# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def search_keywords(prompt: str, gemini_keywords) -> dict:
    """
    Extrae palabras clave y tipo de búsqueda de un prompt utilizando el modelo Gemini.
    
    Args:
        prompt: Texto de la consulta del usuario con su contexto
        gemini_keywords: Modelo de Gemini configurado para extraer keywords
    
    Returns:
        dict: Diccionario con las keywords extraídas y el tipo de búsqueda identificado
    
    Raises:
        Exception: Si hay problemas durante la generación de contenido
    """
    try:
        logger.debug(f"Enviando prompt a Gemini para extracción de keywords: {prompt[:50]}...")
        content = [prompt]
        response = gemini_keywords.generate_content(content)
        
        # Convertir la respuesta a formato JSON
        result = json.loads(response.text)
        logger.debug(f"Keywords extraídas: {result}")
        return result
    except Exception as e:
        logger.error(f"Error en search_keywords: {e}")
        raise

def revision_llm(prompt: str, productos: list, gemini_revision) -> list:
    """
    Revisa una lista de productos y filtra los más relevantes para la consulta del usuario
    utilizando el modelo Gemini para tomar decisiones inteligentes.
    
    Args:
        prompt: Texto de la consulta del usuario con su contexto
        productos: Lista de productos potencialmente relevantes
        gemini_revision: Modelo de Gemini configurado para revisar relevancia
    
    Returns:
        list: Lista filtrada de IDs de productos relevantes para la consulta
    
    Raises:
        Exception: Si hay problemas durante la generación de contenido
    """
    try:
        logger.debug(f"Enviando {len(productos)} productos a Gemini para revisión...")
        # Crear un único contenido combinando la consulta y los productos
        content = [f"#Conversacion previa y consulta:\n{prompt}\n#Productos a elegir:\n{productos}"]
        response = gemini_revision.generate_content(content)
        
        # Convertir la respuesta a lista de IDs
        result = json.loads(response.text)
        logger.debug(f"Productos seleccionados por Gemini: {result}")
        return result
    except Exception as e:
        logger.error(f"Error en revision_llm: {e}")
        raise

def busqueda_vectorial(keywords: str, embedding_model, qdrant_client) -> list:
    """
    Realiza una búsqueda vectorial en Qdrant utilizando embeddings para encontrar
    cursos semánticamente similares a las keywords proporcionadas.
    
    Args:
        keywords: Texto con palabras clave para la búsqueda
        embedding_model: Modelo de embeddings para convertir texto a vectores
        qdrant_client: Cliente de Qdrant para realizar la búsqueda
    
    Returns:
        list: Lista de cursos similares ordenados por relevancia
    
    Raises:
        Exception: Si hay problemas durante la búsqueda vectorial
    """
    try:
        logger.info(f"Realizando búsqueda vectorial para: '{keywords}'")
        
        # Crear embedding de la consulta (convertir texto a vector)
        input_text = [TextEmbeddingInput(text=keywords, task_type="SEMANTIC_SIMILARITY")]
        embedding_user = list(embedding_model.get_embeddings(input_text, output_dimensionality=768, auto_truncate=False)[0].values)
        
        # Nombre de la colección donde se encuentran los cursos
        collection_name = "cursos"
        logger.debug(f"Colecciones disponibles: {qdrant_client.get_collections()}")
        
        # Realizar la búsqueda vectorial usando el embedding generado
        search_result = qdrant_client.search(
            collection_name=collection_name,
            query_vector=embedding_user,
            limit=10,  # Limitar a 10 resultados más similares
            # score_threshold=0.4,  # Umbral de similaridad mínima (comentado)
            with_payload=True  # Incluir los metadatos de cada curso
        )
        
        # Formatear resultados para devolverlos en un formato consistente
        resultados = []
        for hit in search_result:
            resultados.append({
                "id": hit.payload.get("id"),
                "score": hit.score,
                "nombre": hit.payload.get("nombre"),
                "nivel": hit.payload.get("nivel"),
                "duracion": hit.payload.get("duracion"),
                "formato": hit.payload.get("formato"),
                "instructor": hit.payload.get("instructor"),
                "fecha_inicio": hit.payload.get("fecha_inicio"),
                "descripcion": hit.payload.get("descripcion")
            })
        
        logger.info(f"Búsqueda vectorial encontró {len(resultados)} cursos")
        return resultados
    except Exception as e:
        logger.error(f"Error en busqueda_vectorial: {e}")
        raise

def verify_user_in_supabase(email: str, password: str, supabase_client) -> bool:
    """
    Verifica si existe un usuario con el email y contraseña proporcionados.
    
    Args:
        email: Email del usuario
        password: Contraseña del usuario
        supabase_client: Cliente de Supabase para realizar la consulta
    
    Returns:
        bool: True si el usuario existe y las credenciales son correctas
    
    Raises:
        Exception: Si hay problemas durante la verificación
    """
    try:
        logger.info(f"Verificando usuario: {email}")
        # Consultar la tabla 'users' filtrando por email y password
        response = (supabase_client.table("users")
                    .select("*")
                    .eq("email", email)
                    .eq("password", password)
                    .execute())
        
        # Retornar True si se encontró algún resultado
        exists = bool(response.data)
        logger.info(f"Usuario {email} {'encontrado' if exists else 'no encontrado'}")
        return exists
    except Exception as e:
        logger.error(f"Error al verificar usuario {email}: {e}")
        raise

def create_user_in_supabase(email: str, password: str, supabase_client) -> bool:
    """
    Crea un nuevo usuario en Supabase con un embedding inicial.
    
    Args:
        email: Email del nuevo usuario
        password: Contraseña del nuevo usuario
        supabase_client: Cliente de Supabase para realizar operaciones
    
    Returns:
        bool: True si el usuario fue creado exitosamente
    
    Raises:
        ValueError: Si el usuario ya existe
        Exception: Si hay otros problemas durante la creación
    """
    try:
        logger.info(f"Verificando si ya existe el usuario: {email}")
        # Comprobar si el email ya existe
        check_response = (supabase_client.table("users")
                         .select("email")
                         .eq("email", email)
                         .execute())
        
        if check_response.data:
            logger.warning(f"Intento de crear usuario ya existente: {email}")
            raise ValueError(f"El usuario con email {email} ya existe")
        
        logger.info(f"Creando nuevo usuario: {email}")
        # Si no existe, crear el usuario con un embedding inicial de zeros
        response = (supabase_client.table("users")
                   .insert({"email": email, "password": password, "embeddings": [float(0.0)]*768})
                   .execute())
        
        success = bool(response.data)
        logger.info(f"Usuario {email} {'creado con éxito' if success else 'falló al crearse'}")
        return success
    except ValueError:
        # Re-lanzar ValueError para que sea manejada por el controlador
        raise
    except Exception as e:
        logger.error(f"Error al crear usuario {email}: {e}")
        raise

def search_embedding_user(email: str, supabase_client) -> list:
    """
    Obtiene el embedding de un usuario almacenado en Supabase.
    
    Args:
        email: Email del usuario
        supabase_client: Cliente de Supabase para realizar la consulta
    
    Returns:
        list: Vector de embedding del usuario
    
    Raises:
        Exception: Si hay problemas durante la búsqueda o el usuario no existe
    """
    try:
        logger.info(f"Obteniendo embedding para usuario: {email}")
        response = (supabase_client.table("users")
                   .select("embeddings")
                   .eq("email", email)
                   .execute())
        
        if not response.data:
            logger.warning(f"No se encontró el usuario: {email}")
            raise ValueError(f"No se encontró el usuario con email {email}")
        
        embedding = response.data[0]["embeddings"]
        logger.debug(f"Embedding obtenido para {email}: {len(embedding)} dimensiones")
        return embedding
    except Exception as e:
        logger.error(f"Error al buscar embedding para {email}: {e}")
        raise

def recommended(email: str, qdrant_client, supabase_client) -> list:
    """
    Obtiene cursos recomendados para un usuario basados en su embedding,
    excluyendo los cursos en los que ya está inscrito.
    
    Args:
        email: Email del usuario
        qdrant_client: Cliente de Qdrant para la búsqueda vectorial
        supabase_client: Cliente de Supabase para obtener datos del usuario
    
    Returns:
        list: Lista de cursos recomendados
    
    Raises:
        Exception: Si hay problemas durante el proceso de recomendación
    """
    try:
        logger.info(f"Generando recomendaciones para: {email}")
        # Obtener cursos inscritos para excluirlos de recomendaciones
        response = (supabase_client.table("users")
                   .select("cursos_inscritos")
                   .eq("email", email)
                   .execute())
        
        cursos_inscritos = response.data[0].get("cursos_inscritos", []) if response.data else []
        logger.info(f"Usuario {email} tiene {len(cursos_inscritos) if cursos_inscritos else 0} cursos inscritos")
        
        collection_name = "cursos"
        logger.debug(f"Colecciones disponibles: {qdrant_client.get_collections()}")
        
        # Recuperar el embedding del usuario para buscar cursos similares
        user_embedding = search_embedding_user(email, supabase_client)
        
        # Si el usuario tiene cursos inscritos, excluirlos de la búsqueda
        if cursos_inscritos and cursos_inscritos != []:
            logger.info(f"Excluyendo {len(cursos_inscritos)} cursos ya inscritos de las recomendaciones")
            search_result = qdrant_client.search(
                collection_name=collection_name,
                query_vector=user_embedding,
                limit=5,  # Limitar a 5 recomendaciones
                with_payload=True,
                query_filter=Filter(
                    must_not=[
                        FieldCondition(
                            key='id',
                            match=MatchValue(
                                value=int(curso_id)
                            )
                        ) for curso_id in cursos_inscritos
                    ]
                )
            )
        else:
            # Si no tiene cursos inscritos, recomendar los más similares a su embedding
            logger.info("No hay cursos inscritos, recomendando basado solo en el embedding")
            search_result = qdrant_client.search(
                collection_name=collection_name,
                query_vector=user_embedding,
                limit=5,
                with_payload=True
            )
            
        # Formatear resultados
        resultados = []
        for hit in search_result:
            resultados.append({
                "id": hit.payload.get("id"),
                "score": hit.score,
                "nombre": hit.payload.get("nombre"),
                "nivel": hit.payload.get("nivel"),
                "duracion": hit.payload.get("duracion"),
                "formato": hit.payload.get("formato"),
                "instructor": hit.payload.get("instructor"),
                "fecha_inicio": hit.payload.get("fecha_inicio"),
                "descripcion": hit.payload.get("descripcion")
            })
        
        logger.info(f"Se generaron {len(resultados)} recomendaciones para {email}")
        return resultados
    except Exception as e:
        logger.error(f"Error al generar recomendaciones para {email}: {e}")
        raise

def update_embedding_user(email: str, id_curso: str, qdrant_client, supabase_client) -> bool:
    """
    Actualiza el embedding de un usuario combinándolo con el embedding de un curso seleccionado.
    Esto permite mejorar futuras recomendaciones basándose en los intereses del usuario.
    
    Args:
        email: Email del usuario
        id_curso: ID del curso seleccionado
        qdrant_client: Cliente de Qdrant para obtener el embedding del curso
        supabase_client: Cliente de Supabase para actualizar el embedding del usuario
    
    Returns:
        bool: True si la actualización fue exitosa
    
    Raises:
        ValueError: Si no se encuentra el curso o el usuario
        Exception: Si hay otros problemas durante la actualización
    """
    try:
        logger.info(f"Actualizando embedding de {email} con curso ID {id_curso}")
        
        # Obtener el curso por ID junto con su vector de embedding
        points = qdrant_client.retrieve(
            collection_name="cursos",
            ids=[int(id_curso)],
            with_vectors=True,
            with_payload=True
        )
        
        if not points:
            logger.warning(f"No se encontró el curso con ID {id_curso}")
            raise ValueError(f"No se encontró el curso con ID {id_curso}")
        
        # Extraer el vector del curso
        curso_embedding = points[0].vector
        logger.debug(f"Embedding del curso obtenido: {len(curso_embedding)} dimensiones")
        
        # Obtener el embedding actual del usuario
        user_response = supabase_client.table("users").select("embeddings").eq("email", email).execute()
        
        if not user_response.data:
            logger.warning(f"No se encontró el usuario con email {email}")
            raise ValueError(f"No se encontró el usuario con email {email}")
        
        user_embedding = user_response.data[0]["embeddings"]
        logger.debug(f"Embedding actual del usuario: {len(user_embedding)} dimensiones")
        
        # Calcular la media de los dos embeddings para crear un nuevo embedding
        # que combine los intereses anteriores con el nuevo curso
        new_embedding = [(a + b) / 2 for a, b in zip(user_embedding, curso_embedding)]
        logger.debug(f"Nuevo embedding calculado: {len(new_embedding)} dimensiones")
        
        # Actualizar el embedding del usuario en Supabase
        update_response = supabase_client.table("users").update({"embeddings": new_embedding}).eq("email", email).execute()
        
        success = update_response.data is not None
        logger.info(f"Embedding de {email} {'actualizado con éxito' if success else 'falló al actualizarse'}")
        return success
    except Exception as e:
        logger.error(f"Error al actualizar embedding para {email}: {e}")
        raise

def update_course_user(email: str, id_curso: str, supabase_client) -> bool:
    """
    Añade un curso a la lista de cursos inscritos del usuario.
    
    Args:
        email: Email del usuario
        id_curso: ID del curso a añadir
        supabase_client: Cliente de Supabase para actualizar los datos
    
    Returns:
        bool: True si la actualización fue exitosa
    
    Raises:
        Exception: Si hay problemas durante la actualización
    """
    try:
        logger.info(f"Añadiendo curso {id_curso} a los cursos de usuario {email}")
        
        # Obtener la lista actual de cursos inscritos
        response = (supabase_client.table("users")
                   .select("cursos_inscritos")
                   .eq("email", email)
                   .execute())
        
        cursos_inscritos = response.data[0].get("cursos_inscritos", []) if response.data else []
        logger.debug(f"Cursos actuales: {cursos_inscritos}")
        
        # Actualizar la lista de cursos añadiendo el nuevo
        if cursos_inscritos is not None and cursos_inscritos != []:
            # Si ya tiene cursos, añadir el nuevo a la lista existente
            update_response = (supabase_client.table("users")
                             .update({"cursos_inscritos": cursos_inscritos + [int(id_curso)]})
                             .eq("email", email)
                             .execute())
        else:
            # Si no tiene cursos, crear una nueva lista con este curso
            update_response = (supabase_client.table("users")
                             .update({"cursos_inscritos": [int(id_curso)]})
                             .eq("email", email)
                             .execute())
        
        success = update_response.data is not None
        logger.info(f"Curso {id_curso} {'añadido con éxito' if success else 'falló al añadirse'} para {email}")
        return success
    except Exception as e:
        logger.error(f"Error al añadir curso {id_curso} para {email}: {e}")
        raise

def my_courses(email: str, qdrant_client, supabase_client) -> list:
    """
    Obtiene información detallada de los cursos en los que está inscrito un usuario.
    
    Args:
        email: Email del usuario
        qdrant_client: Cliente de Qdrant para obtener detalles de los cursos
        supabase_client: Cliente de Supabase para obtener IDs de cursos inscritos
    
    Returns:
        list: Lista de cursos inscritos con todos sus detalles
    
    Raises:
        Exception: Si hay problemas durante la consulta
    """
    try:
        logger.info(f"Obteniendo cursos inscritos para: {email}")
        
        # Obtener IDs de cursos inscritos desde Supabase
        user_courses = supabase_client.table("users").select("cursos_inscritos").eq("email", email).execute()
        
        cursos_id = user_courses.data[0]["cursos_inscritos"] if user_courses.data else None
        
        # Si no hay cursos inscritos, devolver lista vacía
        if cursos_id is None or cursos_id == []:
            logger.info(f"Usuario {email} no tiene cursos inscritos")
            return []
        
        logger.info(f"Usuario {email} tiene {len(cursos_id)} cursos inscritos")
        
        # Obtener detalles de los cursos desde Qdrant
        points = qdrant_client.retrieve(
            collection_name="cursos",
            ids=cursos_id,
            with_vectors=True,
            with_payload=True
        )
        
        # Formatear resultados
        resultados = []
        for hit in points:
            resultados.append({
                "id": hit.payload.get("id"),
                "nombre": hit.payload.get("nombre"),
                "nivel": hit.payload.get("nivel"),
                "duracion": hit.payload.get("duracion"),
                "formato": hit.payload.get("formato"),
                "instructor": hit.payload.get("instructor"),
                "fecha_inicio": hit.payload.get("fecha_inicio"),
                "descripcion": hit.payload.get("descripcion")
            })
        
        logger.info(f"Recuperados {len(resultados)} cursos para {email}")
        return resultados
    except Exception as e:
        logger.error(f"Error al obtener cursos para {email}: {e}")
        raise


def create_conversation_in_firestore(email: str, db) -> bool:
    """
    Crea un nuevo documento de conversación en Firestore para un usuario.
    
    Args:
        email: Email del usuario
        db: Cliente de Firestore
    
    Returns:
        bool: True si la conversación se creó exitosamente
    """
    try:
        logger.info(f"Creando conversación para: {email}")
        # Crear nuevo documento de conversación
        db.collection("chat_history").document(email).set({
            "email": email,
            "fecha": datetime.now(),
            "hist": [{"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte hoy?"}]
        })
        logger.info(f"Conversación creada exitosamente para: {email}")
        return True
    except Exception as e:
        logger.error(f"Error al crear conversación para {email}: {e}")
        return False