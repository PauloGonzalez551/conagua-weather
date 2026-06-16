# Conagua Weather Scraper 🌧️🇲🇽

A high-performance, concurrent Python scraper designed to systematically extract, parse, and store the complete catalog of weather stations and historical daily climate records from Mexico's National Meteorological Service (**SMN / Conagua**).

This project focuses on executing robust network operations under harsh server conditions, utilizing concurrent threading architectures and relational storage to build a reliable local climate database.

---

##  Key Features

* **Concurrent Architecture:** Uses Python's `ThreadPoolExecutor` to parallelize network I/O bound tasks, reducing download times for over 5,500 stations from hours to minutes.
* **Thread-Local Sessions:** Implements Thread-Local Storage (TLS) via `requests.Session()` to reuse underlying TCP/HTTP connections (Keep-Alive), minimizing handshake overhead.
* **Polite Scraping (Anti-Ban):** Features adaptive worker regulation (`max_workers=3`) combined with randomized request execution delays (Jitter) to safely navigate remote server rate limits and prevent `RemoteDisconnected` or `403 Forbidden` errors.
* **Deterministic Resource Management:** Core functions are wrapped in clean context managers to prevent memory and file descriptor leaks.
* **Relational Storage:** Stores parsed data into a local SQLite database utilizing atomic transactions, optimized batch inserts (`executemany`), and `ROLLBACK` protections upon failures.
* **Robust Observability:** Integrated with comprehensive logging to track extraction statistics (`total`, `ready`, `skipped`, `failed`) and real-time station debugging.

---

## 📂 Project Structure

```text
conagua-weather/
│
├── conagua_scraper/
│   ├── __init__.py
│   ├── main.py          # CLI entrypoint for orchestrating execution modes
│   ├── scraper.py       # Threading logic and HTTP request management
│   ├── parser.py        # Raw HTML/text extraction algorithms
│   └── database.py      # SQLite schema creation and batch transaction execution
│
├── data/                # Local data storage directory (Git ignored)
│   └── estaciones.sqlite3
│
├── .gitignore           # Safeguards binary databases and virtual environments
└── README.md

## Instalation

git clone [https://github.com/PauloGonzalez551/conagua-weather.git](https://github.com/PauloGonzalez551/conagua-weather.git)
cd conagua-weather

You can run python -m conagua_scraper.main setup 
for initializing the database, and python -m conagua_scraper.main metadata
to download the initial stations data, however you can't run the update function
unless there's already some state_key and real_ids from the station already
 
On the contrary run python -m conagua_scraper.main setup 
for a complete setup, metadata load and update daily records




In accordance with software engineering best practices regarding Infrastructure as Code (IaC), this repository tracks only the codebase, configuration, and structural logic.
The actual binary .sqlite3 files and cached data directories are explicitly managed through .gitignore. Every user cloning this repository can generate their own clean, up-to-date instance of the database by executing the startup metadata CLI command.


