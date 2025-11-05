"""Dependency providers for chat-related services."""

from functools import lru_cache
from typing import Optional

from ai_karen_engine.chat.code_execution_service import CodeExecutionService
from ai_karen_engine.chat.tool_integration_service import ToolIntegrationService
from ai_karen_engine.chat.memory_processor import MemoryProcessor
from ai_karen_engine.chat.production_memory import ProductionChatMemory


@lru_cache()
def get_code_execution_service() -> CodeExecutionService:
    """Provide a singleton instance of CodeExecutionService."""
    return CodeExecutionService()


@lru_cache()
def get_tool_integration_service() -> ToolIntegrationService:
    """Provide a singleton instance of ToolIntegrationService."""
    return ToolIntegrationService()


@lru_cache()
def get_memory_processor() -> Optional[MemoryProcessor]:
    """Provide a singleton instance of MemoryProcessor."""
    try:
        from ai_karen_engine.chat.factory import get_chat_service_factory
        factory = get_chat_service_factory()
        return factory.get_service('memory_processor') or factory.create_memory_processor()
    except Exception:
        return None


@lru_cache()
def get_production_memory() -> Optional[ProductionChatMemory]:
    """Provide a singleton instance of ProductionChatMemory."""
    try:
        return ProductionChatMemory()
    except Exception:
        return None


def get_chat_orchestrator_dependency():
    """FastAPI dependency for ChatOrchestrator."""
    from ai_karen_engine.chat.factory import get_chat_orchestrator
    return get_chat_orchestrator()


def get_chat_hub_dependency():
    """FastAPI dependency for ChatHub."""
    from ai_karen_engine.chat.factory import get_chat_hub
    return get_chat_hub()

