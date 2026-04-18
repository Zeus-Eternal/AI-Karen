"""Dependency providers for chat-related services."""

from functools import lru_cache
from typing import Any, Optional

from ai_karen_engine.chat.code_execution_service import CodeExecutionService
from ai_karen_engine.chat.tool_integration_service import ToolIntegrationService
from ai_karen_engine.chat.memory_processor import MemoryProcessor
from ai_karen_engine.memory.memory_service import WebUIMemoryService


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
def get_memory_service() -> Optional[WebUIMemoryService]:
    """Provide the authoritative shared memory service for chat routes."""
    try:
        from ai_karen_engine.chat.factory import get_chat_service_factory

        factory = get_chat_service_factory()
        return factory.get_service("memory_service") or factory.create_memory_service()
    except Exception:
        return None


@lru_cache()
def get_production_memory() -> Optional[Any]:
    """Backward-compatible alias for the production memory service."""
    return get_memory_service()


def get_chat_orchestrator_dependency():
    """FastAPI dependency for ChatOrchestrator."""
    from ai_karen_engine.chat.factory import get_chat_orchestrator
    return get_chat_orchestrator()


