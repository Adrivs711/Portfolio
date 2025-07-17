# 🤖 Enunciado del Proyecto: Chatbot Inteligente para Recomendación de Cursos

## 🎯 Objetivo General
Desarrollar un **chatbot inteligente** completo que utiliza técnicas avanzadas de IA para recomendar cursos de formación. El sistema integra múltiples tecnologías de vanguardia: **procesamiento de lenguaje natural con Gemini**, **búsqueda vectorial con embeddings**, **bases de datos en la nube**, y una **interfaz web moderna** con Streamlit.

## 🚀 Objetivos de Aprendizaje
Al completar este proyecto, el alumno será capaz de:
- Integrar modelos de IA generativa (Google Gemini) en aplicaciones reales
- Implementar búsqueda vectorial con embeddings para sistemas de recomendación
- Desarrollar APIs REST complejas con múltiples servicios externos
- Crear interfaces conversacionales intuitivas
- Gestionar múltiples bases de datos y servicios en la nube
- Implementar sistemas de autenticación y personalización
- Manejar historial de conversaciones y estado de usuario
- Aplicar técnicas de preprocesamiento de datos para IA

## 🛠️ Tecnologías y Servicios Utilizados

### Core Technologies:
- **Backend**: FastAPI, Python
- **Frontend**: Streamlit
- **IA Generativa**: Google Gemini 2.0 Flash
- **Embeddings**: VertexAI Text Embedding Model
- **Búsqueda Vectorial**: Qdrant Cloud
- **Autenticación**: Supabase
- **Historial**: Firebase Firestore
- **Containerización**: Docker

### Librerías Python:
```
fastapi==0.115.7
streamlit
google-generativeai==0.8.3
vertexai==1.70.0
qdrant-client
supabase==2.3.4
firebase-admin
python-dotenv==1.0.1
passlib[bcrypt]==1.7.4
```

## 🏗️ Arquitectura del Sistema

### 📊 Flujo de Procesamiento del Chatbot:
1. **Usuario envía mensaje** → Frontend (Streamlit)
2. **Extracción de keywords** → Gemini AI analiza intención
3. **Clasificación de búsqueda**:
   - **Búsqueda general**: Respuesta directa con Gemini
   - **Búsqueda de cursos**: Búsqueda vectorial en Qdrant
4. **Ranking con IA** → Gemini selecciona cursos más relevantes
5. **Actualización de historial** → Firebase Firestore
6. **Respuesta al usuario** → Interfaz conversacional

### 🗄️ Bases de Datos:
- **Supabase**: Usuarios y datos de autenticación
- **Firebase**: Historial de conversaciones por usuario
- **Qdrant**: Vectores de embeddings de cursos
- **CSV**: Dataset original de cursos (100+ cursos)

## 📋 Funcionalidades Requeridas

### 🔧 API Backend (FastAPI)

#### 1. **Sistema de Autenticación**
- `POST /register` - Registro de nuevos usuarios
- `POST /login` - Inicio de sesión con hash bcrypt

#### 2. **Motor de Chat Inteligente**
- `POST /chat` - Endpoint principal del chatbot
  - Recibe: mensaje, contexto, email del usuario
  - Procesa: extrae keywords, clasifica intención, busca cursos
  - Devuelve: lista de cursos recomendados con scores

#### 3. **Gestión de Historial**
- `GET /get_history/{email}` - Obtener historial de conversaciones
- `DELETE /clear_history/{email}` - Limpiar historial

#### 4. **Sistema de Recomendaciones**
- `POST /recommended_courses` - Cursos personalizados por embeddings
- `POST /my_courses` - Cursos del usuario inscrito
- `POST /update_embeddings_user` - Actualizar perfil de usuario
- `POST /update_courses_user` - Gestionar inscripciones

### 🖥️ Frontend (Streamlit)

#### 1. **Sistema de Autenticación**
- Pantalla de login/registro con validación
- Manejo de sesiones de usuario

#### 2. **Chat Inteligente**
- Interfaz conversacional moderna
- Historial de mensajes persistente
- Botones de inscripción en cursos recomendados
- Limpieza de historial

