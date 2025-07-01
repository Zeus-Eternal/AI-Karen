import json
from pathlib import Path
import duckdb

from .vault import store_secret, load_secret

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
        data = json.loads(row[0])
        if "api_key_ref" in data:
            data["api_key"] = load_secret(data["api_key_ref"]) or ""
        return data
    return {}


def save_config(config: dict) -> None:
    api_key = config.pop("api_key", "")
    if api_key:
        ref = config.get("api_key_ref", "llm_api_key")
        store_secret(ref, api_key)
        config["api_key_ref"] = ref
    con = _connect()
    con.execute(
        "CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, data TEXT)"
    )
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
    if provider != "Local (Ollama)":
        key = config.get("api_key") or load_secret(config.get("api_key_ref", "llm_api_key"))
        if not key:
            return "Invalid"
    return "Ready"
