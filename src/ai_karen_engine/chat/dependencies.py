"""Dependency providers for chat-related services."""

from functools import lru_cache

from ai_karen_engine.chat.code_execution_service import CodeExecutionService
from ai_karen_engine.chat.tool_integration_service import ToolIntegrationService


@lru_cache()
def get_code_execution_service() -> CodeExecutionService:
    """Provide a singleton instance of CodeExecutionService."""
    return CodeExecutionService()


@lru_cache()
def get_tool_integration_service() -> ToolIntegrationService:
    """Provide a singleton instance of ToolIntegrationService."""
    return ToolIntegrationService()

