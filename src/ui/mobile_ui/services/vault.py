import os
import duckdb
from pathlib import Path
from cryptography.fernet import Fernet

BASE_DIR = Path(__file__).resolve().parent.parent
VAULT_DB = BASE_DIR / "data" / "vault.duckdb"


def _connect():
    VAULT_DB.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(VAULT_DB))


def _get_key() -> bytes:
    key_path = VAULT_DB.parent / "vault.key"
    if key_path.exists():
        return key_path.read_bytes()
    key = Fernet.generate_key()
    key_path.write_bytes(key)
    return key


FERNET = Fernet(_get_key())


def store_secret(name: str, secret: str) -> None:
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
    return FERNET.decrypt(row[0].encode("utf-8")).decode("utf-8")
