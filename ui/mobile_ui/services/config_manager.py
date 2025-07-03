import json
from pathlib import Path
try:
    import duckdb
except ModuleNotFoundError:  # pragma: no cover
    duckdb = None

from ui.mobile_ui.services.vault import store_secret, load_secret

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "config.duckdb"


def _connect():
    if duckdb is None:
        raise ImportError("duckdb is required for configuration persistence")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH))


def _init_db(con: duckdb.DuckDBPyConnection) -> None:
    """Ensure required tables exist."""
    con.execute(
        "CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, data TEXT)"
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS providers (name TEXT PRIMARY KEY, data TEXT)"
    )


def load_config() -> dict:
    """Return saved configuration with DeepSeek defaults."""
    if not DB_PATH.exists():
        return {
            "provider": "deepseek",
            "persona": "default",
            "tone": "neutral",
            "language": "en",
            "emotion": "neutral",
        }
    con = _connect()
    _init_db(con)
    row = con.execute("SELECT data FROM settings WHERE id=1").fetchone()
    con.close()
    if row:
        data = json.loads(row[0])
        data.setdefault("provider", "deepseek")
        data.setdefault("persona", "default")
        data.setdefault("tone", "neutral")
        data.setdefault("language", "en")
        data.setdefault("emotion", "neutral")
        if "api_key_ref" in data:
            data["api_key"] = load_secret(data["api_key_ref"]) or ""
        return data
    return {
        "provider": "deepseek",
        "persona": "default",
        "tone": "neutral",
        "language": "en",
        "emotion": "neutral",
    }


def save_config(config: dict) -> None:
    api_key = config.pop("api_key", "")
    if api_key:
        ref = config.get("api_key_ref", "llm_api_key")
        store_secret(ref, api_key)
        config["api_key_ref"] = ref
    con = _connect()
    _init_db(con)
    con.execute("DELETE FROM settings WHERE id=1")
    con.execute("INSERT INTO settings VALUES (1, ?)", (json.dumps(config),))
    con.close()


def update_config(**kwargs) -> None:
    config = load_config()
    config.update(kwargs)
    save_config(config)


def save_provider_config(provider: str, config: dict) -> None:
    """Store provider-specific configuration and credentials."""
    api_key = config.pop("api_key", "")
    if api_key:
        ref = config.get("api_key_ref", f"{provider}_api_key")
        store_secret(ref, api_key)
        config["api_key_ref"] = ref
    con = _connect()
    _init_db(con)
    con.execute(
        "INSERT OR REPLACE INTO providers VALUES (?, ?)",
        (provider, json.dumps(config)),
    )
    con.close()


def load_provider_configs() -> dict:
    """Return mapping of provider name to saved config."""
    if not DB_PATH.exists():
        return {}
    con = _connect()
    _init_db(con)
    rows = con.execute("SELECT name, data FROM providers").fetchall()
    con.close()
    result = {}
    for name, data in rows:
        try:
            meta = json.loads(data)
        except Exception:
            meta = {}
        if "api_key_ref" in meta:
            meta["api_key"] = load_secret(meta["api_key_ref"]) or ""
        result[name] = meta
    return result


def get_status() -> str:
    config = load_config()
    provider = config.get("provider")
    model = config.get("model")
    if not provider or not model:
        return "Pending Config"
    local_providers = {"local", "ollama_cpp"}
    if provider not in local_providers:
        key = config.get("api_key") or load_secret(config.get("api_key_ref", "llm_api_key"))
        if not key:
            return "Invalid"
    return "Ready"


def list_configured_providers() -> list[str]:
    """Return provider names that have saved configuration."""
    return sorted(load_provider_configs().keys())


def get_provider_config(provider: str) -> dict:
    """Return saved config for a single provider."""
    return load_provider_configs().get(provider, {})
