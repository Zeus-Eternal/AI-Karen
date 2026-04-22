from typing import Optional, Any, Dict, List
import logging
import asyncio
from datetime import datetime, timezone

from ai_karen_engine.memory.memory_service import (
    MemoryType,
    UISource,
    WebUIMemoryService,
)
from ai_karen_engine.copilotkit.session_state_manager import SessionStateManager
from .context_manager import ContextManager
from ..utils.message_serialization import (
    message_to_history_entry,
    history_entry_to_message,
)

logger = logging.getLogger(__name__)


async def resolve_memory_service(orchestrator_instance: Any) -> Optional[Any]:
    """Resolve shared memory service via service registry if possible."""

    if getattr(orchestrator_instance, "_memory_service", None) is not None or getattr(
        orchestrator_instance, "_memory_resolution_failed", False
    ):
        return orchestrator_instance._memory_service

    try:
        from ai_karen_engine.core.service_registry import (
            get_memory_service,
        )  # Lazy import

        orchestrator_instance._memory_service = await get_memory_service()
    except Exception as exc:  # pragma: no cover - optional dependency
        if not getattr(orchestrator_instance, "_memory_resolution_failed", False):
            logger.warning("Memory service unavailable: %s", exc)
        try:
            orchestrator_instance._memory_service = WebUIMemoryService()
            logger.info("Fell back to direct WebUIMemoryService initialization")
        except Exception as fallback_exc:  # pragma: no cover - optional dependency
            logger.warning(
                "Direct memory service fallback unavailable: %s", fallback_exc
            )
            orchestrator_instance._memory_resolution_failed = True
            orchestrator_instance._memory_service = None

    return orchestrator_instance._memory_service


async def ensure_context_manager(orchestrator_instance: Any) -> ContextManager:
    """Return a context manager bound to the configured memory service."""

    if getattr(orchestrator_instance, "_context_manager", None) is not None:
        return orchestrator_instance._context_manager

    memory_service = await resolve_memory_service(orchestrator_instance)
    orchestrator_instance._context_manager = ContextManager(memory_service)
    return orchestrator_instance._context_manager


async def ensure_session_state_manager(
    orchestrator_instance: Any,
) -> Optional[SessionStateManager]:
    """Resolve session state manager lazily"""
    if getattr(
        orchestrator_instance, "_session_state_manager", None
    ) is not None or getattr(
        orchestrator_instance, "_session_state_resolution_failed", False
    ):
        return orchestrator_instance._session_state_manager

    try:
        memory_service = await resolve_memory_service(orchestrator_instance)
        orchestrator_instance._session_state_manager = SessionStateManager(
            memory_service=memory_service
        )
    except Exception as exc:
        if not getattr(
            orchestrator_instance, "_session_state_resolution_failed", False
        ):
            logger.warning("Session state manager unavailable: %s", exc)
        orchestrator_instance._session_state_resolution_failed = True
        orchestrator_instance._session_state_manager = None

    return orchestrator_instance._session_state_manager


async def build_runtime_context(
    orchestrator_instance: Any,
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """Build complete runtime context from state"""
    context = {}

    # Add conversation history
    if "messages" in state:
        context["conversation_history"] = [
            message_to_history_entry(msg) for msg in state["messages"]
        ]

    # Add user info
    if "user_profile" in state:
        context["user_profile"] = state["user_profile"]
        context["user_settings"] = state["user_profile"].get("preferences", {})

    # Add memory context
    if "memory_context" in state:
        context["memory_context"] = state["memory_context"]

    # Add file context
    if "file_context" in state:
        context["file_context"] = state["file_context"]

    return context


async def load_session_continuity(
    orchestrator_instance: Any,
    session_id: str,
) -> Optional[Dict[str, Any]]:
    """Load session state for continuity"""
    session_manager = await ensure_session_state_manager(orchestrator_instance)
    if not session_manager or not session_id:
        return None

    try:
        session_state = await session_manager.load_session_state(session_id)
        return session_state
    except Exception as exc:
        logger.warning(f"Failed to load session state for {session_id}: {exc}")
        return None


async def save_session_continuity(
    orchestrator_instance: Any,
    session_id: str,
    response: str,
    messages: List[Any],
) -> None:
    """Save session state for continuity"""
    session_manager = await ensure_session_state_manager(orchestrator_instance)
    if not session_manager or not session_id:
        return

    try:
        recent_turns = []
        for msg in messages[-6:]:
            role = "user" if msg.__class__.__name__ == "HumanMessage" else "assistant"
            recent_turns.append({"role": role, "content": msg.content[:120]})

        session_state = {
            "last_user_message": messages[-2].content[:280]
            if len(messages) >= 2
            else "",
            "last_assistant_response": response[:280],
            "recent_turns": recent_turns,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await session_manager.save_session_state(session_id, session_state)
    except Exception as exc:
        logger.warning(f"Failed to save session state for {session_id}: {exc}")


def serialize_messages(messages: List[Any]) -> List[Dict[str, Any]]:
    """Serialize LangChain messages for storage/transmission"""
    return [message_to_history_entry(msg) for msg in messages]


def deserialize_messages(serialized: List[Dict[str, Any]]) -> List[Any]:
    """Deserialize messages back to LangChain format"""
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

    messages = []
    for entry in serialized:
        role = entry.get("role")
        content = entry.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
    return messages


def extract_last_user_content(messages: List[Any]) -> Optional[str]:
    """Extract last user message content"""
    for msg in reversed(messages):
        if msg.__class__.__name__ == "HumanMessage":
            return msg.content
    return None

    memory_service = await resolve_memory_service(orchestrator_instance)
    orchestrator_instance._context_manager = ContextManager(memory_service)
    return orchestrator_instance._context_manager
