from conagua_scraper.config import DB_PATH, DATA_DIR
from conagua_scraper.database import (connect_database,
                                    delete_tables,
                                    create_tables,
                                    load_state,
                                    get_existing_state_keys
                                    )
from conagua_scraper.scraper import (get_first_data,
                                    get_key_real_id_file,
                                    get_daily_file
                                     )
from conagua_scraper.parser import parse_key_real_id, parse_metadata



def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    with connect_database(DB_PATH) as conn:
        create_tables(conn)

    print(f"Database ready at {DB_PATH}")

    # with connect_database(DB_PATH) as conn:
    #     delete_tables(conn)

    # print(f"Database deleted at {DB_PATH}")

    

    with connect_database(DB_PATH) as conn:
        seen_states = get_existing_state_keys(conn)

        for station in get_first_data():
            station_number =  station["id_estacion"]
            state_key, real_id = parse_key_real_id(
                get_key_real_id_file(station_number)
                )
            if state_key is None or real_id is None:
                continue
            state, name, mun, situation, lat, lon, elev = parse_metadata(
                get_daily_file(state_key, real_id)
                )
            
            if state_key not in seen_states:
                load_state(conn, state, state_key)
                seen_states.add(state_key)



if __name__ == "__main__":
    main()