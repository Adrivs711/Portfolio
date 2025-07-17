from dotenv import load_dotenv
import os
import json
import logging
from datetime import datetime
from clases import CaseStatus
from agentes import create_anonymizer_agent, create_judge_agent, create_case_reviewer_agent, create_case_review_judge_agent
from herramientas import load_json_file, save_to_csv, get_department_descriptions, get_processed_ids
from agno.agent import Agent
load_dotenv()

# --- Constantes ---
FILE_OUTPUT = "processed_cases.csv"
FILE_INPUT = "cases.json"
LOG_FILENAME = "sequential_workflow.log"
DEPARTMENTS_FILE = 'departments.json'
MODEL_GPT_NAME = "gpt-4o-mini"
MODEL_OLLAMA_NAME = "qwen3:4b"

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILENAME, mode='a' if os.path.exists(LOG_FILENAME) else 'w', encoding='utf-8'),
              logging.StreamHandler()]
)

# Separador para cada nueva ejecución
logging.info(f"\n{'='*50} NEW EXECUTION RUN - {datetime.now()} {'='*50}\n")


######### FUNCIONES AUXILIARES #########
def run_anonymization_process(text_to_anonymize: str, anonymizer_agent: Agent, judge_agent: Agent, max_retries: int = 5) -> str | None:
    """
    Orquesta el proceso de anonimización de un texto.

    Este proceso involucra a dos agentes:
    1.  **Anonimizador**: Intenta anonimizar el texto.
    2.  **Juez**: Evalúa si la anonimización es correcta.

    El proceso se reintenta hasta `max_retries` veces si el juez no aprueba el resultado.
    Args:
        text_to_anonymize (str): El texto original que se va a anonimizar.
        anonymizer_agent (Agent): La instancia del agente que anonimiza.
        judge_agent (Agent): La instancia del agente que juzga.
        max_retries (int): El número máximo de intentos.

    Returns:
        str | None: El texto anonimizado si el proceso tiene éxito, o None si falla.
    """
    logging.info("--- FASE 1: Iniciando Proceso Secuencial de Anonimización ---")
    try:
        #Inicia el bucle de reintentos
        for attempt in range(max_retries):

            logging.info(f"\nIntento de anonimización {attempt + 1}/{max_retries}...")
            
            #1. Anonimizar texto
            anon_response = anonymizer_agent.run(f"Anonimiza el siguiente texto: \n\n---\n{text_to_anonymize}\n---")
            anonymized_text = anon_response.content.texto_anonimizado
            logging.info(f"Texto anonimizado (intento {attempt + 1}):\n{anonymized_text}")

            #2. Evaluar anonimización
            judge_response = judge_agent.run(
                f"Evalúa si la siguiente anonimización es correcta.\n"
                f"Texto Original:\n---\n{text_to_anonymize}\n---\n\n"
                f"Texto Anonimizado:\n---\n{anonymized_text}\n---"
            )
            #3. Validación de que la anonimización es correcta y se devuelve el texto anonimizado
            if judge_response.content.is_correct:
                logging.info("El Juez ha aprobado la anonimización.")
                return anonymized_text
            else:
                logging.warning("El Juez ha rechazado la anonimización. Reintentando...")
        
        #Si no se ha podido obtener una anonimización correcta, se devuelve None
        logging.error("No se pudo obtener una anonimización correcta después de 5 intentos.")
        return None
    except Exception as e:
        logging.error(f"Error al anonimizar el texto: {e}")
        raise Exception(f"Error al anonimizar el texto: {e}")


def run_case_review_process(anonymized_text: str, case_reviewer_agent: Agent, case_review_judge_agent: Agent, max_retries: int = 5) -> CaseStatus | None:
    """
    Orquesta el proceso de revisión y clasificación de un caso anonimizado.

    Este proceso involucra a dos agentes:
    1.  **Revisor de Casos**: Analiza el informe y extrae su estado, acciones, etc.
    2.  **Juez de Revisión**: Evalúa si la clasificación del revisor es correcta.

    El proceso se reintenta hasta `max_retries` veces si el juez no aprueba el resultado.

    Args:
        anonymized_text (str): El informe del caso ya anonimizado.
        case_reviewer_agent (Agent): Instancia del agente que revisa el caso.
        case_review_judge_agent (Agent): Instancia del agente que juzga la revisión.
        max_retries (int): El número máximo de intentos.

    Returns:
        CaseStatus | None: Un objeto con el estado del caso si el proceso tiene éxito, o None si falla.
    """
    logging.info("--- FASE 2: Revisión de Caso ---")
    
    try:
        #Inicia el bucle de reintentos
        for attempt in range(max_retries):
                logging.info(f"Intento {attempt + 1}/{max_retries}")
            
                #1. Analizar caso
                review_response = case_reviewer_agent.run(f"Analiza el siguiente informe del caso: \n\n---\n{anonymized_text}\n---")
                case_status = review_response.content
                
                #2. Evaluar revisión
                judge_response = case_review_judge_agent.run(
                    f"Evalúa si la siguiente revisión es correcta.\n"
                    f"Informe del Caso:\n---\n{anonymized_text}\n---\n\n"
                    f"Análisis del Revisor (JSON):\n---\n{case_status.model_dump_json()}\n---"
                )
                
                #3. Validación de que la revisión es correcta y se devuelve el caso
                if judge_response.content.is_correct:
                    logging.info("El Juez ha aprobado la revisión.")
                    return case_status
                else:
                    logging.warning("El Juez ha rechazado la revisión. Reintentando...")
                    
    except Exception as e:
        logging.error(f"Error al analizar el caso: {e}")
        raise Exception(f"Error al analizar el caso: {e}")

    #Si no se ha podido obtener una revisión correcta, se devuelve None
    logging.error("No se pudo obtener una revisión correcta después de 5 intentos")
    return None


