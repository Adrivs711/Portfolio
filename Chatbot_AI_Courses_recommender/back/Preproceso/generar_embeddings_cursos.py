"""
Script para generar embeddings del archivo Cursos.csv utilizando el modelo de Google
y guardar los datos en una colección de Qdrant.
"""

import pandas as pd
import numpy as np
import re
import os
import logging
from dotenv import load_dotenv

# Cargar variables de entorno desde el directorio padre
# La ruta relativa '../' sube un nivel desde 'Preproceso' a 'back'
dotenv_path = os.path.join(os.path.dirname(__file__), '../chatbot.env')
load_dotenv(dotenv_path=dotenv_path)

# Configurar Google Vertex AI
import vertexai
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput

# Configurar Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def inicializar_vertex_ai():
    """
    Inicializa la conexión con Vertex AI
    """
    logger.info("Inicializando Vertex AI...")
    # Proyecto y ubicación deben configurarse según tu entorno
    vertexai.init(project=os.getenv("VERTEXAI_PROJECT"), location=os.getenv("VERTEXAI_LOCATION"))
    
    # Cargar el modelo de embeddings multilingüe
    text_embedding_model = TextEmbeddingModel.from_pretrained("text-multilingual-embedding-002")
    logger.info("Modelo de embeddings cargado correctamente")
    
    return text_embedding_model

def cargar_datos_cursos(ruta_csv):
    """
    Carga los datos del archivo CSV de cursos
    """
    logger.info(f"Cargando datos desde {ruta_csv}...")
    df = pd.read_csv(ruta_csv)
    logger.info(f"Datos cargados correctamente. {len(df)} cursos encontrados.")
    return df

def preparar_texto_para_embeddings(df):
    """
    Prepara los textos de los cursos para generar embeddings
    """
    logger.info("Preparando textos para embeddings...")
    
    # Crear un texto combinado para cada curso
    textos_combinados = []
    
    for _, row in df.iterrows():
        # Combinar información relevante del curso
        texto = f"Nombre: {row['Nombre']}. "
        texto += f"Nivel: {row['Nivel']}. "
        texto += f"Duración: {row['duracion']}. "
        texto += f"Formato: {row['Formato']}. "
        texto += f"Instructor: {row['Instructor']}. "
        
        # Añadir categorías (solo las que son "Sí")
        categorias = []
        for categoria in ['Informatica', 'Bases_de_datos', 'Sistemas_Operativos', 'Programacion', 
                         'Linux', 'Machine_Learning', 'Cloud', 'Ciberseguridad', 
                         'Desarrollo_Web', 'Redes', 'Inteligencia_Artificial', 
                         'Big_Data', 'Desarrollo_Móvil']:
            if row[categoria] == 'Sí':
                categorias.append(f"{categoria.replace('_', ' ')}: Sí")
            else:
                categorias.append(f"{categoria.replace('_', ' ')}: No")
        
        if categorias:
            texto += f"Categorías: {', '.join(categorias)}. "
        
        # Añadir descripción
        texto += f"Descripción: {row['Descripcion']}"
        
        textos_combinados.append(texto)
    
    logger.info(f"Textos preparados para {len(textos_combinados)} cursos")
    return textos_combinados

def generar_embeddings(textos, modelo):
    """
    Genera embeddings para los textos utilizando el modelo de Google
    """
    logger.info("Generando embeddings...")
    
    # Generar embeddings en batches para evitar limitaciones de memoria
    batch_size = 10
    embeddings = []
    
    for i in range(0, len(textos), batch_size):
        batch = textos[i:i+batch_size]
        logger.info(f"Procesando batch {i//batch_size + 1}/{(len(textos)-1)//batch_size + 1}")
        
        # Crear inputs para el modelo
        batch_inputs = [
            TextEmbeddingInput(text=texto, task_type="SEMANTIC_SIMILARITY") 
            for texto in batch
        ]
        
        # Generar embeddings
        batch_embeddings = modelo.get_embeddings(
            batch_inputs, 
            output_dimensionality=768,  # Dimensión estándar para este modelo
            auto_truncate=True  # Truncar textos muy largos automáticamente
        )
        
        # Extraer los valores de los embeddings
        batch_vectors = [list(emb.values) for emb in batch_embeddings]
        embeddings.extend(batch_vectors)
    
    logger.info(f"Embeddings generados correctamente para {len(embeddings)} cursos")
    return embeddings

