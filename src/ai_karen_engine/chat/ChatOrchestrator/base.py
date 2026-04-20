from __future__ import annotations
import asyncio
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    Union,
    AsyncGenerator,
    AsyncIterator,
)

from ai_karen_engine.chat.memory_processor import MemoryProcessor
from ai_karen_engine.chat.file_attachment_service import FileAttachmentService
from ai_karen_engine.chat.multimedia_service import MultimediaService
from ai_karen_engine.chat.code_execution_service import CodeExecutionService
from ai_karen_engine.chat.tool_integration_service import ToolIntegrationService
from ai_karen_engine.chat.instruction_processor import InstructionProcessor
from ai_karen_engine.chat.context_integrator import ContextIntegrator
from ai_karen_engine.chat.response_formatter import PrettyOutputLayer
from .router import FallbackRouter
from .models import (
    ChatRequest,
    ChatResponse,
    ChatStreamChunk,
    ProcessingContext,
    ProcessingResult,
    RetryConfig,
)
from ai_karen_engine.models.shared_types import ChatMessage


class ChatOrchestratorProtocol(Protocol):
    """
    Defines the interface for the ChatOrchestrator, ensuring type safety across mixins.
    """

    # Services
    memory_processor: Optional[MemoryProcessor]
    file_attachment_service: Optional[FileAttachmentService]
    multimedia_service: Optional[MultimediaService]
    code_execution_service: Optional[CodeExecutionService]
    tool_integration_service: Optional[ToolIntegrationService]
    instruction_processor: InstructionProcessor
    context_integrator: ContextIntegrator
    conversation_manager: Optional[Any]
    session_state_manager: Optional[Any]
    auth_service: Optional[Any]
    output_layer: PrettyOutputLayer
    fallback_router: FallbackRouter

    # Configuration
    retry_config: RetryConfig
    timeout_seconds: float
    enable_monitoring: bool
    _hook_timeout_seconds: float

    # Internal state
    _total_requests: int
    _successful_requests: int
    _failed_requests: int
    _retry_attempts: int
    _fallback_usage: int
    _processing_times: List[float]
    _active_contexts: Dict[str, ProcessingContext]
    _active_tasks: Dict[str, asyncio.Task]
    _contexts_lock: asyncio.Lock
    _tasks_lock: asyncio.Lock

    # Core Methods
    async def handle_chat(self, request: ChatRequest) -> ChatResponse: ...

    async def handle_chat_stream(
        self, request: ChatRequest
    ) -> AsyncGenerator[ChatStreamChunk, None]: ...

    async def process_message(
        self, request: ChatRequest
    ) -> Union[ChatResponse, AsyncGenerator[ChatStreamChunk, None]]: ...

    async def _persist_user_message(self, request: ChatRequest) -> Dict[str, Any]: ...

    async def _resolve_conversation_state(
        self, request: ChatRequest, user_message_record: Dict[str, Any]
    ) -> Dict[str, Any]: ...

    async def _build_working_context(
        self, request: ChatRequest, conversation_state: Dict[str, Any]
    ) -> Dict[str, Any]: ...

    async def _select_execution_path(
        self, request: ChatRequest, working_context: Dict[str, Any]
    ) -> str: ...

    async def _execute_generation(
        self,
        request: ChatRequest,
        working_context: Dict[str, Any],
        execution_path: str,
    ) -> ChatResponse: ...

    async def _finalize_response(
        self,
        request: ChatRequest,
        generation_result: ChatResponse,
        execution_path: str,
        working_context: Dict[str, Any],
        user_message_record: Dict[str, Any],
    ) -> ChatResponse: ...

    async def _persist_assistant_message(
        self, request: ChatRequest, response: ChatResponse
    ) -> ChatResponse: ...

    async def _post_response_writeback(
        self,
        request: ChatRequest,
        response: ChatResponse,
        working_context: Dict[str, Any],
    ) -> None: ...

    async def _emit_chat_telemetry(
        self,
        request: ChatRequest,
        response: ChatResponse,
        working_context: Dict[str, Any],
    ) -> None: ...

    async def _process_traditional(
        self, request: ChatRequest, context: ProcessingContext
    ) -> ChatResponse: ...

    def _process_streaming(
        self, request: ChatRequest, context: ProcessingContext
    ) -> AsyncGenerator[ChatStreamChunk, None]: ...

    async def _process_with_retry(
        self, request: ChatRequest, context: ProcessingContext, stream: bool = False
    ) -> Union[ProcessingResult, AsyncIterator[str]]: ...

    async def _process_message_core(
        self, request: ChatRequest, context: ProcessingContext, stream: bool = False
    ) -> Union[ProcessingResult, AsyncIterator[str]]: ...

    async def _process_message_internal(
        self, request: ChatRequest, context: ProcessingContext, stream: bool = False
    ) -> Union[ProcessingResult, AsyncIterator[str]]: ...

    async def _retrieve_context(
        self,
        embeddings: List[float],
        parsed_message: Any,
        user_id: str,
        conversation_id: str,
    ) -> Dict[str, Any]: ...

    # Prompt Methods (from ChatPromptMixin)
    async def _get_persona_system_prompt(self, context: ProcessingContext) -> str: ...

    async def _build_chat_messages(
        self, context: ProcessingContext
    ) -> List[ChatMessage]: ...

    async def _build_enhanced_prompt(self, context: ProcessingContext) -> str: ...

    # LLM Implementation Methods (from ChatLLMMixin)
    async def _try_user_chosen_llm(
        self,
        request: ChatRequest,
        context: ProcessingContext,
        persona_prompt: str,
        message_history: List[ChatMessage],
        stream: bool = False,
    ) -> tuple[
        Optional[Union[ProcessingResult, AsyncIterator[str]]], Optional[str]
    ]: ...

    async def _try_system_default_llms(
        self,
        request: ChatRequest,
        context: ProcessingContext,
        persona_prompt: str,
        message_history: List[ChatMessage],
        stream: bool = False,
        initial_failure_reason: Optional[str] = None,
    ) -> Union[ProcessingResult, AsyncIterator[str]]: ...

    # LLM Methods (Entry Points)
    async def _generate_ai_response_enhanced(
        self,
        message: str,
        parsed_message: Any,
        embeddings: Optional[List[float]],
        integrated_context: Optional[Any],
        active_instructions: List[Any],
        context: ProcessingContext,
        stream: bool = False,
    ) -> Union[tuple[str, dict[str, Any], bool], AsyncIterator[str]]: ...

    # Memory Methods
    async def _orchestrate_post_response_memory_writeback(
        self, request: ChatRequest, context: ProcessingContext, result: ProcessingResult
    ) -> Dict[str, Any]: ...

    # Utility Methods
    async def _trigger_hooks_with_timeout(
        self,
        hook_manager: Any,
        hook_context: Any,
    ) -> Any: ...

    def _get_model_display_name(self, model_id: Optional[str]) -> Optional[str]: ...

    # Agentic Methods
    async def _orchestrate_agentic_workflow(
        self, request: ChatRequest, context: ProcessingContext
    ) -> Optional[ProcessingResult]: ...

    # State Management
    async def _register_context(self, context: ProcessingContext) -> None: ...

    async def _register_task(self, correlation_id: str, task: asyncio.Task) -> None: ...

    async def _cleanup_context(self, correlation_id: str) -> None: ...