######### FUNCIÓN PRINCIPAL #########
def main():
    """
    Función principal que orquesta el pipeline completo de procesamiento de casos.

    El proceso consiste en los siguientes pasos:
    1.  Carga los casos de un fichero JSON de entrada.
    2.  Comprueba qué casos ya han sido procesados previamente (revisando un CSV de salida).
    3.  Filtra los casos para procesar únicamente los que son nuevos.
    4.  Para cada caso nuevo, ejecuta un flujo de dos fases:
        a.  **Anonimización**: Se anonimiza el informe del caso.
        b.  **Revisión**: Se clasifica el caso anonimizado para determinar su estado y departamento.
    5.  Guarda el resultado de cada caso procesado exitosamente en el fichero CSV de salida.
    """
    #1 Conexión a fuentes de datos y carga de datos
    try:
        #Carga los casos del fichero JSON de entrada
        cases = load_json_file(FILE_INPUT)
    except Exception as e:
        logging.error(f"Error al cargar los casos: {e}")
        raise Exception(f"Error al cargar los casos: {e}")
    
    try:
        #Carga las descripciones de los departamentos del fichero JSON de entrada
        department_descriptions = get_department_descriptions(DEPARTMENTS_FILE)
    except Exception as e:
        logging.error(f"Error al cargar las descripciones de los departamentos: {e}")
        raise Exception(f"Error al cargar las descripciones de los departamentos: {e}")

    try:
        # Obtener IDs de los casos ya procesados para no repetirlos
        processed_ids = get_processed_ids(FILE_OUTPUT)
    except Exception as e:
        logging.error(f"Error al obtener los IDs de los casos ya procesados: {e}")
        raise Exception(f"Error al obtener los IDs de los casos ya procesados: {e}")

    # Crear todos los agentes
    try:
        anonymizer = create_anonymizer_agent(model_name=MODEL_OLLAMA_NAME)
        judge = create_judge_agent(model_name=MODEL_OLLAMA_NAME)
        case_reviewer = create_case_reviewer_agent(department_descriptions=department_descriptions, model_name=MODEL_GPT_NAME)
        case_review_judge = create_case_review_judge_agent(department_descriptions=department_descriptions, model_name=MODEL_GPT_NAME)
    except Exception as e:
        logging.error(f"Error al crear los agentes: {e}")
        raise Exception(f"Error al crear los agentes: {e}")
    

    
    #2 Seleccionar los casos que no han sido procesados
    cases_to_process = [
        case for case in cases 
        if case.get('caseID') not in processed_ids
    ]
    #Validación si no hay casos para procesar
    if not cases_to_process:
        logging.info("No hay casos nuevos para procesar.")
        return

    #3 Procesar los casos
    try:
        for i, case_to_process in enumerate(cases_to_process):
            logging.info(f"\n--- Procesando caso {i+1}/{len(cases_to_process)} (ID: {case_to_process.get('caseID')}) ---")
            #Extraer el texto a procesar y el ID del caso
            text_to_process = case_to_process.get('report')
            case_id = case_to_process.get('caseID')

            #Validación de que existe el texto a procesar y el ID del caso
            if not text_to_process or not case_id:
                logging.warning(f"Saltando caso {i+1} por falta de 'report' o 'caseID'.")
                continue

            # --- Ejecución del proceso completo para un caso ---
            texto_anonimizado_resultado = run_anonymization_process(text_to_process, anonymizer, judge)

            if texto_anonimizado_resultado:
                final_case_status = run_case_review_process(texto_anonimizado_resultado, case_reviewer, case_review_judge)

                if final_case_status:
                    #6. Formateo de la salida desde la clase Pydantic a JSON
                    json_output_final = json.loads(final_case_status.model_dump_json())

                    #7. Añadir el ID del caso al JSON
                    json_output_final["caseID"] = case_id

                    #Logs de la salida final para trazabilidad
                    logging.info("\n--- Proceso completado para el caso ---")
                    logging.info("\n--- Salida JSON Final ---")
                    logging.info(json.dumps(json_output_final, indent=2, ensure_ascii=False))
                    
                    #8. Guardar el resultado del caso en un archivo CSV. Se guarda como una lista porque cada posicion de la lista es una fila del csv.
                    save_to_csv([json_output_final], FILE_OUTPUT)

                else:
                    logging.error(f"Error en la fase de revisión para el caso ID: {case_id}.")

            else:
                logging.error(f"Error en la fase de anonimización para el caso ID: {case_id}.")


        logging.info(f"\n{'='*50} FIN DEL PROCESO - {datetime.now()} {'='*50}\n")
        return None
    
    except Exception as e:
        logging.error(f"Error en el flujo principal: {e}")
        raise Exception(f"Error en el flujo principal: {e}")



if __name__ == "__main__":
    main() 