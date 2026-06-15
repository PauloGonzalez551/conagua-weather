import sqlite3
from pathlib import Path



def connect_database(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def delete_tables(conn:sqlite3.Connection)->None:
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS daily_records')
    cursor.execute('DROP TABLE IF EXISTS stations')
    cursor.execute('DROP TABLE IF EXISTS states')


def create_tables(conn:sqlite3.Connection)->None:
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS states (
        state_key TEXT PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
        )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stations (
        station_number TEXT PRIMARY KEY,
        real_id TEXT NOT NULL,
        state_key TEXT NOT NULL,
        name TEXT NOT NULL,
        municipio TEXT NOT NULL,
        situacion TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        elevation REAL,
        FOREIGN KEY (state_key) REFERENCES states (state_key)
    )
''')
    
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS daily_records (
          station_number TEXT NOT NULL,
          date TEXT NOT NULL,
          precip REAL,
          evap REAL,
          tmax REAL,
          tmin REAL,
          PRIMARY KEY (station_number, date),
          FOREIGN KEY (station_number) REFERENCES stations (station_number)
      )
  ''')
    
def get_existing_state_keys(conn: sqlite3.Connection) -> set[int]:
    cursor = conn.cursor()

    cursor.execute("SELECT state_key FROM states")
    return {row[0] for row in cursor.fetchall()}


def load_states_batch(
    conn: sqlite3.Connection,
    states_info: list[tuple[str, str]],
) -> None:
    conn.executemany(
        """
        INSERT OR IGNORE INTO states (name, state_key)
        VALUES (?, ?)
        """,
        states_info,
    )
    

def load_stations_batch(
    conn: sqlite3.Connection,
    stations_info: list[tuple],
) -> None:
    conn.executemany(
        """
        INSERT OR IGNORE INTO stations (station_number,
                real_id,
                state_key,
                name,
                municipio,
                situacion,
                latitude,
                longitude,
                elevation
            )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        stations_info,
    )

def load_daily_data_batch(
    conn: sqlite3.Connection,
    records_by_batch: list[tuple],
) -> None:
    conn.executemany(
        """
        INSERT OR IGNORE INTO daily_records (station_number,
                date,
                precip,
                evap,
                tmax,
                tmin
            )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        records_by_batch,
    )

def key_id_from_db(conn:sqlite3.Connection)->list[tuple[str, str]]:
    """Selects the state key and real id from the stations table

    Args:
        conn(Connection):

    Returns:
        list: list of tuples (state_key, real_id)
    """
    cursor = conn.cursor()

    cursor.execute('''SELECT state_key, real_id , station_number FROM stations''')

    return cursor.fetchall()