import logging
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


from conagua_scraper.config import DB_PATH, DATA_DIR
from conagua_scraper.database import (connect_database,
                                    delete_tables,
                                    create_tables,
                                    load_states_batch,
                                    load_stations_batch,
                                    load_daily_data_batch,
                                    key_id_from_db,
                                    )
from conagua_scraper.scraper import (get_first_data,
                                    get_key_real_id_file,
                                    get_daily_file,
                                    create_session,
                                     )
from conagua_scraper.parser import (parse_key_real_id,
                                    parse_metadata,
                                    remove_header,
                                    daily_data,
                                    )

from conagua_scraper.config import setup_logging
logger = logging.getLogger(__name__)
_thread_local = threading.local()

def get_thread_session():
    """Obtiene o inicializa la sesión HTTP asignada exclusivamente al hilo actual.

    Utiliza el almacenamiento local de hilos (Thread-Local Storage) para garantizar
    que cada hilo del Pool tenga su propia instancia de 'requests.Session'. Esto
    evita problemas de contención de cerrojos (lock contention) y corrupción de 
    estado en operaciones concurrentes, al mismo tiempo que permite la reutilización 
    de sockets TCP (HTTP Keep-Alive) dentro del mismo hilo.

    Returns:
        requests.Session: Un objeto de sesión HTTP configurado y aislado para 
        el hilo que invoca la función.
    """
    if not hasattr(_thread_local, "session"):
        _thread_local.session = create_session()
    return _thread_local.session

def delete_database()->None:

    with connect_database(DB_PATH) as conn:
        delete_tables(conn)

    print(f"Database deleted at {DB_PATH}")

def setup_database()->None:
    """Garantiza la existencia del directorio de datos e inicializa la base de datos.
    """
    DATA_DIR.mkdir(exist_ok=True)

    with connect_database(DB_PATH) as conn:
        create_tables(conn)

    print(f"Database ready at {DB_PATH}")

def fetch_metadata(station_number:str)-> tuple[tuple,tuple] | None:
    session = get_thread_session()

    state_key, real_id = parse_key_real_id(
                get_key_real_id_file(session, station_number)
                )
    
    if state_key is None or real_id is None:
        logger.warning("Skipping station %s because state_key or real_id are missing", station_number)
        return None
    
    state, name, mun, situation, lat, lon, elev = parse_metadata(
                get_daily_file(session, state_key, real_id)
                )
    if state is None: 
                logger.warning("No metadata could be found for station %s", station_number)
    station_row = (
                station_number,
                real_id,
                state_key,
                name,
                mun,
                situation,
                lat,                     
                lon,
                elev,
                )
    state_row = (state, state_key)

    return state_row, station_row
             
def load_initial_metadata_conc()->None:
    """Orquesta el scraping, parseo y almacenamiento del catálogo inicial de estaciones.

    El proceso se ejecuta en las siguientes etapas secuenciales:
    1. Obtiene la lista base de estaciones desde el mapa/página principal de Conagua.
    2. Descarga de forma síncrona el identificador real (`real_id`) y el estado (`state_key`) 
       asociados a cada número de estación.
    3. Descarga el archivo climatológico de cada estación para extraer sus metadatos geográficos 
       e institucionales (nombre, municipio, latitud, longitud, elevación, etc.).
    4. Clasifica las estaciones con fallos de metadatos para guardarlas con valores nulos (para 
       no perder el registro) y cataloga los nombres de los estados de forma única.
    5. Guarda de forma masiva (en lotes) la información recolectada en las tablas 'states' y 
       'stations' utilizando una única conexión de base de datos al final del proceso.

    Métricas registradas por el logger:
        - total_stations: Cantidad total de estaciones encontradas inicialmente.
        - skipped_stations: Estaciones descartadas por no devolver ID real o Clave de Estado.
        - failed_stations: Estaciones sin archivo de metadatos legible (se insertan con valores None).

    Raises:
        requests.RequestException: Si ocurren fallos críticos de red durante el scraping.
        sqlite3.Error: Si ocurre una violación de restricciones al insertar los lotes en la base de datos."""
    max_workers = 8
    states_to_insert = {}
    stations_to_insert =[]
    first_data = get_first_data()
    logger.info("Found %d stations in first data page", len(first_data))

    skipped_stations = 0
    failed_stations = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures =[
            executor.submit(fetch_metadata, station["id_estacion"])
                for station in first_data
        ]
        total_stations = len(futures)

        for index, future in enumerate(as_completed(futures), start=1):
            try:
                result = future.result()
            except Exception:
                failed_stations += 1
                logger.exception("Failed to process one station")
                continue

            if result is None:
                skipped_stations += 1
                continue

            state_row, station_row = result
            state, state_key = state_row


            if state is not None:
                states_to_insert[state_key] = state

            stations_to_insert.append(station_row)

            if index % 200 == 0:
                logger.info("Processed %d/%d stations", index, len(first_data))
    
    logger.info(
        "Finished downloading metadata: %d total, %d ready to insert, %d skipped, %d failed",
        total_stations,
        len(stations_to_insert),
        skipped_stations,
        failed_stations,
    )


    with connect_database(DB_PATH) as conn:
        load_states_batch(
            conn,
            [
            (state_name, state_key)
             for state_key, state_name in states_to_insert.items()
             ],
        )

        load_stations_batch(conn, stations_to_insert)
    
    logger.info("Inserted metadata into database")

