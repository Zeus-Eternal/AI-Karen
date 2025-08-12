import asyncio
import importlib.util
from pathlib import Path
import types
import sys


def load_memory_helper():
    fake_manager = types.SimpleNamespace(
        update_memory=lambda *a, **k: None,
        recall_context=lambda *a, **k: [],
    )
    ai_pkg = types.ModuleType("ai_karen_engine")
    core_pkg = types.ModuleType("ai_karen_engine.core")
    memory_pkg = types.ModuleType("ai_karen_engine.core.memory")
    memory_pkg.manager = fake_manager
    core_pkg.memory = memory_pkg
    ai_pkg.core = core_pkg
    sys.modules.setdefault("ai_karen_engine", ai_pkg)
    sys.modules.setdefault("ai_karen_engine.core", core_pkg)
    sys.modules.setdefault("ai_karen_engine.core.memory", memory_pkg)
    sys.modules.setdefault("ai_karen_engine.core.memory.manager", fake_manager)

    path = Path(__file__).resolve().parents[1] / "memory_manager.py"
    spec = importlib.util.spec_from_file_location("pm_memory_manager", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    return module


memory_mod = load_memory_helper()
MemoryManager = memory_mod.MemoryManager
unified_memory = memory_mod.unified_memory


def load_module():
    path = Path(__file__).resolve().parents[1] / "examples/hello-world/handler.py"
    spec = importlib.util.spec_from_file_location("hello_world_handler", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    return module


def test_memory_persistence(monkeypatch):
    stored = []

    def fake_update(user_ctx, query, result, tenant_id=None):  # pragma: no cover - simple stub
        stored.append({"user_ctx": user_ctx, "query": query, "result": result})
        return True

    def fake_recall(user_ctx, query, limit=10, tenant_id=None):  # pragma: no cover - simple stub
        return stored

    monkeypatch.setattr(unified_memory, "update_memory", fake_update)
    monkeypatch.setattr(unified_memory, "recall_context", fake_recall)

    module = load_module()
    asyncio.run(module.run({}, user_context={"user_id": "tester"}))

    memories = MemoryManager().read({"user_id": "tester"}, "greet")
    assert memories and memories[0]["result"] == "Hey there! I'm Kari—your AI co-pilot. What can I help with today?"
