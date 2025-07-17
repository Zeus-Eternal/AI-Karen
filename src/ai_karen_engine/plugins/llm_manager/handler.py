"""Manage available language models for Kari."""

from ai_karen_engine.integrations.llm_registry import registry
from ai_karen_engine.integrations import model_discovery

async def run(params: dict) -> dict:
    action = params.get("action", "list")
    if action == "list":
        return {"models": list(registry.list_models()), "active": registry.active}
    if action == "refresh":
        models = model_discovery.sync_registry(model_discovery.REGISTRY_PATH)
        return {"status": "refreshed", "count": len(models)}
    if action == "select":
        model = params.get("model")
        if not model:
            return {"error": "model required"}
        try:
            registry.set_active(model)
        except KeyError:
            return {"error": f"unknown model {model}"}
        return {"status": "selected", "active": registry.active}
    return {"error": "unknown action"}
