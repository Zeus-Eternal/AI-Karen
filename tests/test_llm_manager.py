import asyncio

from plugins.llm_manager.handler import run
from src.integrations.llm_registry import registry


def test_list_models():
    resp = asyncio.run(run({"action": "list"}))
    assert resp["active"] == registry.active
    assert "local" in resp["models"]


def test_select_model_unknown():
    resp = asyncio.run(run({"action": "select", "model": "unknown"}))
    assert "error" in resp