#### 3. **Gestión de Cursos**
- **Pestaña "Cursos Recomendados"**: Basados en perfil del usuario
- **Pestaña "Mis Cursos"**: Cursos en los que está inscrito
- **Inscripción con un clic**: Actualiza automáticamente perfil

#### 4. **Interfaz Responsive**
- Diseño moderno con pestañas
- Expansores para información detallada de cursos
- Mensajes de estado y errores informativos

## 🗂️ Estructura de Archivos Requerida

```
6.Chatbot/
├── back/
│   ├── main.py              # API principal FastAPI
│   ├── operations.py        # Lógica de base de datos y búsquedas
│   ├── clases.py           # Modelos Pydantic
│   ├── instrucciones.py    # Prompts para Gemini AI
│   ├── tools.py            # Utilidades para IA (configuración Gemini)
│   ├── chatbot.env         # Variables de entorno
│   ├── requirements.txt    # Dependencias Python
│   ├── Dockerfile          # Containerización
│   ├── credenciales_historial.json  # Credenciales Firebase
│   ├── Preproceso/
│   │   ├── Cursos.csv     # Dataset de cursos
│   │   └── generar_embeddings_cursos.py  # Script de preprocesamiento
│   └── readme.md
├── front/
│   ├── chat.py            # Interfaz Streamlit principal
│   ├── prueba_supabase.py # Tests de conexión
│   ├── requirements.txt   # Dependencias frontend
│   └── readme.md
└── Enunciado.md           # Este archivo
```

## 🔧 Configuración de Servicios Externos

### 1. **Google Cloud Platform**
```bash
# Habilitar APIs necesarias
- Vertex AI API
- Generative Language API
```

