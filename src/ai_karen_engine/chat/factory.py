"""
Production Chat Service Factory
Comprehensive factory for initializing and wiring all chat-related services.
"""

import logging
from typing import Optional

from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator, RetryConfig
from ai_karen_engine.chat.memory_processor import MemoryProcessor
from ai_karen_engine.chat.file_attachment_service import FileAttachmentService
from ai_karen_engine.chat.multimedia_service import MultimediaService
from ai_karen_engine.chat.code_execution_service import CodeExecutionService
from ai_karen_engine.chat.tool_integration_service import ToolIntegrationService
from ai_karen_engine.chat.instruction_processor import InstructionProcessor
from ai_karen_engine.chat.context_integrator import ContextIntegrator
from ai_karen_engine.chat.stream_processor import AsyncStreamProcessor as StreamProcessor
from ai_karen_engine.chat.websocket_gateway import WebSocketGateway
from ai_karen_engine.database.client import MultiTenantPostgresClient
from ai_karen_engine.database.conversation_manager import ConversationManager
from ai_karen_engine.core.memory.session_state_manager import SessionStateManager
from ai_karen_engine.clients.factory import get_redis_client
from services.memory.memory_service import WebUIMemoryService

logger = logging.getLogger(__name__)


class ChatServiceConfig:
    """Configuration for chat services."""

    def __init__(
        self,
        enable_memory: bool = True,
        enable_file_attachments: bool = True,
        enable_multimedia: bool = True,
        enable_code_execution: bool = True,
        enable_tool_integration: bool = True,
        enable_websocket: bool = True,
        retry_max_attempts: int = 3,
        retry_backoff_factor: float = 2.0,
        timeout_seconds: float = 300.0,
        enable_monitoring: bool = True,
    ):
        self.enable_memory = enable_memory
        self.enable_file_attachments = enable_file_attachments
        self.enable_multimedia = enable_multimedia
        self.enable_code_execution = enable_code_execution
        self.enable_tool_integration = enable_tool_integration
        self.enable_websocket = enable_websocket
        self.retry_max_attempts = retry_max_attempts
        self.retry_backoff_factor = retry_backoff_factor
        self.timeout_seconds = timeout_seconds
        self.enable_monitoring = enable_monitoring


