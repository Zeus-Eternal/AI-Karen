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
        self.auth_service = auth_service
        self.output_layer = PrettyOutputLayer()
        
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

# Export aliases for backward compatibility if needed
__all__ = ["ChatOrchestrator", "ChatRequest", "ChatResponse", "ChatStreamChunk"]