def load_initial_metadata()->None:
    """Orquesta el scraping, parseo y almacenamiento del catálogo inicial de estaciones.

    El proceso se ejecuta en las siguientes etapas secuenciales:
    1. Obtiene la lista base de estaciones desde el mapa/página principal de Conagua.
    2. Descarga de forma síncrona el identificador real (`real_id`) y el estado (`state_key`) 
       asociados a cada número de estación.
    3. Descarga el archivo climatológico de cada estación para extraer sus metadatos geográficos 
       e institucionales (nombre, municipio, latitud, longitud, elevación, etc.).
    4. Clasifica las estaciones con fallos de metadatos para guardarlas con valores nulos (para 
       no perder el registro) y cataloga los nombres de los estados de forma única.
    5. Guarda de forma masiva (en lotes) la información recolectada en las tablas 'states' y 
       'stations' utilizando una única conexión de base de datos al final del proceso.

    Métricas registradas por el logger:
        - total_stations: Cantidad total de estaciones encontradas inicialmente.
        - skipped_stations: Estaciones descartadas por no devolver ID real o Clave de Estado.
        - failed_stations: Estaciones sin archivo de metadatos legible (se insertan con valores None).

    Raises:
        requests.RequestException: Si ocurren fallos críticos de red durante el scraping.
        sqlite3.Error: Si ocurre una violación de restricciones al insertar los lotes en la base de datos."""
    states_to_insert = {}
    stations_to_insert =[]
    first_data = get_first_data()
    logger.info("Found %d stations in first data page", len(first_data))

    total_stations = 0
    skipped_stations = 0
    failed_stations = 0

    with create_session() as session:

        for index, station in enumerate(first_data, start=1):
            station_number =  station["id_estacion"]
            total_stations += 1

            state_key, real_id = parse_key_real_id(
                get_key_real_id_file(session, station_number)
                )
            
            if state_key is None or real_id is None:
                skipped_stations += 1
                logger.warning("Skipping station %s because state_key or real_id are missing", station_number)
                continue

            state, name, mun, situation, lat, lon, elev = parse_metadata(
                get_daily_file(session, state_key, real_id)
                )
            
            if state is None: 
                failed_stations += 1
                logger.warning("No metadata could be found for station %s", station_number)
                stations_to_insert.append((station_number, real_id, state_key, None, None, None, None, None, None))
                continue

            states_to_insert[state_key] = state

            stations_to_insert.append(
                    (
                    station_number,
                     real_id,
                     state_key,
                     name,
                     mun,
                     situation,
                     lat,
                     lon,
                     elev,
                    )
            )

            if index % 200 == 0:
                logger.info("Processed %d/%d stations", index, len(first_data))
    
    logger.info(
        "Finished downloading metadata: %d total, %d ready to insert, %d skipped, %d failed",
        total_stations,
        len(stations_to_insert),
        skipped_stations,
        failed_stations,
    )


    with connect_database(DB_PATH) as conn:
        load_states_batch(
            conn,
            [
                (state_name, state_key)
             for state_key, state_name in states_to_insert.items()
             ],
        )

        load_stations_batch(conn, stations_to_insert)
    
    logger.info("Inserted metadata into database")

