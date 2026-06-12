import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

from conagua_scraper.config import url_home, url_estacion, url_daily

def create_session()-> requests.Session:
    session = requests.Session()

    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(500, 502, 503, 504)
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update({
        "User-Agent": "conagua-weather-scraper/0.1"
    })

    return session

    

def get_first_data(status_message : bool = True) -> dict:
    """Obtiene los datos de las estaciones meteorológicas desde la página de
    Conagua.

    Realiza una petición GET a la URL especificada para descargar y parsear
    el archivo JSON que contiene los identificadores y metadatos de las
    estaciones. s

    Args:
        url (str): La URL del endpoint o página principal de Conagua.

    Returns:
        dict: Un diccionario con la información de las estaciones, en el que se incluye
        un id rudimentario de cada estación
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


def get_key_real_id_file(id_estacion: int, status_message : bool = True) ->  str:
    """ Realiza una petición GET a la URL especificada por el id secundario para descargar 
    el texto que contiene el id y la clave por estado 

    Estos se usan para completar los urls de los datos por estación

    Args:
        url (str): el id_preliminar de la estación

    Returns:
        str: texto que incluye el state_key y real_id

    Raises:
        requests.exceptions.RequestException: Si la petición HTTP falla
            (por ejemplo, error 404, 500 o problemas de conexión).
  """
    try:
        url = url_estacion+str(id_estacion)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        if status_message: print("Status code:", response.status_code)
        return response.text
    except requests.exceptions.RequestException as err:
        if status_message: print(f"Error de conexión o HTTP: {err}")
        return ""
    
def get_daily_file(state_key:str, real_id:str)->str:
    url = url_daily+state_key+'/dia'+real_id+'.txt'
    response = requests.get(url)
    return response.text



