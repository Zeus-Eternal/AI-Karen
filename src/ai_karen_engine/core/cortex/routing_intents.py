"""
CORTEX routing intent extension - adds routing intents to existing dispatch system.
"""
from typing import Any, Dict, Tuple, List
from ai_karen_engine.core.cortex.intent import resolve_intent as base_resolve

# Routing-specific intent patterns
ROUTING_INTENT_MAP = {
    "route to": "routing.select",
    "use provider": "routing.select",
    "switch model": "routing.select",
    "routing profile": "routing.profile",
    "model selection": "routing.select"
}


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
    providers = ["openai", "deepseek", "llamacpp", "huggingface", "gemini"]
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
