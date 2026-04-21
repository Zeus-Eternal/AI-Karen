"""
Code Execution Service Compatibility Layer.

This module provides a simplified compatibility layer for code execution functionality
that was previously in the chat directory. Since the original services were removed during
demolition, this provides basic functionality with warnings.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CodeLanguage(str, Enum):
    """Supported programming languages."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    RUST = "rust"
    GO = "go"
    SHELL = "shell"
    SQL = "sql"
    JSON = "json"


class SecurityLevel(str, Enum):
    """Security levels for code execution."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    STRICT = "strict"


@dataclass
class CodeExecutionRequest:
    """Code execution request."""

    code: str
    language: CodeLanguage
    security_level: SecurityLevel
    timeout: int = 30
    context: Optional[Dict[str, Any]] = None


@dataclass
class CodeExecutionResponse:
    """Code execution response."""

    execution_id: str
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    memory_usage: int = 0
    status: str = "completed"
    metadata: Optional[Dict[str, Any]] = None


class CodeExecutionService:
    """Simplified code execution service for compatibility."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.warning(
            "Using compatibility CodeExecutionService - full functionality not available"
        )

    async def execute_code(
        self, request: CodeExecutionRequest
    ) -> CodeExecutionResponse:
        """Execute code (simplified implementation)."""
        execution_id = str(uuid.uuid4())

        # Simulate code execution
        self.logger.info(f"Executing {request.language} code: {request.code[:100]}...")

        # Basic safety check
        if "import os" in request.code.lower() or "subprocess" in request.code.lower():
            return CodeExecutionResponse(
                execution_id=execution_id,
                output="",
                error="Code execution blocked for security reasons",
                status="failed",
                metadata={"security_blocked": True},
            )

        # Simulate execution
        output = f"Code executed successfully (simulated)\nLanguage: {request.language}\nCode length: {len(request.code)} characters"

        return CodeExecutionResponse(
            execution_id=execution_id,
            output=output,
            execution_time=0.1,
            status="completed",
        )

    async def get_supported_languages(self) -> List[CodeLanguage]:
        """Get supported languages."""
        return [lang for lang in CodeLanguage]

    async def validate_code(self, code: str, language: CodeLanguage) -> Dict[str, Any]:
        """Validate code (simplified implementation)."""
        return {"valid": True, "warnings": [], "errors": []}


# Global service instance
_service: Optional[CodeExecutionService] = None


def get_code_execution_service() -> CodeExecutionService:
    """Get the code execution service instance."""
    global _service
    if _service is None:
        _service = CodeExecutionService()
    return _service


# Tool integration service compatibility
@dataclass
class ToolExecutionContext:
    """Tool execution context."""

    tool_name: str
    parameters: Dict[str, Any]
    user_id: str
    session_id: Optional[str] = None


@dataclass
class ToolExecutionResult:
    """Tool execution result."""

    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class ToolIntegrationService:
    """Simplified tool integration service for compatibility."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.warning(
            "Using compatibility ToolIntegrationService - full functionality not available"
        )

    async def execute_tool(self, context: ToolExecutionContext) -> ToolExecutionResult:
        """Execute a tool (simplified implementation)."""
        self.logger.info(f"Executing tool: {context.tool_name}")

        # Simulate tool execution
        if context.tool_name == "weather":
            output = {"temperature": 72, "condition": "sunny"}
        elif context.tool_name == "calculator":
            # Simple calculator simulation
            try:
                result = eval(context.parameters.get("expression", "0"))
                output = {"result": result}
            except:
                output = {"error": "Invalid expression"}
        else:
            output = {
                "message": f"Tool {context.tool_name} not available in compatibility mode"
            }

        return ToolExecutionResult(success=True, output=output, execution_time=0.1)

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        return [
            {"name": "weather", "description": "Get weather information"},
            {"name": "calculator", "description": "Simple calculator"},
            {
                "name": "search",
                "description": "Web search (not available in compatibility mode)",
            },
        ]


# Global service instance
_tool_service: Optional[ToolIntegrationService] = None


def get_tool_integration_service() -> ToolIntegrationService:
    """Get the tool integration service instance."""
    global _tool_service
    if _tool_service is None:
        _tool_service = ToolIntegrationService()
    return _tool_service
