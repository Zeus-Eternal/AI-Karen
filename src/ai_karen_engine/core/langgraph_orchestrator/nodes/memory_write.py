import logging
import asyncio
import os
from datetime import datetime, timezone
from typing import Optional, Any, List, Dict
from dataclasses import dataclass

from langchain_core.messages import HumanMessage
from ai_karen_engine.memory.memory_service import MemoryType, UISource
from ai_karen_engine.copilotkit.session_state_manager import SessionStateManager
from ..contracts.orchestration_state import LangGraphOrchestrationState
from ..context.context_manager_adapter import resolve_memory_service

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
    """Unified memory writeback for orchestration"""

    def __init__(self):
        self.pending_writes: List[MemoryWriteRequest] = []

    async def __call__(
        self, state: LangGraphOrchestrationState
    ) -> LangGraphOrchestrationState:
        """
        Memory write node for LangGraph orchestration

        Implements unified memory writeback for session continuity and persistence
        """
        logger.info("Memory write processing")

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
        """Write user message to memory"""

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

            # Create write request
            request = MemoryWriteRequest(
                session_id=state.get("session_id", ""),
                user_id=state.get("user_id", ""),
                conversation_id=state.get("conversation_id", ""),
                message_type="user_message",
                content=user_message.get("content", ""),
                metadata={
                    "message_id": user_message.get("id", ""),
                    "timestamp": user_message.get("timestamp"),
                    "intent": state.get("detected_intent"),
                    "safety_status": state.get("safety_status"),
                },
            )

            # Execute write
            result = await self._execute_write(request, state)

            return result

        except Exception as e:
            logger.error(f"User message write error: {e}")
            return MemoryWriteResult(
                success=False,
                message_id="",
                timestamp=datetime.now(timezone.utc).isoformat(),
                error_message=str(e),
            )

    async def write_assistant_response(
        self, state: LangGraphOrchestrationState
    ) -> MemoryWriteResult:
        """Write assistant response to memory"""

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

            # Create write request
            request = MemoryWriteRequest(
                session_id=state.get("session_id", ""),
                user_id=state.get("user_id", ""),
                conversation_id=state.get("conversation_id", ""),
                message_type="assistant_response",
                content=response,
                metadata={
                    "selected_provider": state.get("selected_provider"),
                    "selected_model": state.get("selected_model"),
                    "execution_plan": state.get("execution_plan"),
                    "routing_reason": state.get("routing_reason"),
                    "response_summary": state.get("response_summary"),
                    "tool_results": state.get("tool_results"),
                    "synthesis_metadata": state.get("synthesis_metadata"),
                },
            )

            # Execute write
            result = await self._execute_write(request, state)

            return result

        except Exception as e:
            logger.error(f"Assistant response write error: {e}")
            return MemoryWriteResult(
                success=False,
                message_id="",
                timestamp=datetime.now(timezone.utc).isoformat(),
                error_message=str(e),
            )

    async def write_session_state(
        self, state: LangGraphOrchestrationState
    ) -> MemoryWriteResult:
        """Write session state update to memory"""

        try:
            # Create session state update
            session_update = {
                "session_id": state.get("session_id"),
                "user_id": state.get("user_id"),
                "conversation_id": state.get("conversation_id"),
                "last_message_timestamp": state.get("timestamp"),
                "runtime_level": state.get("runtime_level", "FULL"),
                "safety_status": state.get("safety_status"),
                "selected_provider": state.get("selected_provider"),
                "selected_model": state.get("selected_model"),
                "execution_plan": state.get("execution_plan"),
                "streaming_enabled": state.get("streaming_enabled", False),
                "metadata": {
                    "message_count": len(state.get("messages", [])),
                    "tool_executions": len(state.get("tool_results", [])),
                    "errors_count": len(state.get("errors", [])),
                    "processing_time_ms": state.get("processing_time_ms"),
                },
            }

            # Create write request
            request = MemoryWriteRequest(
                session_id=state.get("session_id", ""),
                user_id=state.get("user_id", ""),
                conversation_id=state.get("conversation_id", ""),
                message_type="system_update",
                content=str(session_update),
                metadata=session_update,
            )

            # Execute write
            result = await self._execute_write(request, state)

            return result

        except Exception as e:
            logger.error(f"Session state write error: {e}")
            return MemoryWriteResult(
                success=False,
                message_id="",
                timestamp=datetime.now(timezone.utc).isoformat(),
                error_message=str(e),
            )

    async def write_memory_context(
        self, state: LangGraphOrchestrationState
    ) -> MemoryWriteResult:
        """Write memory context update to memory"""

        try:
            # Extract memory context
            memory_context = state.get("memory_context", {})
            if not memory_context:
                return MemoryWriteResult(
                    success=False,
                    message_id="",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    error_message="No memory context found",
                )

            # Create write request
            request = MemoryWriteRequest(
                session_id=state.get("session_id", ""),
                user_id=state.get("user_id", ""),
                conversation_id=state.get("conversation_id", ""),
                message_type="memory_update",
                content=str(memory_context),
                metadata={
                    "context_type": memory_context.get("type", "unknown"),
                    "context_summary": memory_context.get("context_summary"),
                    "context_timestamp": memory_context.get("timestamp"),
                    "context_metadata": memory_context.get("metadata"),
                },
            )

            # Execute write
            result = await self._execute_write(request, state)

            return result

        except Exception as e:
            logger.error(f"Memory context write error: {e}")
            return MemoryWriteResult(
                success=False,
                message_id="",
                timestamp=datetime.now(timezone.utc).isoformat(),
                error_message=str(e),
            )

    async def _execute_write(
        self, request: MemoryWriteRequest, state: LangGraphOrchestrationState
    ) -> MemoryWriteResult:
        """Execute memory write operation"""

        try:
            # Get context manager
            context_manager = await ensure_context_manager(state)

            # Create message entry
            message_entry = {
                "session_id": request.session_id,
                "user_id": request.user_id,
                "conversation_id": request.conversation_id,
                "message_type": request.message_type,
                "content": request.content,
                "metadata": request.metadata,
                "timestamp": request.timestamp,
            }

            # Write to memory service
            success = await context_manager.memory_service.write_message(message_entry)

            if success:
                return MemoryWriteResult(
                    success=True,
                    message_id=message_entry.get("id", ""),
                    timestamp=request.timestamp,
                    write_type=request.message_type,
                )
            else:
                return MemoryWriteResult(
                    success=False,
                    message_id="",
                    timestamp=request.timestamp,
                    error_message="Memory write failed",
                    write_type=request.message_type,
                )

        except Exception as e:
            logger.error(f"Memory write execution error: {e}")
            return MemoryWriteResult(
                success=False,
                message_id="",
                timestamp=datetime.now(timezone.utc).isoformat(),
                error_message=str(e),
                write_type=request.message_type,
            )

    async def execute_writeback(
        self,
        state: LangGraphOrchestrationState,
        write_types: Optional[List[str]] = None,
    ) -> Dict[str, MemoryWriteResult]:
        """Execute complete memory writeback"""

        logger.info("Executing memory writeback")

        if write_types is None:
            write_types = [
                "user_message",
                "assistant_response",
                "session_state",
                "memory_context",
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
            elif write_type == "memory_context":
                results["memory_context"] = await self.write_memory_context(state)

        # Store results in state
        state["memory_write_results"] = results
        state["memory_writeback_completed"] = True

        # Check for write failures
        failed_writes = [result for result in results.values() if not result.success]

        if failed_writes:
            error_messages = [
                f"{result.write_type} write failed: {result.error_message}"
                for result in failed_writes
            ]
            state.setdefault("errors", []).extend(error_messages)

        logger.info(f"Memory writeback completed: {len(results)} writes attempted")
        return results


async def memory_write_node(
    state: LangGraphOrchestrationState,
) -> LangGraphOrchestrationState:
    """Convenience wrapper for MemoryWriteNode"""
    node = MemoryWriteNode()
    return await node(state)
