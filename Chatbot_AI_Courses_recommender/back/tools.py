import google.generativeai as genai
from google.generativeai.types import HarmCategory,HarmBlockThreshold
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='chatbot.env')

def generar_modelo(instrucciones: str):
    """
    Instancia y genera el modelo con los parámetros establecidos.
    Input: Instrcciones
    Output: El modelo generado
    """

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    safety_config = {HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT:  HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT:HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH:HarmBlockThreshold.BLOCK_NONE
        }
    generation_config = {    "temperature": 0.5,    "max_output_tokens":5000,    "response_mime_type": "application/json"    }
    gemini = genai.GenerativeModel(model_name="gemini-2.0-flash", generation_config= generation_config, safety_settings=safety_config,system_instruction=instrucciones)
    return gemini