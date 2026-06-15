from pathlib import Path
import logging


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "estaciones.sqlite3"


url_home = 'https://smn.conagua.gob.mx/tools/PHP/ConsultaCapas.php?tipo=ENCS&clave=Act'
url_estacion = 'https://smn.conagua.gob.mx/tools/PHP/GetInfoENCS.php?id_estacion={station_number}'
url_daily = 'https://smn.conagua.gob.mx/tools/RESOURCES/Normales_Climatologicas/Diarios/{state_key}/dia{real_id}.txt'

def setup_logging()->None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )