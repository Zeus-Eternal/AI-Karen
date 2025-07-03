import os
try:
    import duckdb
except ModuleNotFoundError:  # pragma: no cover
    duckdb = None
from pathlib import Path
try:
    from cryptography.fernet import Fernet
except ModuleNotFoundError:  # pragma: no cover - optional for tests
    Fernet = None

BASE_DIR = Path(__file__).resolve().parent.parent
VAULT_DB = BASE_DIR / "data" / "vault.duckdb"


def _connect():
    if duckdb is None:
        raise ImportError("duckdb is required for secret storage")
    VAULT_DB.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(VAULT_DB))


def _get_key() -> bytes:
    if Fernet is None:
        raise ImportError("cryptography is required for secret storage")
    key_path = VAULT_DB.parent / "vault.key"
    if key_path.exists():
        return key_path.read_bytes()
    key = Fernet.generate_key()
    key_path.write_bytes(key)
    return key


FERNET = Fernet(_get_key()) if Fernet is not None else None


def store_secret(name: str, secret: str) -> None:
    if FERNET is None:
        raise ImportError("cryptography is required for secret storage")
    con = _connect()
    con.execute(
        "CREATE TABLE IF NOT EXISTS secrets (name TEXT PRIMARY KEY, secret TEXT)"
    )
    token = FERNET.encrypt(secret.encode("utf-8")).decode("utf-8")
    con.execute("INSERT OR REPLACE INTO secrets VALUES (?, ?)", (name, token))
    con.close()


def load_secret(name: str) -> str | None:
    if not VAULT_DB.exists():
        return None
    con = _connect()
    con.execute(
        "CREATE TABLE IF NOT EXISTS secrets (name TEXT PRIMARY KEY, secret TEXT)"
    )
    row = con.execute("SELECT secret FROM secrets WHERE name=?", (name,)).fetchone()
    con.close()
    if not row:
        return None
    if FERNET is None:
        raise ImportError("cryptography is required for secret storage")
    return FERNET.decrypt(row[0].encode("utf-8")).decode("utf-8")
