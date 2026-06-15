import re


def parse_key_real_id(text : str) -> tuple [str|None, str|None]:
    """Recibe el texto que incluye el state key, real id y los extrae
    
    Args:
        text(str): texto obtenido del numero de estacion
    
    Returns:
        tuple: state_key, real_id
    """
    try:
        key, real_id = re.findall(r'([a-z]*)..dia([0-9]*).txt"',text)[0]
        return key, real_id
    except IndexError:
        return None, None
    


def parse_metadata(text: str) -> tuple[str|None , str|None, str|None, str|None, str|None, str|None, str|None  ]:
    """ Encuentra el bloque de metadata dentro de la informacion diaria
    y obtiene los valores de metadata dentro del bloque
    considerando el siguiente formato:
        COMISIÓN NACIONAL DEL AGUA
        COORDINACIÓN GENERAL DEL SERVICIO METEOROLÓGICO NACIONAL
        BASE DE DATOS CLIMATOLÓGICA NACIONAL 

        REGISTRO DIARIO HISTÓRICO
        EMISIÓN   : 05/06/2026 

        DATOS DISPONIBLES EN LA BASE DE DATOS A: JUNE DE 2026; 
        CON LA INFORMACIÓN SUMINISTRADA POR LAS UNIDADES ADMINISTRATIVAS 

        ESTACIÓN  : 1001 
        NOMBRE    : AGUASCALIENTES (OBS) 
        ESTADO    : AGUASCALIENTES 
        MUNICIPIO : AGUASCALIENTES 
        SITUACIÓN : OPERANDO 
        CVE-OMM   : 76571 
        LATITUD   : 21.85027778 ° 
        LONGITUD  : -102.2908333 ° 
        ALTITUD   : 1890.8 msnm 

    Args:
        text (str): archivo de texto de la climatología diaria

    Returns:
        tuple: estado, nombre, municipio, situacion, latitud, longitud, altitud
    """
    try:
        start = text.find("ESTACIÓN")
        end = text.find("msnm") + 4
        header_block = text[start:end]

        matches = re.findall(r"([A-ZÁÉÍÓÚÑ-]+)\s*:\s*(.+)", header_block)
        data = {key.strip(): val.strip() for key, val in matches}

        estado = data.get("ESTADO", "")
        nombre = data.get("NOMBRE", "")
        municipio = data.get("MUNICIPIO", "")
        situacion = data.get("SITUACIÓN", "")
        latitud = data.get("LATITUD", "").replace("°", "").strip()
        longitud = data.get("LONGITUD", "").replace("°", "").strip()
        altitud = data.get("ALTITUD", "").replace("msnm", "").strip()

        return estado, nombre, municipio, situacion, latitud, longitud, altitud
    except:
        return None, None, None, None, None, None, None

def catch_nulls(value:str, status_message:bool = True)-> float|None:
    """Returns None if the value = 'NULO'
    or returns the float of the value

    Raises:
        ValueError: Si el string no se puede convertir a float
    """
    if value == 'NULO':
        return None
    try:
        return float(value)
    except ValueError:
        if status_message: print(f"Advertencia: No se pudo convertir '{value}' a float. Reemplazando por None.")
        return None


def remove_header(text: str)-> str:
    """Removes the header from the text considering the format:
            FECHA		PRECIP	EVAP	TMAX	TMIN
                (mm)	(mm)	(°C )	(°C)
            1878-01-01	0	NULO	20.2	9.8

    Args:
        text(str): texto de la tabla de climatología diaria
    
    Returns:
        (str): datos de la tabla
        
        """
    match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
    if match:
        start = match.start()
        return text[start:]
    return ""
    

def daily_data(text:str, real_id: str)-> list[tuple[str, str, float|None, float|None, float|None, float|None]]:
    """Parses the data from the table climatología diaria de alguna estación

    Args:
        text(str): datos de la tabla de climatología diaria
    
    Returns:
        (list): lista de datos de la tabla por dia 
        (date, precip, evap, tmax, tmin)
    """
    daily_records = []

    for line in text.splitlines():
        parts = line.split()
        if len(parts) != 5:
            continue

        fecha, precip, evap, tmax, tmin = parts
        daily_records.append(
            (real_id,
            fecha,
            catch_nulls(precip),
            catch_nulls(evap),
            catch_nulls(tmax),
            catch_nulls(tmin)),
            )
    return daily_records