class ChatServiceFactory:
    """
    Factory for creating and wiring chat services.

    This factory ensures all chat services are properly initialized,
    configured, and wired together for production use.
    """

    def __init__(self, config: Optional[ChatServiceConfig] = None):
        self.config = config or ChatServiceConfig()
        self._services = {}
        logger.info("ChatServiceFactory initialized")

    def create_memory_processor(self) -> Optional[MemoryProcessor]:
        """Create and configure memory processor."""
        if not self.config.enable_memory:
            logger.info("Memory processor disabled by configuration")
            return None

        try:
            from services.memory.nlp_service_manager import nlp_service_manager
            memory_service = self.get_service("memory_service") or self.create_memory_service()
            memory_manager = getattr(memory_service, "base_manager", None) if memory_service else None

            if memory_manager is None:
                logger.warning("Memory manager unavailable - chat memory processor will be disabled")
                return None

            spacy_service = getattr(nlp_service_manager, "spacy_service", None)
            distilbert_service = getattr(nlp_service_manager, "distilbert_service", None)
            if spacy_service is None or distilbert_service is None:
                logger.warning("NLP services unavailable - chat memory processor will be disabled")
                return None

            # Create memory processor
            memory_processor = MemoryProcessor(
                spacy_service=spacy_service,
                distilbert_service=distilbert_service,
                memory_manager=memory_manager,
            )

            self._services['memory_processor'] = memory_processor

            logger.info("Memory processor created successfully")
            return memory_processor

        except Exception as e:
            logger.error(f"Failed to create memory processor: {e}")
            return None

    def create_memory_service(self) -> Optional[WebUIMemoryService]:
        """Create and cache the authoritative chat memory service."""
        if not self.config.enable_memory:
            logger.info("Memory service disabled by configuration")
            return None

        try:
            service = WebUIMemoryService()
            self._services["memory_service"] = service
            logger.info("Memory service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create memory service: {e}")
            return None

    def create_file_attachment_service(self) -> Optional[FileAttachmentService]:
        """Create and configure file attachment service."""
        if not self.config.enable_file_attachments:
            logger.info("File attachment service disabled by configuration")
            return None

        try:
            service = FileAttachmentService()
            self._services['file_attachment_service'] = service
            logger.info("File attachment service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create file attachment service: {e}")
            return None

    def create_multimedia_service(self) -> Optional[MultimediaService]:
        """Create and configure multimedia service."""
        if not self.config.enable_multimedia:
            logger.info("Multimedia service disabled by configuration")
            return None

        try:
            service = MultimediaService()
            self._services['multimedia_service'] = service
            logger.info("Multimedia service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create multimedia service: {e}")
            return None

    def create_code_execution_service(self) -> Optional[CodeExecutionService]:
        """Create and configure code execution service."""
        if not self.config.enable_code_execution:
            logger.info("Code execution service disabled by configuration")
            return None

        try:
            service = CodeExecutionService()
            self._services['code_execution_service'] = service
            logger.info("Code execution service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create code execution service: {e}")
            return None

    def create_tool_integration_service(self) -> Optional[ToolIntegrationService]:
        """Create and configure tool integration service."""
        if not self.config.enable_tool_integration:
            logger.info("Tool integration service disabled by configuration")
            return None

        try:
            service = ToolIntegrationService()
            self._services['tool_integration_service'] = service
            logger.info("Tool integration service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create tool integration service: {e}")
            return None

    def create_instruction_processor(self) -> InstructionProcessor:
        """Create and configure instruction processor."""
        try:
            processor = InstructionProcessor()
            self._services['instruction_processor'] = processor
            logger.info("Instruction processor created successfully")
            return processor
        except Exception as e:
            logger.error(f"Failed to create instruction processor: {e}")
            # Return default instance as fallback
            return InstructionProcessor()

    def create_context_integrator(self) -> ContextIntegrator:
        """Create and configure context integrator."""
        try:
            integrator = ContextIntegrator()
            self._services['context_integrator'] = integrator
            logger.info("Context integrator created successfully")
            return integrator
        except Exception as e:
            logger.error(f"Failed to create context integrator: {e}")
            # Return default instance as fallback
            return ContextIntegrator()

    def create_conversation_manager(self) -> Optional[ConversationManager]:
        """Create and configure the authoritative conversation manager."""
        try:
            db_client = MultiTenantPostgresClient()
            manager = ConversationManager(db_client)
            self._services['conversation_manager'] = manager
            logger.info("Enhanced conversation manager created successfully")
            return manager
        except Exception as e:
            logger.error(f"Failed to create conversation manager: {e}")
            return None

    def create_session_state_manager(self) -> Optional[SessionStateManager]:
        """Create and configure the Redis-backed session continuity manager."""
        try:
            redis_client = get_redis_client()
            manager = SessionStateManager(redis_client=redis_client)
            self._services["session_state_manager"] = manager
            logger.info("Session state manager created successfully")
            return manager
        except Exception as e:
            logger.error(f"Failed to create session state manager: {e}")
            return None

    def create_chat_orchestrator(self) -> ChatOrchestrator:
        """
        Create and configure chat orchestrator with all services wired.

        Returns:
            Fully configured ChatOrchestrator instance
        """
        logger.info("Creating chat orchestrator with all services")

        # Create all dependent services
        memory_processor = self.create_memory_processor()
        file_attachment_service = self.create_file_attachment_service()
        multimedia_service = self.create_multimedia_service()
        code_execution_service = self.create_code_execution_service()
        tool_integration_service = self.create_tool_integration_service()
        instruction_processor = self.create_instruction_processor()
        context_integrator = self.create_context_integrator()
        session_state_manager = self.create_session_state_manager()

        # Create retry configuration
        retry_config = RetryConfig(
            max_attempts=self.config.retry_max_attempts,
            backoff_factor=self.config.retry_backoff_factor,
            exponential_backoff=True
        )

        # Get auth service
        from ai_karen_engine.auth.auth_service import get_auth_service
        import asyncio
        
        try:
            # Check if we have a running loop
            loop = asyncio.get_running_loop()
            auth_service = loop.run_until_complete(get_auth_service()) if not loop.is_running() else None
            # If loop is running, we might need a different approach, 
            # but for factory initialization it's usually fine or we just use the getter inside orchestrator.
            # Actually, the orchestrator can call the getter itself if it's async.
        except RuntimeError:
            from ai_karen_engine.auth.auth_service import get_auth_service_sync
            auth_service = get_auth_service_sync()

        # Create orchestrator with all services
        orchestrator = ChatOrchestrator(
            memory_processor=memory_processor,
            file_attachment_service=file_attachment_service,
            multimedia_service=multimedia_service,
            code_execution_service=code_execution_service,
            tool_integration_service=tool_integration_service,
            instruction_processor=instruction_processor,
            context_integrator=context_integrator,
            conversation_manager=self.create_conversation_manager(),
            session_state_manager=session_state_manager,
            retry_config=retry_config,
            timeout_seconds=self.config.timeout_seconds,
            enable_monitoring=self.config.enable_monitoring,
            auth_service=auth_service
        )

        self._services['chat_orchestrator'] = orchestrator

        logger.info("Chat orchestrator created successfully with all services wired")
        return orchestrator


    def create_stream_processor(self) -> StreamProcessor:
        """Create and configure stream processor."""
        try:
            processor = StreamProcessor()
            self._services['stream_processor'] = processor
            logger.info("Stream processor created successfully")
            return processor
        except Exception as e:
            logger.error(f"Failed to create stream processor: {e}")
            return StreamProcessor()

    def create_websocket_gateway(self) -> Optional[WebSocketGateway]:
        """Create and configure WebSocket gateway."""
        if not self.config.enable_websocket:
            logger.info("WebSocket gateway disabled by configuration")
            return None

        try:
            # Get orchestrator for WebSocket gateway
            orchestrator = self.get_service('chat_orchestrator')
            if not orchestrator:
                orchestrator = self.create_chat_orchestrator()

            gateway = WebSocketGateway(chat_orchestrator=orchestrator)
            self._services['websocket_gateway'] = gateway
            logger.info("WebSocket gateway created successfully")
            return gateway

        except Exception as e:
            logger.error(f"Failed to create WebSocket gateway: {e}")
            return None

    def create_all_services(self):
        """
        Create all chat services and wire them together.

        This is the main entry point for full chat system initialization.
        """
        logger.info("Creating all chat services")

        # Create services in dependency order
        self.create_chat_orchestrator()
        self.create_stream_processor()
        self.create_websocket_gateway()

        logger.info(f"All chat services created: {list(self._services.keys())}")
        return self._services

    def get_service(self, service_name: str):
        """Get a service by name."""
        return self._services.get(service_name)

    def get_all_services(self):
        """Get all created services."""
        return self._services.copy()


# Global factory instance
_global_factory: Optional[ChatServiceFactory] = None


def get_chat_service_factory(config: Optional[ChatServiceConfig] = None) -> ChatServiceFactory:
    """
    Get or create global chat service factory.

    Args:
        config: Optional configuration for the factory

    Returns:
        ChatServiceFactory instance
    """
    global _global_factory

    if _global_factory is None:
        _global_factory = ChatServiceFactory(config)
        logger.info("Global chat service factory created")

    return _global_factory


def get_chat_orchestrator() -> ChatOrchestrator:
    """
    Get or create global chat orchestrator.

    Returns:
        ChatOrchestrator instance
    """
    factory = get_chat_service_factory()
    orchestrator = factory.get_service('chat_orchestrator')

    if orchestrator is None:
        orchestrator = factory.create_chat_orchestrator()

    return orchestrator




__all__ = [
    'ChatServiceConfig',
    'ChatServiceFactory',
    'get_chat_service_factory',
    'get_chat_orchestrator',
]
