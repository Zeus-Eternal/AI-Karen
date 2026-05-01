"""CORTEX routing intent extensions and capability-routing contract."""
from dataclasses import asdict, dataclass, field
import json
import time
from pathlib import Path
from typing import Any, Dict, Tuple, List, Optional
from ai_karen_engine.core.cortex.intent import resolve_intent as base_resolve

# Routing-specific intent patterns
ROUTING_INTENT_MAP = {
    "route to": "routing.select",
    "use provider": "routing.select",
    "switch model": "routing.select",
    "routing profile": "routing.profile",
    "model selection": "routing.select"
}

CAPABILITY_ROUTES: Dict[str, Dict[str, Any]] = {
    "time.current": {
        "triggers": ["what time", "current time", "time in", "timezone"],
        "required_capability": "time_query",
        "preferred_plugin": "time-query",
        "handler": "current_time",
        "fallback_tool": "time",
        "requires_live_data": True,
        "allow_llm_only": False,
    },
    "web.search": {
        "triggers": ["search the internet", "look online", "find current", "latest", "web search"],
        "required_capability": "web_search",
        "preferred_plugin": "intelligent-search",
        "handler": "general",
        "fallback_tool": "search",
        "requires_live_data": True,
        "allow_llm_only": False,
    },
    "weather.current": {
        "triggers": ["weather", "forecast", "temperature", "rain today"],
        "required_capability": "weather",
        "preferred_plugin": "intelligent-search",
        "handler": "weather",
        "fallback_tool": "weather",
        "requires_live_data": True,
        "allow_llm_only": False,
    },
}
_CAPABILITY_CACHE: Dict[str, Dict[str, Any]] | None = None
_CAPABILITY_CACHE_TS: float = 0.0
_CAPABILITY_CACHE_TTL_SECONDS = 60.0


@dataclass(slots=True)
class CapabilityDecision:
    intent: str
    confidence: float
    requires_tool: bool
    requires_live_data: bool
    capability: Optional[str] = None
    preferred_plugin: Optional[str] = None
    handler: Optional[str] = None
    allow_llm_only: bool = True
    missing_requirements: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def resolve_capability_decision(query: str, *, confidence: float = 0.9) -> CapabilityDecision:
    q = query.lower().strip()
    for intent, config in get_capability_routes().items():
        if any(trigger in q for trigger in config.get("triggers", [])):
            return CapabilityDecision(
                intent=intent,
                confidence=confidence,
                requires_tool=True,
                requires_live_data=bool(config.get("requires_live_data", False)),
                capability=config.get("required_capability"),
                preferred_plugin=config.get("preferred_plugin"),
                handler=config.get("handler"),
                allow_llm_only=bool(config.get("allow_llm_only", False)),
            )

    return CapabilityDecision(
        intent="general.chat",
        confidence=confidence,
        requires_tool=False,
        requires_live_data=False,
        allow_llm_only=True,
    )


def get_capability_routes(force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    """Return static + dynamically discovered capability routes.

    Discovery reads plugin manifests and enriches routes when prompt-first
    capabilities are available in the active extension set.
    """
    global _CAPABILITY_CACHE, _CAPABILITY_CACHE_TS
    now = time.time()
    if not force_refresh and _CAPABILITY_CACHE and (now - _CAPABILITY_CACHE_TS) < _CAPABILITY_CACHE_TTL_SECONDS:
        return _CAPABILITY_CACHE

    routes = {k: dict(v) for k, v in CAPABILITY_ROUTES.items()}
    for manifest in _discover_plugin_manifests():
        plugin_id = str(manifest.get("id") or manifest.get("plugin_id") or "").strip()
        if not plugin_id:
            continue
        tags = [str(tag).lower() for tag in manifest.get("tags", []) if isinstance(tag, str)]
        capabilities = manifest.get("capabilities") if isinstance(manifest.get("capabilities"), dict) else {}
        cap_name = str(capabilities.get("name") or "").strip().lower()
        prompt_first = bool(capabilities.get("prompt_first"))
        if not prompt_first:
            continue

        if plugin_id == "time-query" or "time" in tags or "timezone" in tags or "time" in cap_name:
            routes["time.current"]["preferred_plugin"] = plugin_id
        if plugin_id == "intelligent-search" or "search" in tags or "web" in tags or "search" in cap_name:
            routes["web.search"]["preferred_plugin"] = plugin_id
            routes["weather.current"]["preferred_plugin"] = plugin_id

    _CAPABILITY_CACHE = routes
    _CAPABILITY_CACHE_TS = now
    return routes


def _discover_plugin_manifests() -> List[Dict[str, Any]]:
    manifests: List[Dict[str, Any]] = []
    plugin_root = Path(__file__).resolve().parents[2] / "extensions" / "plugins"
    if not plugin_root.exists():
        return manifests
    for manifest_path in plugin_root.rglob("plugin_manifest.json"):
        try:
            manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return manifests


def resolve_routing_intent(query: str, user_ctx: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Extend existing intent resolution with routing capabilities."""
    q = query.lower().strip()
    
    # Check for routing patterns first
    for pattern, intent in ROUTING_INTENT_MAP.items():
        if pattern in q:
            return intent, {
                "match": "routing", 
                "pattern": pattern,
                "user_id": user_ctx.get("user_id"),
                "original_query": query
            }
    
    # Fallback to existing resolve_intent function
    return base_resolve(query, user_ctx)


def extract_routing_parameters(query: str) -> Dict[str, Any]:
    """Extract routing parameters from query."""
    providers = ["openai", "deepseek", "local_gguf", "huggingface", "gemini"]
    models = ["gpt-4", "gpt-3.5-turbo", "deepseek-chat", "llama2", "gemini-pro"]
    
    detected_provider = None
    detected_model = None
    
    q_lower = query.lower()
    for provider in providers:
        if provider in q_lower:
            detected_provider = provider
            break
            
    for model in models:
        if model in q_lower:
            detected_model = model
            break
            
    return {
        "requested_provider": detected_provider,
        "requested_model": detected_model,
        "task_hints": _detect_task_type(query)
    }


def _detect_task_type(query: str) -> List[str]:
    """Detect potential task types from query."""
    task_keywords = {
        "code": ["code", "program", "python", "javascript", "function", "debug"],
        "reasoning": ["think", "reason", "analyze", "solve", "logic", "explain"],
        "summarization": ["summarize", "summary", "brief", "overview"],
        "chat": ["chat", "talk", "converse", "discuss"]
    }
    
    detected_tasks = []
    q_lower = query.lower()
    
    for task, keywords in task_keywords.items():
        if any(keyword in q_lower for keyword in keywords):
            detected_tasks.append(task)
            
    return detected_tasks or ["chat"]  # Default to chat
