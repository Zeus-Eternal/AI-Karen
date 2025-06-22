from src.integrations.llm_registry import registry


async def run(params: dict) -> dict:
    action = params.get("action", "list")
    if action == "list":
        return {"models": list(registry.list_models()), "active": registry.active}
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
