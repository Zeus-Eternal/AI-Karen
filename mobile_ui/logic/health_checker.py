"""Basic runtime diagnostics for the mobile UI."""

from src.integrations.llm_registry import registry as llm_registry
from mobile_ui.logic.memory_controller import MEM_DB
from mobile_ui.logic.vault import VAULT_DB


def get_system_health() -> dict:
    """Return a summary of backend availability."""

    duckdb_ok = MEM_DB.exists() or VAULT_DB.exists()
    return {
        "redis": "ok",  # in-memory stub always available
        "duckdb": "ok" if duckdb_ok else "init",
        "milvus": "ok",  # local vector store
        "llm": llm_registry.active,
    }