### 2. **Supabase Setup**
- Crear proyecto en [supabase.com](https://supabase.com)
- Crear tabla `usuarios`:
```sql
CREATE TABLE usuarios (
  email TEXT PRIMARY KEY,
  password TEXT NOT NULL,
  embeddings_usuario FLOAT[] DEFAULT NULL,
  courses_usuario INTEGER[] DEFAULT '{}'::INTEGER[]
);
```

### 3. **Qdrant Cloud**
- Crear cluster en [cloud.qdrant.io](https://cloud.qdrant.io)
- Configurar colección "cursos" con vectores de 768 dimensiones

### 4. **Firebase Firestore**
- Crear proyecto Firebase
- Habilitar Firestore
- Descargar credenciales de servicio (.json)

### 5. **Archivo de Variables de Entorno**
```env
# chatbot.env
VERTEXAI_PROJECT="tu-proyecto-gcp"
VERTEXAI_LOCATION="europe-west1"
QDRANT_URL="https://tu-cluster.qdrant.io:6333"
QDRANT_API_KEY="tu-api-key"
SUPABASE_URL="https://tu-proyecto.supabase.co"
SUPABASE_KEY="tu-anon-key"
CREDENCIALES_FIRESTORE="credenciales_historial.json"
GEMINI_API_KEY="tu-gemini-api-key"
```

## 💡 Guía de Implementación Paso a Paso

### 🌟 Fase 1: Configuración Base (2-3 días)
1. **Configurar servicios externos** (GCP, Supabase, Qdrant, Firebase)
2. **Crear modelos Pydantic** en `clases.py`
3. **Implementar autenticación básica** (register/login)
4. **Configurar conexiones** en `operations.py`

### 🧠 Fase 2: Motor de IA (3-4 días)
5. **Configurar Gemini** en `tools.py`
6. **Implementar prompts** en `instrucciones.py`
7. **Desarrollar pipeline de chat**:
   - Extracción de keywords
   - Clasificación de búsquedas
   - Búsqueda vectorial
   - Ranking con LLM

### 📊 Fase 3: Sistema de Datos (2-3 días)
8. **Preprocesar dataset** de cursos
9. **Generar embeddings** y cargar en Qdrant
10. **Implementar gestión de historial** con Firebase
11. **Sistema de recomendaciones** personalizado

### 🎨 Fase 4: Frontend e Integración (2-3 días)
12. **Desarrollar interfaz** de chat en Streamlit
13. **Implementar pestañas** de gestión de cursos
14. **Conectar frontend con API**
15. **Testing completo** del sistema

## 🚀 Cómo Ejecutar el Proyecto

### Backend:
```bash
cd back/
pip install -r requirements.txt
python -m uvicorn main:app --port=8000 --reload
```

### Frontend:
```bash
cd front/
pip install -r requirements.txt
python -m streamlit run chat.py --server.port=8080
```

### Docker (Producción):
```bash
cd back/
docker build -t chatbot-api .
docker run -p 8000:8000 chatbot-api
```

## ✅ Criterios de Evaluación

### Integración de IA (35%)
- [ ] Gemini AI configurado y funcionando correctamente
- [ ] Pipeline de procesamiento de mensajes implementado
- [ ] Búsqueda vectorial con embeddings operativa
- [ ] Sistema de recomendaciones personalizado

### Backend API (25%)
- [ ] Todos los endpoints implementados y funcionales
- [ ] Autenticación segura con Supabase
- [ ] Gestión correcta de historial con Firebase
- [ ] Manejo robusto de errores y logging

### Frontend UX (20%)
- [ ] Interfaz conversacional intuitiva
- [ ] Sistema de pestañas funcional
- [ ] Gestión de cursos (recomendados/inscritos)
- [ ] Autenticación de usuario fluida

### Arquitectura y Código (20%)
- [ ] Código bien estructurado y documentado
- [ ] Separación correcta de responsabilidades
- [ ] Modelos Pydantic apropiados
- [ ] Configuración correcta de servicios externos

## 🎯 Funcionalidades Bonus (Puntos Extra)

### IA Avanzada:
- Implementar memory a largo plazo del usuario
- Añadir análisis de sentimientos
- Sistema de feedback de recomendaciones

### UX Mejorado:
- Interfaz de chat más visual (avatars, typing indicators)
- Exportar historial de conversaciones
- Dashboard de estadísticas de usuario

### Técnico:
- Implementar rate limiting
- Añadir métricas y monitoreo
- Tests unitarios y de integración

## 📚 Conceptos Clave a Dominar

### 🤖 Inteligencia Artificial:
- **LLMs (Large Language Models)**: Gemini 2.0 Flash
- **Embeddings**: Representación vectorial de texto
- **RAG (Retrieval Augmented Generation)**: Búsqueda + Generación
- **Prompt Engineering**: Diseño de instrucciones efectivas

### 🔍 Búsqueda Vectorial:
- **Similarity Search**: Búsqueda por similitud semántica
- **Vector Databases**: Qdrant para almacenamiento eficiente
- **Dimensionalidad**: Vectores de 768 dimensiones
- **Scoring**: Métricas de relevancia

### 🏗️ Arquitectura Distribuida:
- **Microservicios**: API desacoplada del frontend
- **Cloud Services**: Múltiples proveedores integrados
- **Async Programming**: Manejo eficiente de I/O
- **Error Handling**: Recuperación elegante de fallos

## 📖 Recursos de Aprendizaje

### Documentación Oficial:
- [Google Gemini AI](https://ai.google.dev/docs)
- [VertexAI Python](https://cloud.google.com/vertex-ai/docs/python-sdk/use-vertex-ai-python-sdk)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Supabase Python](https://supabase.com/docs/reference/python)
- [Firebase Admin Python](https://firebase.google.com/docs/admin/setup)

### Tutoriales Recomendados:
- [Building RAG Applications](https://python.langchain.com/docs/tutorials/rag/)
- [Vector Search Fundamentals](https://qdrant.tech/articles/what-is-a-vector-database/)
- [Streamlit Chat Elements](https://docs.streamlit.io/library/api-reference/chat)

## 🎓 Resultados de Aprendizaje

Al completar este proyecto, habrás construido:
- ✅ Un chatbot de IA conversacional completamente funcional
- ✅ Un sistema de recomendaciones basado en embeddings
- ✅ Una arquitectura de microservicios moderna
- ✅ Integración con 5+ servicios cloud diferentes
- ✅ Una comprensión profunda de RAG y búsqueda vectorial

---

**¡Este es un proyecto de nivel profesional que te preparará para trabajar con IA en el mundo real! 🚀**

*Recuerda: Este proyecto integra tecnologías avanzadas. Tómate tu tiempo para entender cada componente antes de pasar al siguiente.* 