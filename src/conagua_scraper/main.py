import logging
import argparse

from conagua_scraper.config import DB_PATH, DATA_DIR
from conagua_scraper.database import (connect_database,
                                    delete_tables,
                                    create_tables,
                                    load_states_batch,
                                    load_stations_batch,
                                    )
from conagua_scraper.scraper import (get_first_data,
                                    get_key_real_id_file,
                                    get_daily_file,
                                    create_session,
                                     )
from conagua_scraper.parser import parse_key_real_id, parse_metadata

logger = logging.getLogger(__name__)

def setup_logging()->None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def delete_database()->None:

    with connect_database(DB_PATH) as conn:
        delete_tables(conn)

    print(f"Database deleted at {DB_PATH}")

def setup_database()->None:

    DATA_DIR.mkdir(exist_ok=True)

    with connect_database(DB_PATH) as conn:
        create_tables(conn)

    print(f"Database ready at {DB_PATH}")

    # with connect_database(DB_PATH) as conn:
    #     delete_tables(conn)

    # print(f"Database deleted at {DB_PATH}")

def load_initial_metadata()->None:
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



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=["setup", "delete", "metadata", "update", "all"]
    )

    args = parser.parse_args()

    if args.command == "setup":
        setup_database()
    if args.command == "delete":
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
        load_initial_metadata()
    elif args.command == "update":
        logger.warning("Update function hasn't been created yet")
    elif args.command == "all":
        setup_database()
        load_initial_metadata()

if __name__ == "__main__":
    main()