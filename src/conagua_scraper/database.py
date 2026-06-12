import sqlite3
from pathlib import Path

def connect_database(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def create_tables(conn:sqlite3.Connection)->None:
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS states (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        state_key TEXT NOT NULL
        )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stations (
        station_id INTEGER PRIMARY KEY,
        real_id TEXT NOT NULL,
        state_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        municipio TEXT NOT NULL,
        situacion TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        elevation REAL,
        FOREIGN KEY (state_id) REFERENCES states (id)
    )
''')
    
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS daily_records (
          station_id INTEGER NOT NULL,
          date TEXT NOT NULL,
          precip REAL,
          evap REAL,
          tmax REAL,
          tmin REAL,
          PRIMARY KEY (station_id, date),
          FOREIGN KEY (station_id) REFERENCES stations (station_id)
      )
  ''')
    
def get_existing_state_keys(conn: sqlite3.Connection) -> set[int]:
    cursor = conn.cursor()

    cursor.execute("SELECT state_key FROM states")
    return {row[0] for row in cursor.fetchall()}

def load_state(conn:sqlite3.Connection, state_name, state_key)->None:
    cursor = conn.cursor()

    cursor.execute('''
            INSERT OR IGNORE INTO states (name, state_key)
            VALUES (? , ?)
        ''', (state_name, state_key))
