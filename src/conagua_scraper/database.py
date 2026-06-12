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
          station_id TEXT NOT NULL,
          date TEXT NOT NULL,
          precip REAL,
          evap REAL,
          tmax REAL,
          tmin REAL,
          PRIMARY KEY (station_id, date),
          FOREIGN KEY (station_id) REFERENCES stations (real_id)
      )
  ''')
    
def get_existing_state_keys(conn: sqlite3.Connection) -> set[int]:
    cursor = conn.cursor()

    cursor.execute("SELECT state_key FROM states")
    return {row[0] for row in cursor.fetchall()}

# def load_state(conn:sqlite3.Connection, state_name, state_key)->None:
#     cursor = conn.cursor()

#     cursor.execute('''
#             INSERT OR IGNORE INTO states (name, state_key)
#             VALUES (? , ?)
#         ''', (state_name, state_key))

def load_states_batch(
    conn: sqlite3.Connection,
    states_info: list[tuple[str, int]],
) -> None:
    conn.executemany(
        """
        INSERT OR IGNORE INTO states (name, state_key)
        VALUES (?, ?)
        """,
        states_info,
    )
    
# def load_station(conn:sqlite3.Connection,
#                 station_number,
#                 real_id,
#                 state_key,
#                 name,
#                 municipio,
#                 situacion,
#                 latitude,
#                 longitude,
#                 elevation
# )->None:
#     cursor = conn.cursor()

#     cursor.execute('''
#             INSERT OR IGNORE INTO stations (station_number,
#                 real_id,
#                 state_key,
#                 name,
#                 municipio,
#                 situacion,
#                 latitude,
#                 longitude,
#                 elevation
#                 )
#             VALUES (?, ?, ?, ?, ?, ?, ?, ? ,?)
#             ''', (station_number,
#                     real_id,
#                     state_key,
#                     name,
#                     municipio,
#                     situacion,
#                     latitude,
#                     longitude,
#                     elevation
#                     )
#                 )
    

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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        stations_info,
    )