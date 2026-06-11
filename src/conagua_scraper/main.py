from conagua_scraper.config import DB_PATH, DATA_DIR
from conagua_scraper.database import connect_database, create_tables


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    with connect_database(DB_PATH) as conn:
        create_tables(conn)

    print(f"Database ready at {DB_PATH}")


if __name__ == "__main__":
    main()