"""
ChatOrchestrator with spaCy and DistilBERT integration.

This module implements the core chat orchestrator that coordinates message processing
with NLP services, retry logic, error handling, and context management.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Union

from ai_karen_engine.chat.ChatOrchestrator import (
    ChatRequest,
    ChatResponse,
    ChatStreamChunk,
    ProcessingContext,
    ProcessingStatus,
    ErrorType,
    RetryConfig,
    ChatCoreMixin,
    ChatLLMMixin,
    ChatPromptMixin,
    ChatMemoryMixin,
    ChatToolMixin,
    ChatUtilityMixin,
    ChatAgentMixin,
)
from ai_karen_engine.chat.ChatOrchestrator.router import FallbackRouter

from ai_karen_engine.chat.memory_processor import MemoryProcessor
from ai_karen_engine.chat.file_attachment_service import FileAttachmentService
from ai_karen_engine.chat.multimedia_service import MultimediaService
from ai_karen_engine.chat.code_execution_service import CodeExecutionService
from ai_karen_engine.chat.tool_integration_service import ToolIntegrationService
from ai_karen_engine.chat.instruction_processor import InstructionProcessor
from ai_karen_engine.chat.context_integrator import ContextIntegrator
from ai_karen_engine.chat.response_formatter import PrettyOutputLayer
from ai_karen_engine.services.response_formatting_engine import (
    ResponseFormattingEngine,
    FormattingContext,
    DisplayContext,
    AccessibilityLevel,
)
from ai_karen_engine.services.response_policy_enforcer import ResponsePolicyEnforcer

logger = logging.getLogger(__name__)

class ChatOrchestrator(
    ChatUtilityMixin,
    ChatCoreMixin,
    ChatLLMMixin,
    ChatAgentMixin,
    ChatPromptMixin,
    ChatMemoryMixin,
    ChatToolMixin
):
    """
    Production-ready chat orchestrator with modular architecture.
    
    Inherits logic from specialized Mixins to maintain a clean separation of concerns:
    - ChatCoreMixin: Main processing loops and flow control.
    - ChatLLMMixin: LLM routing, trials, and fallback logic.
    - ChatPromptMixin: Persona and context-aware prompt building.
    - ChatMemoryMixin: Transactional memory writeback orchestration.
    - ChatToolMixin: Code and tool execution handling.
    - ChatUtilityMixin: General helper methods.
    """
    
    def __init__(
        self,
        memory_processor: Optional[MemoryProcessor] = None,
        file_attachment_service: Optional[FileAttachmentService] = None,
        multimedia_service: Optional[MultimediaService] = None,
        code_execution_service: Optional[CodeExecutionService] = None,
        tool_integration_service: Optional[ToolIntegrationService] = None,
        instruction_processor: Optional[InstructionProcessor] = None,
        context_integrator: Optional[ContextIntegrator] = None,
        conversation_manager: Optional[Any] = None,
        session_state_manager: Optional[Any] = None,
        retry_config: Optional[RetryConfig] = None,
        timeout_seconds: float = 30.0,
        enable_monitoring: bool = True,
        auth_service: Optional[Any] = None
    ):
        # Service registrations
        self.memory_processor = memory_processor
        self.file_attachment_service = file_attachment_service
        self.multimedia_service = multimedia_service
        self.code_execution_service = code_execution_service
        self.tool_integration_service = tool_integration_service
        self.instruction_processor = instruction_processor or InstructionProcessor()
        self.context_integrator = context_integrator or ContextIntegrator()
        self.conversation_manager = conversation_manager
        self.session_state_manager = session_state_manager
        self.auth_service = auth_service
        self.output_layer = PrettyOutputLayer()
        self.formatting_engine = ResponseFormattingEngine()
        self.response_policy_enforcer = ResponsePolicyEnforcer()
        
        # Configuration
        self.retry_config = retry_config or RetryConfig()
        self.timeout_seconds = timeout_seconds
        self.enable_monitoring = enable_monitoring
        self._hook_timeout_seconds = float(os.getenv("KARI_CHAT_HOOK_TIMEOUT_SECONDS", "2.0"))
        
        # Internal state
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._retry_attempts = 0
        self._fallback_usage = 0
        self._processing_times: List[float] = []
        
        self._active_contexts: Dict[str, ProcessingContext] = {}
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._contexts_lock = asyncio.Lock()
        self._tasks_lock = asyncio.Lock()
        
        # Governance
        self.fallback_router = FallbackRouter()
        
        logger.info("ChatOrchestrator initialized with modular Mixin architecture.")

    def _build_formatting_context(
        self,
        turn_context: Any,
        *,
        content_length: int = 0,
    ) -> FormattingContext:
        """Build formatting context from request/session preferences."""
        user_prefs: Dict[str, Any] = {}
        metadata: Dict[str, Any] = {}

        if turn_context is not None:
            metadata = getattr(turn_context, "metadata", {}) or {}
            user_ctx = getattr(turn_context, "user_ctx", None)
            if isinstance(user_ctx, dict):
                user_prefs = dict(user_ctx.get("formatting_preferences", {}) or {})

        if not user_prefs and isinstance(metadata.get("formatting_preferences"), dict):
            user_prefs = dict(metadata.get("formatting_preferences") or {})

        display_context_value = str(
            user_prefs.get("display_context")
            or metadata.get("display_context")
            or "desktop"
        ).strip()
        accessibility_value = str(
            user_prefs.get("accessibility_level")
            or metadata.get("accessibility_level")
            or "basic"
        ).strip()
        technical_level = str(
            user_prefs.get("technical_level")
            or metadata.get("technical_level")
            or "intermediate"
        ).strip()
        language = str(
            user_prefs.get("language") or metadata.get("language") or "en"
        ).strip()

        try:
            display_context = DisplayContext(display_context_value)
        except ValueError:
            display_context = DisplayContext.DESKTOP

        try:
            accessibility_level = AccessibilityLevel(accessibility_value)
        except ValueError:
            accessibility_level = AccessibilityLevel.BASIC

        return FormattingContext(
            display_context=display_context,
            accessibility_level=accessibility_level,
            user_preferences=user_prefs,
            content_length=content_length,
            technical_level=technical_level or "intermediate",
            language=language or "en",
        )

# Export aliases for backward compatibility if needed
__all__ = ["ChatOrchestrator", "ChatRequest", "ChatResponse", "ChatStreamChunk"]
