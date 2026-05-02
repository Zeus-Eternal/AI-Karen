from __future__ import annotations
from .engines import BuiltinProviderEngine, DisabledEngine, OpenAICompatibleEngine


def get_engine(engine_id: str, engine_type: str | None = None):
    by_id = {
        "builtin": BuiltinProviderEngine(),
        "openai_compatible": OpenAICompatibleEngine(),
        "disabled": DisabledEngine(),
    }
    by_type = {
        "builtin_provider_engine": BuiltinProviderEngine(),
        "openai_compatible": OpenAICompatibleEngine(),
        "disabled_engine": DisabledEngine(),
    }
    if engine_type and engine_type in by_type:
        return by_type[engine_type]
    return by_id.get(engine_id, DisabledEngine())