def fetch_daily_record(state_key:str, real_id:str, station_number:str)->list[tuple]:
    """Descarga, limpia y estructura el registro histórico diario de una estación.
    
    Solicita la sesión HTTP persistente asignada al hilo actual, descarga el
    archivo de climatología de Conagua, remueve sus encabezados y parsea las
    filas convirtiéndolas en registros listos para la base de datos.

    Args: 
        state_key(str): clave de estado
        real_id(str): id de la estación
        station_number(str): numero de estación

    Returns: 
        list[tuple]: Una lista de tuplas donde cada tupla representa las lecturas
        de un día con la estructura exacta:
        (station_number, date, precip, evap, tmax, tmin)

    Raises: 
        requests.RequestException: Si ocurren fallos críticos de red durante el scraping.

        
    """
    session = get_thread_session()
    raw_data = remove_header(
        get_daily_file(session,
                       state_key=state_key,
                       real_id=real_id)
                       )
    return daily_data(raw_data, station_number)

def update_all_daily_records()->None:
    """Descarga y actualiza de forma concurrente los registros climáticos diarios.

    Obtiene las claves de las estaciones desde la base de datos, descarga los
    registros históricos utilizando un Pool de hilos y almacena las lecturas
    en SQLite en bloques optimizados (batches) para evitar saturar la memoria
    RAM.

    Raises:
        sqlite3.OperationalError: Si las tablas de la base de datos no han
          sido inicializadas previamente con el comando 'setup'.
        requests.RequestException: Si ocurren fallos críticos de red durante el scraping.

    """
    batch_size = 5_000
    batch_to_store = []
    total_inserted = 0
    failed_stations = 0
    max_workers = 8

    with connect_database(DB_PATH) as conn:
        keys_ids = key_id_from_db(conn)

    with connect_database(DB_PATH) as conn:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                    executor.submit(fetch_daily_record, state_key, real_id, station_number)
                    for state_key, real_id, station_number in keys_ids
                ]
            total_stations = len(futures)

            for index, future in enumerate(as_completed(futures), start=1):
                try:
                    result = future.result()
                except Exception:
                    failed_stations += 1
                    logger.exception("Failed to process one stattion")
                    continue

                if result is None:
                    continue

                batch_to_store.extend(result)

                if len(batch_to_store) >= batch_size:
                    load_daily_data_batch(conn, batch_to_store)
                    total_inserted += len(batch_to_store)

                    if index % 50 == 0:
                        logger.info(
                            "Inserted batch of %d records, total inserted so far %d", 
                            len(batch_to_store),
                            total_inserted,
                            )
                    
                    batch_to_store.clear()
                
                if index % 100 == 0:
                    logger.info("Processed %d/%d stations", index, total_stations)


            if batch_to_store:
                load_daily_data_batch(conn, batch_to_store)
                total_inserted += len(batch_to_store)
                logger.info("Inserted final batch of %d records", len(batch_to_store))

    logger.info(
        "Finished daily records update: %d records inserted, %d failed stations",
        total_inserted,
        failed_stations,
        )



def main() -> None:
    """Punto de entrada principal para la interfaz de línea de comandos (CLI).

    Configura el sistema de logs, parsea los argumentos pasados por la
    terminal y enruta la ejecución hacia los submódulos correspondientes:
    - 'setup': Inicializa el esquema de la base de datos.
    - 'delete': Elimina de forma segura la base de datos actual.
    - 'metadata': Descarga y cataloga las estaciones disponibles.
    - 'update': Descarga los registros diarios históricos de las estaciones.
    - 'all': Ejecuta todo el pipeline desde cero.
    """
    setup_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=["setup", "delete", "metadata", "update", "all"]
    )

    args = parser.parse_args()

    if args.command == "setup":
        setup_database()
    elif args.command == "delete":
        print("ADVERTENCIA: Esta acción es irreversible y perderás todos los datos.")
        confirmacion = input(
            "Para continuar, escribe exactamente la palabra 'ELIMINAR': "
        )

        if confirmacion.strip() == "ELIMINAR":
            delete_database()
            print("Base de datos eliminada.")
        else:
            print("La palabra no coincide. Acción abortada.")
    elif args.command == "metadata":
        load_initial_metadata_conc()
    elif args.command == "update":
        update_all_daily_records()
    elif args.command == "all":
        setup_database()
        load_initial_metadata_conc()
        update_all_daily_records()

if __name__ == "__main__":
    main()