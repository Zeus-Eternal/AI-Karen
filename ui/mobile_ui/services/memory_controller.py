"""Persist chat memory using DuckDB."""

from pathlib import Path
try:
    import duckdb
except ModuleNotFoundError:  # pragma: no cover
    duckdb = None
try:
    import streamlit as st
except ModuleNotFoundError:  # pragma: no cover - fallback for tests
    class _DummyStreamlit:
        def __init__(self) -> None:
            self.session_state = {}

    st = _DummyStreamlit()

BASE_DIR = Path(__file__).resolve().parent.parent
MEM_DB = BASE_DIR / "data" / "memory.duckdb"


def _connect():
    if duckdb is None:
        raise ImportError("duckdb is required for memory persistence")
    MEM_DB.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(MEM_DB))


def sync_memory() -> None:
    """Save session messages to DuckDB."""
    messages = st.session_state.get("messages", [])
    con = _connect()
    con.execute(
        "CREATE TABLE IF NOT EXISTS messages (role TEXT, text TEXT)"
    )
    con.execute("DELETE FROM messages")
    for m in messages:
        con.execute(
            "INSERT INTO messages VALUES (?, ?)",
            (m.get("role", "user"), m.get("text", "")),
        )
    con.close()


def restore_memory() -> None:
    """Load messages from DuckDB into session state."""
    if not MEM_DB.exists():
        return
    con = _connect()
    con.execute(
        "CREATE TABLE IF NOT EXISTS messages (role TEXT, text TEXT)"
    )
    data = con.execute("SELECT role, text FROM messages").fetchall()
    con.close()
    st.session_state["messages"] = [
        {"role": r, "text": t} for r, t in data
    ]


def flush_memory() -> None:
    """Clear session memory and delete the database."""
    if MEM_DB.exists():
        MEM_DB.unlink()
    st.session_state["messages"] = []
