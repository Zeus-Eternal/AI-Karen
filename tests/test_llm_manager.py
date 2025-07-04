import asyncio

from src.plugins.llm_manager.handler import run
from integrations.llm_registry import registry
from integrations import model_discovery


def test_refresh_models(tmp_path, monkeypatch):
    path = tmp_path / "reg.json"
    monkeypatch.setattr(model_discovery, "REGISTRY_PATH", path)
    resp = asyncio.run(run({"action": "refresh"}))
    assert resp["status"] == "refreshed"
    assert path.exists()


def test_list_models():
    resp = asyncio.run(run({"action": "list"}))
    assert resp["active"] == registry.active
    assert "local" in resp["models"]


def test_select_model_unknown():
    resp = asyncio.run(run({"action": "select", "model": "unknown"}))
    assert "error" in resp

