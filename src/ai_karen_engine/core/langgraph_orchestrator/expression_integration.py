"""Integration between LangGraph orchestration and ExpressionGateway.

This module provides helper functions to convert orchestration state into
ExpressionTask format for the ExpressionGateway.
"""

import logging
import uuid
from typing import Any, Dict, Optional

from ai_karen_engine.core.expression.contracts import ExpressionTask

logger = logging.getLogger(__name__)


def build_expression_task_from_state(
    state: Dict[str, Any],
    *,
    task_kind: str = "chat",
    response_mode: str = "text",
    required_capabilities: Optional[list[str]] = None,
    forbidden_capabilities: Optional[list[str]] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    timeout_ms: int = 30000,
) -> ExpressionTask:
    """Build an ExpressionTask from orchestration state.

    Args:
        state: The LangGraph orchestration state
        task_kind: The kind of task (chat, synthesis, etc.)
        response_mode: The desired response mode
        required_capabilities: Required capabilities for the engine
        forbidden_capabilities: Capabilities the engine must NOT have
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        timeout_ms: Request timeout in milliseconds

    Returns:
        An ExpressionTask ready for ExpressionGateway.generate()
    """
    # Extract messages from state
    messages = []
    for msg in state.get("messages", []):
        if hasattr(msg, "type") and hasattr(msg, "content"):
            messages.append({"role": msg.type, "content": str(msg.content)})
        elif isinstance(msg, dict):
            messages.append({
                "role": msg.get("role", msg.get("type", "user")),
                "content": str(msg.get("content", ""))
            })
        else:
            # Fallback for unknown message types
            messages.append({"role": "user", "content": str(msg)})

    # Extract provider/model preferences from request config
    request_config = state.get("request_config") or {}
    preferred_provider = None
    preferred_model = None

    if isinstance(request_config, dict):
        preferred_provider = request_config.get("preferred_llm_provider")
        preferred_model = request_config.get("preferred_model")

    # Fallback to profile preferences if not in request config
    if not preferred_provider or not preferred_model:
        try:
            from ai_karen_engine.core.memory.profile_synthesis.profile_manager import ProfileManager
            profile_manager = ProfileManager()
            profile = profile_manager.get_active_profile()
            if profile and hasattr(profile, "provider_preferences"):
                prefs = profile.provider_preferences
                if isinstance(prefs, dict):
                    if not preferred_provider:
                        preferred_provider = prefs.get("preferred_llm_provider")
                    if not preferred_model:
                        chat_pref = prefs.get("chat")
                        if chat_pref:
                            preferred_model = str(chat_pref)
        except Exception as e:
            logger.debug(f"Could not load profile preferences: {e}")

    # Determine required capabilities from cortex/intent
    required_caps = required_capabilities or ["text"]
    forbidden_caps = forbidden_capabilities or []

    cortex = state.get("cortex")
    if cortex:
        if hasattr(cortex, "intent"):
            intent = cortex.intent
            # Code models shouldn't handle chat
            if intent.primary_intent == "general.chat":
                forbidden_caps.extend(["code_only"])
        elif isinstance(cortex, dict):
            intent_data = cortex.get("intent", {})
            if isinstance(intent_data, dict):
                if intent_data.get("primary_intent") == "general.chat":
                    forbidden_caps.extend(["code_only"])

    return ExpressionTask(
        task_id=state.get("task_id") or str(uuid.uuid4()),
        kind=task_kind,
        messages=messages,
        response_mode=response_mode,
        required_capabilities=required_caps,
        forbidden_capabilities=forbidden_caps,
        preferred_provider=preferred_provider,
        preferred_model=preferred_model,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout_ms=timeout_ms,
        correlation_id=state.get("correlation_id"),
        request_id=state.get("request_id"),
        metadata={
            "session_id": state.get("session_id"),
            "user_id": state.get("user_id"),
            "intent": state.get("detected_intent"),
            "streaming_enabled": state.get("streaming_enabled", False),
            "tool_calls": state.get("tool_calls", []),
            "memory_context": state.get("memory_context", {}),
        }
    )


def convert_expression_result_to_metadata(
    result: Any,
    state: Dict[str, Any],
    latency_ms: Optional[float] = None,
) -> Dict[str, Any]:
    """Convert ExpressionResult to the metadata format expected by the orchestrator.

    Args:
        result: Either an ExpressionResult object or a dict with similar fields
        state: The original orchestration state
        latency_ms: Override latency if needed

    Returns:
        A dict with the expected metadata structure
    """
    if hasattr(result, "provider"):
        # It's an ExpressionResult object
        provider = result.provider
        model = result.model
        engine_id = result.engine_id
        engine_mode = result.engine_mode
        runtime_engine = result.runtime_engine
        response_source = result.response_source
        degraded = result.degraded
        degradation_reason = result.degradation_reason
        actual_latency = result.latency_ms
        attempts = result.attempts or []
        skipped = result.skipped or []
        result_metadata = result.metadata or {}
    elif isinstance(result, dict):
        # It's already a dict
        provider = result.get("provider") or result.get("actual_provider")
        model = result.get("model") or result.get("actual_model")
        engine_id = result.get("engine_id", "unknown")
        engine_mode = result.get("engine_mode", "unknown")
        runtime_engine = result.get("runtime_engine")
        response_source = result.get("response_source", "unknown")
        degraded = result.get("degraded", False)
        degradation_reason = result.get("degradation_reason")
        actual_latency = result.get("latency_ms", latency_ms)
        attempts = result.get("attempts", [])
        skipped = result.get("skipped", [])
        result_metadata = result.get("metadata", {})
    else:
        # Fallback for unknown result types
        provider = None
        model = None
        engine_id = "unknown"
        engine_mode = "unknown"
        runtime_engine = None
        response_source = "unknown"
        degraded = True
        degradation_reason = "unknown_result_type"
        actual_latency = latency_ms or 0
        attempts = []
        skipped = []
        result_metadata = {}

    # Get requested preferences from state
    request_config = state.get("request_config") or {}
    requested_provider = request_config.get("preferred_llm_provider") if isinstance(request_config, dict) else None
    requested_model = request_config.get("preferred_model") if isinstance(request_config, dict) else None

    # Determine if provider changed
    provider_changed = (
        str(requested_provider or "").strip()
        and str(provider or "").strip()
        and str(requested_provider).strip().lower() != str(provider).strip().lower()
    )

    # Build the metadata structure expected by the orchestrator
    llm_metadata = {
        "requested_provider": requested_provider or provider,
        "requested_model": requested_model or model,
        "actual_provider": provider,
        "actual_model": model,
        "provider": provider,
        "model_id": model,
        "model_name": model,
        "runtime_engine": runtime_engine or str(provider).replace("builtin_", ""),
        "response_source": response_source,
        "source": response_source,
        "engine_id": engine_id,
        "engine_mode": engine_mode,
        "fallback_level": 1 if provider_changed else 0,
        "degraded_mode": degraded,
        "is_degraded": degraded,
        "used_fallback": degraded or provider_changed,
        "attempts": attempts,
        "skipped_engines": skipped,
        "streaming_enabled": state.get("streaming_enabled", False),
    }

    if actual_latency is not None:
        llm_metadata["latency_ms"] = actual_latency
        llm_metadata["duration"] = actual_latency / 1000

    if degraded and not degradation_reason:
        llm_metadata["degradation_reason"] = (
            "requested_provider_unavailable" if provider_changed else "provider_fallback"
        )

    # Merge any additional metadata from the result
    llm_metadata.update(result_metadata)

    return llm_metadata
