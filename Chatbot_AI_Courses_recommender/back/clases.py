from pydantic import BaseModel

class Mensaje(BaseModel):
    """Representa el input del usuario:
           message: mensaje del usuario
    """
    message: str
    contexto: list
    email: str = None

class Course(BaseModel):
    """Productos
    id: código nacional
    name: nombre del producto
    score: distancia vectorial entre el artículo y la consulta del usuario
    """
    id: str
    name: str
    score: float
    instructor: str
    fecha_inicio: str
    nivel: str
    duracion: str
    formato: str
    descripcion: str

class FinalOutput(BaseModel):
    "Salida final. Productos seleccionados por la IA"
    coursesCount: int
    courses: list[Course]

class User(BaseModel):
    """Representa el usuario"""
    email: str
    password: str = None
    id_curso: int = None