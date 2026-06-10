import requests
import json
import re
from config import url_home, url_estacion

def get_first_data(status_message : bool = True) -> dict:
    """Obtiene los datos de las estaciones meteorológicas desde la página de
    Conagua.

    Realiza una petición GET a la URL especificada para descargar y parsear
    el archivo JSON que contiene los identificadores y metadatos de las
    estaciones.

    Args:
        url (str): La URL del endpoint o página principal de Conagua.

    Returns:
        dict: Un diccionario con la información de las estaciones, en el que se incluye un id rudimentario de cada estación
              Retorna un diccionario vacío si la decodificación del JSON falla.

    Raises:
        requests.exceptions.RequestException: Si la petición HTTP falla
            (por ejemplo, error 404, 500 o problemas de conexión).
    """
    try:
        response = requests.get(url_home, timeout=10)
        response.raise_for_status()
        data = response.json()
        if status_message: print("Status code:", response.status_code)
    except requests.exceptions.RequestException as err:
        if status_message: print(f"Error de conexión o HTTP: {err}")
    except json.JSONDecodeError as e: 
        if status_message: print("Error: El contenido recibido no es un JSON válido:", e)
    return data


def state_key_and_id(id_estacion: int, status_message : bool = True) ->  tuple[str|None , str|None ]:
    """Encuentra el id de la estación correspondiente al id del servidor
    y encuentra la clave para el estado en el que se encuentra la estación

    Estos se usan para completar los urls de los datos por estación

    Realiza una petición GET a la URL especificada para descargar el texto 
    que contiene el id y la clave por estado que se obtienen mediante expresiones regulares

    Args:
        url (str): el id_preliminar de la estación

    Returns:
        tuple: clave del estado, id

    Raises:
        requests.exceptions.RequestException: Si la petición HTTP falla
            (por ejemplo, error 404, 500 o problemas de conexión).
  """
    try:
        url = url_estacion+str(id_estacion)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        if status_message: print("Status code:", response.status_code)

        key, id = re.findall(r'([a-z]*)..dia([0-9]*).txt"',response.text)[0]
        return key, id
    except requests.exceptions.RequestException as err:
        if status_message: print(f"Error de conexión o HTTP: {err}")
        return None, None



