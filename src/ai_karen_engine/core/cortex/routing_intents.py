"""CORTEX routing intent extensions and capability-routing contract."""
from dataclasses import asdict, dataclass, field
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
    "search.general": {
        "triggers": ["search the internet", "look online", "find current", "latest", "web search"],
        "required_capability": "internet_search",
        "preferred_plugin": "intelligent-search",
        "handler": "general",
        "fallback_tool": "search",
        "requires_live_data": True,
        "allow_llm_only": False,
    },
    "search.weather": {
        "triggers": ["weather", "forecast", "temperature", "rain today"],
        "required_capability": "internet_search",
        "preferred_plugin": "intelligent-search",
        "handler": "weather",
        "fallback_tool": "search",
        "requires_live_data": True,
        "allow_llm_only": False,
    },
}


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
    for intent, config in CAPABILITY_ROUTES.items():
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
    providers = ["openai", "deepseek", "huggingface", "gemini", "builtin_transformers", "builtin_vllm", "ollama"]
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
