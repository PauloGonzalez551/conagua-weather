import re

def parse_key_real_id(text : str) -> tuple [str|None, str|None]:
    key, real_id = re.findall(r'([a-z]*)..dia([0-9]*).txt"',text)[0]
    return key, real_id


def parse_metadata(text: str) -> tuple[str|None , str|None, str|None, str|None, str|None, str|None, str|None  ]:
    """" Encuentra el bloque de metadata dentro de la informacion diaria
    y obtiene los valores de metadata dentro del bloque

    Args:
        text (str): archivo de texto de la climatología diaria

    Returns:
        tuple: estado, nombre, municipio, situacion, latitud, longitud, altitud
    """

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