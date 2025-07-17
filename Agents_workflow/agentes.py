from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.ollama import Ollama
from clases import JudgeDecision, TextoAnonimizado, CaseStatus
from instrucciones import get_anonymizer_instructions, get_judge_anonymizer_instructions, get_reviewer_instructions, get_judge_reviewer_instructions

def create_anonymizer_agent(model_name: str) -> Agent:
    """Crea y devuelve el agente anonimizador."""
    return Agent(
        name="Anonimizador",
        role="Tu tarea es anonimizar el texto que se te proporciona.",
        model=Ollama(id=model_name), response_model=TextoAnonimizado,
        description="Eres un AgnoAnom, un anonimizador de texto en idioma español.",
        instructions=[get_anonymizer_instructions()]
    )

def create_judge_agent(model_name: str) -> Agent:
    """Crea y devuelve el juez de anonimización."""
    return Agent(
        name="JuezDeAnonimizacion",
        role="Tu tarea es evaluar el trabajo del Anonimizador.",
        model=Ollama(id=model_name), response_model=JudgeDecision,
        description="Eres AgnoJuez, tu tarea es comparar un texto original con su versión anonimizada.",
        instructions=get_judge_anonymizer_instructions()
    )

def create_case_reviewer_agent(department_descriptions: str, model_name: str) -> Agent:
    """Crea y devuelve un agente revisor de casos con las descripciones de departamento incluidas."""
    return Agent(
        name="RevisorDeCasos",
        role="Tu tarea es analizar el estado de un caso y determinar las acciones necesarias.",
        model=OpenAIChat(id=model_name), response_model=CaseStatus,
        description="Eres un experto en análisis de casos de soporte.",
        instructions=[get_reviewer_instructions(department_descriptions)]
    )

def create_case_review_judge_agent(department_descriptions: str, model_name: str) -> Agent:
    """Crea y devuelve un agente juez de revisión con las descripciones de departamento incluidas."""
    return Agent(
        name="JuezDeRevisionDeCasos",
        role="Tu tarea es evaluar el análisis de un caso de soporte.",
        model=OpenAIChat(id=model_name), response_model=JudgeDecision,
        description="Eres un auditor experto que evalúa la clasificación de un caso.",
        instructions=[get_judge_reviewer_instructions(department_descriptions)]
    ) 