def crear_coleccion_qdrant(client, nombre_coleccion):
    """
    Crea una colección en Qdrant si no existe
    """
    try:
        client.get_collection(nombre_coleccion)
        logger.info(f"La colección {nombre_coleccion} ya existe")
    except Exception:
        client.create_collection(
            collection_name=nombre_coleccion,
            vectors_config=models.VectorParams(
                size=768,  # Dimensión de los vectores
                distance=models.Distance.COSINE  # Métrica de distancia
            )
        )
        logger.info(f"Colección {nombre_coleccion} creada correctamente")

def guardar_en_qdrant(df, embeddings, nombre_coleccion):
    """
    Guarda los datos y embeddings en una colección de Qdrant
    """
    logger.info("Conectando a Qdrant...")
    
    # Conectar a Qdrant
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"), 
        api_key=os.getenv("QDRANT_API_KEY"),
    )
    print("Llega aqui")
    # Crear colección si no existe
    crear_coleccion_qdrant(client, nombre_coleccion)
    
    # Preparar puntos para Qdrant
    logger.info("Preparando datos para Qdrant...")
    points = []
    
    for i, (_, row) in enumerate(df.iterrows()):
        # Crear payload con la información del curso
        payload = {
            "id": i,
            "nombre": row["Nombre"],
            "nivel": row["Nivel"],
            "duracion": row["duracion"],
            "formato": row["Formato"],
            "instructor": row["Instructor"],
            "descripcion": row["Descripcion"],
            "fecha_inicio": row["FechaInicio"]
        }
        
        # Añadir categorías como booleanos
        for categoria in ['Informatica', 'Bases_de_datos', 'Sistemas_Operativos', 'Programacion', 
                         'Linux', 'Machine_Learning', 'Cloud', 'Ciberseguridad', 
                         'Desarrollo_Web', 'Redes', 'Inteligencia_Artificial', 
                         'Big_Data', 'Desarrollo_Móvil']:
            payload[categoria.lower()] = (row[categoria] == 'Sí' or row[categoria] == 'No')
        
        # Crear punto
        points.append(models.PointStruct(
            id=i,  # Usar índice como ID
            vector=embeddings[i],
            payload=payload
        ))
    
    # Insertar puntos en batches
    logger.info("Insertando datos en Qdrant...")
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i+batch_size]
        client.upsert(
            collection_name=nombre_coleccion,
            points=batch
        )
        logger.info(f"Insertados {min(i+batch_size, len(points))} de {len(points)} puntos")
    
    logger.info(f"Datos guardados correctamente en la colección {nombre_coleccion}")
    return True

def main():
    """
    Función principal
    """
    # Ruta al archivo CSV
    ruta_csv = "c:\\Users\\avelasco\\Desktop\\Adrian_local\\bot_gcp\\back\\Preproceso\\Cursos.csv"
    
    # Nombre de la colección en Qdrant
    nombre_coleccion = "cursos"
    
    # Inicializar Vertex AI y cargar modelo
    modelo = inicializar_vertex_ai()
    
    # Cargar datos
    df = cargar_datos_cursos(ruta_csv)
    
    # Preparar textos
    textos = preparar_texto_para_embeddings(df)
    
    # Generar embeddings
    embeddings = generar_embeddings(textos, modelo)
    
    # Guardar en Qdrant
    guardar_en_qdrant(df, embeddings, nombre_coleccion)
    
    logger.info("Proceso completado con éxito")

if __name__ == "__main__":
    main()
