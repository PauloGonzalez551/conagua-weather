import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

import logging
logger =logging.getLogger(__name__)

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

    

def get_first_data() -> list:
    """Obtiene los datos de las estaciones meteorológicas desde la página de
    Conagua.

    Realiza una petición GET a la URL especificada para descargar y parsear
    el archivo JSON que contiene los identificadores y metadatos de las
    estaciones.

    Returns:
        list: una lista de diccionarios que incluyen el número de estación
              Retorna una lista vacía si la decodificación del JSON falla.

    Raises:
        requests.exceptions.RequestException: Si la petición HTTP falla
            (por ejemplo, error 404, 500 o problemas de conexión).
    """
    try:
        response = requests.get(url_home, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Status code: %s", response.status_code)
        return data
    except requests.exceptions.RequestException as err:
        logger.error("Error de conexión o HTTP:  %s", err)
    except json.JSONDecodeError as e: 
        logger.error("Error: El contenido recibido no es un JSON válido:  %s", e)
    return []
    


def get_key_real_id_file(session:requests.Session, station_number: int) ->  str:
    """ Realiza una petición GET a la URL especificada por el id secundario para descargar 
    el texto que contiene el id y la clave por estado 

    Estos se usan para completar los urls de los datos por estación

    Args:
        session (requests.Session): sesión
        station_number (str): el número de estación

    Returns:
        str: texto que incluye el state_key y real_id

    Raises:
        requests.exceptions.RequestException: Si la petición HTTP falla
            (por ejemplo, error 404, 500 o problemas de conexión).
  """
    try:
        url = url_estacion.format(station_number=station_number)
        response = session.get(url, timeout=(5,30))
        response.raise_for_status()
        logger.debug("Se obtuvo el id y state key con código: %s", response.status_code)
        return response.text
    except requests.exceptions.HTTPError as http_err:
        logger.error("Error HTTP al descargar estación número %s: %s", station_number, http_err)
    except requests.exceptions.Timeout:
        logger.error("Timeout al descargar estación número %s", station_number)

    except requests.exceptions.RequestException as err:
        logger.error("Error de conexión con estación número %s o HTTP: %s", station_number, err)
    return ""
    
def get_daily_file(session:requests.Session,
                   state_key:str,
                   real_id:str,
)->str:
    """Gets the file containing all the metadata an daily data
    using the real id and state key from a station

    Args:
        session (requests.Session): sesión
        state_key(str): la clave de estado
        real_id(str): id de la estación

    Returns:
        str: texto de los datos de climatología diaria

    Raises:
        requests.exceptions.RequestException: Si la petición HTTP falla
            (por ejemplo, error 404, 500 o problemas de conexión).
    
    """

    url = url_daily.format(state_key=state_key, real_id=real_id)
    try:
        response = session.get(url, timeout=(5,30))
        response.raise_for_status()
        logger.debug("File de climatología diaria obtenido con código: %s", response.status_code)
        return response.text
    except requests.exceptions.HTTPError as http_err:
        logger.error("Error HTTP al descargar esatción id %s: %s", real_id, http_err)
    except requests.exceptions.Timeout:
        logger.error("Timeout al descargar estación id %s", real_id)
    except requests.exceptions.RequestException as err:
        logger.error("Error de conexión con estación id %s o HTTP: %s", real_id, err)
    return ""




