from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "estaciones.sqlite3"


url_home = 'https://smn.conagua.gob.mx/tools/PHP/ConsultaCapas.php?tipo=ENCS&clave=Act'
url_estacion = 'https://smn.conagua.gob.mx/tools/PHP/GetInfoENCS.php?id_estacion='
url_daily = 'https://smn.conagua.gob.mx/tools/RESOURCES/Normales_Climatologicas/Diarios/'