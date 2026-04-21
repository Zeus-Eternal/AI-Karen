import logging
import asyncio
import os
from datetime import datetime, timezone
from typing import Optional, Any

from langchain_core.messages import HumanMessage
from ai_karen_engine.memory.memory_service import MemoryType, UISource
from ai_karen_engine.copilotkit.session_state_manager import SessionStateManager
from ..contracts.orchestration_state import LangGraphOrchestrationState
from ..context.context_manager_adapter import resolve_memory_service

logger = logging.getLogger(__name__)

async def _ensure_session_state_manager(self) -> Optional[SessionStateManager]:
    """Resolve session state manager lazily."""
    if (
        getattr(self, "_session_state_manager", None) is not None
        or getattr(self, "_session_state_resolution_failed", False)
    ):
        return self._session_state_manager

    try:
        # Try to resolve via service registry or direct instantiation if available
        memory_service = await resolve_memory_service(self)
        self._session_state_manager = SessionStateManager(
            memory_service=memory_service
        )
    except Exception as exc:
        if not getattr(self, "_session_state_resolution_failed", False):
            logger.warning("Session state manager unavailable: %s", exc)
        self._session_state_resolution_failed = True
        self._session_state_manager = None

    return self._session_state_manager

async def memory_write_node(self, state: LangGraphOrchestrationState) -> LangGraphOrchestrationState:
    """Memory writing and conversation storage with salvaged session continuity writeback."""
    logger.info("Memory write processing")

    try:
        memory_write_timeout = float(
            os.getenv("LANGGRAPH_MEMORY_WRITE_TIMEOUT_SECONDS", "2.0")
        )
        memory_service = await asyncio.wait_for(
            resolve_memory_service(self),
            timeout=memory_write_timeout,
        )
        if not memory_service or not hasattr(memory_service, "store_web_ui_memory"):
            state.setdefault("warnings", []).append(
                "Memory service unavailable; skipping persistence"
            )
            return state

        response = state.get("response")
        if not response:
            return state

        tenant_id = state.get("tenant_id") or "default"
        user_id = state.get("user_id") or "anonymous"
        session_id = state.get("session_id")

        metadata = {
            "provider": state.get("selected_provider"),
            "model": state.get("selected_model"),
            "intent": state.get("detected_intent"),
            "tool_execution": state.get("tool_execution_metadata"),
            "safety": state.get("safety_evaluation"),
        }

        # 1. Store canonical conversation memory
        await asyncio.wait_for(
            memory_service.store_web_ui_memory(
                tenant_id=tenant_id,
                content=response,
                user_id=user_id,
                ui_source=UISource.API,
                session_id=session_id,
                conversation_id=session_id,
                memory_type=MemoryType.CONVERSATION,
                tags=["conversation", state.get("detected_intent", "general_chat")],
                importance_score=5,
                ai_generated=True,
                metadata=metadata,
            ),
            timeout=memory_write_timeout,
        )

        # 2. Salvaged: Store session state for continuity
        session_state_manager = await _ensure_session_state_manager(self)
        if session_state_manager and session_id:
            recent_turns = []
            messages = state.get("messages", [])
            for msg in messages[-6:]:
                role = "user" if isinstance(msg, HumanMessage) else "assistant"
                recent_turns.append({"role": role, "content": msg.content[:120]})

            session_state = {
                "last_user_message": messages[-2].content[:280]
                if len(messages) >= 2
                else "",
                "last_assistant_response": response[:280],
                "recent_turns": recent_turns,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            await session_state_manager.save_session_state(
                session_id, session_state
            )
            state.setdefault("warnings", []).append(
                f"Persisted session state writeback for {session_id}"
            )

    except asyncio.TimeoutError:
        logger.warning("Memory write timed out; skipping persistence")
        state.setdefault("warnings", []).append(
            "Memory write timed out; skipping persistence"
        )
    except Exception as e:
        logger.error(f"Memory write error: {e}")
        state["errors"].append(f"Memory write error: {str(e)}")

    return state
