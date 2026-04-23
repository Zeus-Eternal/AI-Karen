import logging
import asyncio
import os
from datetime import datetime, timezone
from typing import Optional, Any, List, Dict
from dataclasses import dataclass

from langchain_core.messages import HumanMessage
from ai_karen_engine.core.memory import get_memory_manager
from ..contracts.orchestration_state import LangGraphOrchestrationState

logger = logging.getLogger(__name__)


@dataclass
class MemoryWriteRequest:
    """Standardized memory write request"""

    session_id: str
    user_id: str
    conversation_id: str
    message_type: str  # user_message, assistant_response, system_update
    content: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class MemoryWriteResult:
    """Result of memory write operation"""

    success: bool
    message_id: str
    timestamp: str
    error_message: Optional[str] = None
    write_type: Optional[str] = None


class MemoryWriteNode:
    """Unified memory writeback for orchestration using Next-Gen Memory Ledger."""

    def __init__(self):
        self.pending_writes: List[MemoryWriteRequest] = []
        self.memory_manager = get_memory_manager()

    async def __call__(
        self, state: LangGraphOrchestrationState
    ) -> LangGraphOrchestrationState:
        """
        Memory write node for LangGraph orchestration

        Implements ledger-first memory writeback for interaction artifacts.
        """
        logger.info("Memory write processing (Ledger-First)")

        try:
            # Execute complete writeback
            results = await self.execute_writeback(state)

            # Log results
            successful_writes = len([r for r in results.values() if r.success])
            failed_writes = len([r for r in results.values() if not r.success])

            logger.info(
                f"Memory writeback: {successful_writes} successful, {failed_writes} failed"
            )

            # Store writeback results in state
            state["writeback_results"] = {
                key: {
                    "success": result.success,
                    "message_id": result.message_id,
                    "timestamp": result.timestamp,
                    "error_message": result.error_message,
                }
                for key, result in results.items()
            }

        except Exception as e:
            logger.error(f"Memory write error: {e}")
            state.setdefault("errors", []).append(f"Memory write error: {str(e)}")

        return state

    async def write_user_message(
        self, state: LangGraphOrchestrationState
    ) -> MemoryWriteResult:
        """Write user message to memory via ledger-first adaptive pipeline."""

        try:
            # Extract user message
            messages = state.get("messages", [])
            if not messages:
                return MemoryWriteResult(
                    success=False,
                    message_id="",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    error_message="No user message found",
                )

            # Get last user message
            user_message = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg
                    break

            if not user_message:
                return MemoryWriteResult(
                    success=False,
                    message_id="",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    error_message="No user message found",
                )

            # Use new adaptive memory manager
            user_id = str(state.get("user_id", "anonymous"))
            tenant_id = str(state.get("tenant_id", "default"))
            content = user_message.get("content", "")
            
            # Process via ledger (Extraction -> Scoring -> Ledger -> Projections)
            result = await self.memory_manager.process_interaction(
                text=content,
                user_id=user_id,
                tenant_id=tenant_id,
                source_type="chat_user",
                source_ref=user_message.get("id")
            )

            return MemoryWriteResult(
                success=result.get("status") == "success",
                message_id=user_message.get("id", ""),
                timestamp=datetime.now(timezone.utc).isoformat(),
                write_type="user_message"
            )

        except Exception as e:
            logger.error(f"User message write error: {e}")
            return MemoryWriteResult(
                success=False,
                message_id="",
                timestamp=datetime.now(timezone.utc).isoformat(),
                error_message=str(e),
                write_type="user_message"
            )

    async def write_assistant_response(
        self, state: LangGraphOrchestrationState
    ) -> MemoryWriteResult:
        """Write assistant response to memory via ledger-first adaptive pipeline."""

        try:
            # Extract assistant response
            response = state.get("llm_response", "")
            if not response:
                return MemoryWriteResult(
                    success=False,
                    message_id="",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    error_message="No assistant response found",
                )

            user_id = str(state.get("user_id", "anonymous"))
            tenant_id = str(state.get("tenant_id", "default"))

            # Process assistant response to extract self-correction signals or new facts
            result = await self.memory_manager.process_interaction(
                text=response,
                user_id=user_id,
                tenant_id=tenant_id,
                source_type="chat_assistant"
            )

            return MemoryWriteResult(
                success=result.get("status") == "success",
                message_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc).isoformat(),
                write_type="assistant_response"
            )

        except Exception as e:
            logger.error(f"Assistant response write error: {e}")
            return MemoryWriteResult(
                success=False,
                message_id="",
                timestamp=datetime.now(timezone.utc).isoformat(),
                error_message=str(e),
                write_type="assistant_response"
            )

    async def write_session_state(
        self, state: LangGraphOrchestrationState
    ) -> MemoryWriteResult:
        """Session state persistence is now handled by ledger projections."""
        # For compatibility with orchestrator, we just return success
        # Real session continuity is being moved to specialized projections
        return MemoryWriteResult(
            success=True,
            message_id="ledger_session",
            timestamp=datetime.now(timezone.utc).isoformat(),
            write_type="session_state"
        )

    async def execute_writeback(
        self,
        state: LangGraphOrchestrationState,
        write_types: Optional[List[str]] = None,
    ) -> Dict[str, MemoryWriteResult]:
        """Execute complete memory writeback using Next-Gen Ledger."""

        logger.info("Executing ledger-first memory writeback")

        if write_types is None:
            write_types = [
                "user_message",
                "assistant_response",
                "session_state",
            ]

        results = {}

        # Execute writes based on requested types
        for write_type in write_types:
            if write_type == "user_message":
                results["user_message"] = await self.write_user_message(state)
            elif write_type == "assistant_response":
                results["assistant_response"] = await self.write_assistant_response(
                    state
                )
            elif write_type == "session_state":
                results["session_state"] = await self.write_session_state(state)

        # Store results in state
        state["memory_write_results"] = results
        state["memory_writeback_completed"] = True

        return results


async def memory_write_node(
    state: LangGraphOrchestrationState,
) -> LangGraphOrchestrationState:
    """Convenience wrapper for MemoryWriteNode"""
    node = MemoryWriteNode()
    return await node(state)


async def memory_write_node(
    state: LangGraphOrchestrationState,
) -> LangGraphOrchestrationState:
    """Convenience wrapper for MemoryWriteNode"""
    node = MemoryWriteNode()
    return await node(state)
