import logging
from typing import Dict, Any, Optional
from dataclasses import asdict

from ai_karen_engine.services.llm_router import ChatRequest
from ..contracts.orchestration_state import LangGraphOrchestrationState
from ..utils.message_serialization import message_to_history_entry

logger = logging.getLogger(__name__)

async def router_select_node(self, state: LangGraphOrchestrationState) -> LangGraphOrchestrationState:
    """LLM provider and model selection"""
    logger.info("Router selection processing")

    try:
        messages = state.get("messages", [])
        if not messages:
            state["selected_provider"] = "fallback"
            state["selected_model"] = "kari-fallback-v1"
            state["routing_reason"] = "No conversation context available"
            return state

        conversation_history = state.get("conversation_history") or [
            message_to_history_entry(message) for message in messages
        ]
        memory_context = state.get("memory_context") or {}
        plan = state.get("execution_plan", {})
        tool_calls = state.get("tool_calls") or []

        profile = self._profile_manager.get_active_profile()
        provider_preferences = (
            asdict(profile.provider_preferences)
            if profile and getattr(profile, "provider_preferences", None)
            else {}
        )
        request_config = state.get("request_config") or {}
        if isinstance(request_config, dict):
            preferred_provider = request_config.get("preferred_llm_provider")
            preferred_model = request_config.get("preferred_model")
            if preferred_provider and not provider_preferences.get(
                "preferred_llm_provider"
            ):
                provider_preferences["preferred_llm_provider"] = preferred_provider
            if preferred_model and not provider_preferences.get("preferred_model"):
                provider_preferences["preferred_model"] = preferred_model
        explicit_preferred_provider = (
            request_config.get("preferred_llm_provider")
            if isinstance(request_config, dict)
            else None
        )
        explicit_preferred_model = (
            request_config.get("preferred_model")
            if isinstance(request_config, dict)
            else None
        )
        preferred_model_name: Optional[str] = None
        if explicit_preferred_model:
            preferred_model_name = str(explicit_preferred_model)
        elif not explicit_preferred_provider:
            profile_chat_preference = provider_preferences.get("chat")
            if profile_chat_preference:
                preferred_model_name = str(profile_chat_preference)

        request = ChatRequest(
            message=conversation_history[-1]["content"],
            context={
                "conversation": conversation_history,
                "plan": plan,
                "safety": state.get("safety_evaluation"),
            },
            tools=[call["tool"] for call in tool_calls],
            memory_context=memory_context.get("context_summary"),
            user_preferences=provider_preferences,
            preferred_model=preferred_model_name,
            conversation_id=state.get("session_id"),
            stream=bool(state.get("streaming_enabled")),
        )

        provider_selection = await self._llm_router.select_provider(
            request,
            user_preferences=provider_preferences,
        )

        if provider_selection:
            provider_name, model_name = provider_selection
            state["selected_provider"] = provider_name
            state["selected_model"] = model_name
            state["routing_reason"] = "Selected via LLM router policy"
        else:
            state["selected_provider"] = "fallback"
            state["selected_model"] = "kari-fallback-v1"
            state["routing_reason"] = "Router returned no provider; using fallback"

    except Exception as e:
        logger.error(f"Router selection error: {e}")
        state.setdefault("errors", []).append(f"Router selection error: {str(e)}")

    return state
