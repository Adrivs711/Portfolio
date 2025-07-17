import json
import os
import pandas as pd

def load_json_file(file_path: str) -> dict:
    """Carga un archivo JSON y devuelve su contenido."""
    with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)


def get_department_descriptions(file_path: str) -> str:
    """
    Carga los departamentos y devuelve una cadena de texto formateada con sus descripciones.
    """
    departments = load_json_file(file_path)
    return "\n".join([f"- {d['departmentID']}: {d['description']}" for d in departments])

def get_processed_ids(csv_filepath: str) -> list:
    """
    Lee un archivo CSV con pandas y devuelve una lista de los 'caseID' existentes.
    Los caseID se devuelven como strings de 3 dígitos (ej: "001", "002").
    """
    if not os.path.isfile(csv_filepath):
        return []
    df = pd.read_csv(csv_filepath)
    #Pasar a lista el arry de pandas y aplicar map con zfill para asegurar formato de 3 dígitos
    case_ids = list(map(lambda x: str(x).zfill(3),df['caseID'].to_list()))
    return case_ids

def save_to_csv(data, csv_filepath: str):
    """
    Guarda una lista de diccionarios en un archivo CSV usando pandas.
    Si el archivo no existe, crea uno nuevo con cabeceras.
    Si ya existe, añade las nuevas filas sin repetir las cabeceras.
    """
    df = pd.DataFrame(data)
    if os.path.isfile(csv_filepath):
        df.to_csv(csv_filepath, mode='a', header=False, index=False, encoding='utf-8')
    else:
        df.to_csv(csv_filepath, mode='w', header=True, index=False, encoding='utf-8')