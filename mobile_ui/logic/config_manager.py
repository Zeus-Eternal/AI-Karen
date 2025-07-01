import json
from pathlib import Path
import duckdb

DB_PATH = Path("mobile_ui/data/config.duckdb")


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH))


def load_config() -> dict:
    if not DB_PATH.exists():
        return {}
    con = _connect()
    con.execute("CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, data TEXT)")
    row = con.execute("SELECT data FROM settings WHERE id=1").fetchone()
    con.close()
    if row:
        return json.loads(row[0])
    return {}


def save_config(config: dict) -> None:
    con = _connect()
    con.execute("CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, data TEXT)")
    con.execute("DELETE FROM settings WHERE id=1")
    con.execute("INSERT INTO settings VALUES (1, ?)", (json.dumps(config),))
    con.close()


def update_config(**kwargs) -> None:
    config = load_config()
    config.update(kwargs)
    save_config(config)


def get_status() -> str:
    config = load_config()
    provider = config.get("provider")
    model = config.get("model")
    if not provider or not model:
        return "Pending Config"
    if provider != "Local (Ollama)" and not config.get("api_key"):
        return "Invalid"
    return "Ready"
