from __future__ import annotations
import logging
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING
from ai_karen_engine.chat.code_execution_service import (
    CodeExecutionRequest,
    CodeLanguage,
    SecurityLevel,
)
from ai_karen_engine.chat.tool_integration_service import ToolExecutionContext

if TYPE_CHECKING:
    from ai_karen_engine.chat.ChatOrchestrator.models import (
        ChatRequest,
        ProcessingContext,
    )
    from ai_karen_engine.chat.ChatOrchestrator.base import ChatOrchestratorProtocol

    Base = ChatOrchestratorProtocol
else:
    Base = object

logger = logging.getLogger(__name__)


class ChatToolMixin(Base):
    """Methods for tool and code execution detection and handling."""

    async def _handle_code_execution_request(
        self, message: str, context: ProcessingContext
    ) -> Optional[str]:
        """Detect and execute code if requested in the message."""
        if (
            not self._is_code_related_message(message)
            or not self.code_execution_service
        ):
            return None

        logger.info(f"Detected code execution request: {context.correlation_id}")
        try:
            language = self._detect_programming_language(message)

            # Construct formal CodeExecutionRequest
            exec_request = CodeExecutionRequest(
                code=message,
                language=CodeLanguage(language),
                user_id=context.user_id,
                conversation_id=context.conversation_id,
                security_level=SecurityLevel.STRICT,
                metadata={"correlation_id": context.correlation_id},
            )

            response = await self.code_execution_service.execute_code(exec_request)

            if response.success and response.result:
                return f"\n\n[Code Execution Result]\nSTDOUT: {response.result.stdout}\nSTDERR: {response.result.stderr}"
            else:
                return f"\n\n[Code Execution Failed]\n{response.message}"
        except Exception as e:
            logger.error(f"Code execution handler failed: {e}")
            return f"\n\n[Code Execution Error]\n{str(e)}"

    async def _handle_tool_execution_request(
        self, message: str, context: ProcessingContext
    ) -> Optional[str]:
        """Detect and execute integrated tools if requested."""
        if not self.tool_integration_service:
            return None

        # Enhanced tool detection with better parameter extraction
        available_tools = self.tool_integration_service.get_available_tools()

        # Check for weather-related queries
        weather_keywords = [
            "weather",
            "temperature",
            "forecast",
            "rain",
            "sunny",
            "cloudy",
            "humidity",
            "wind",
        ]
        if any(keyword in message.lower() for keyword in weather_keywords):
            logger.info(f"Detected weather tool request: {context.correlation_id}")
            try:
                # Extract location from message
                location = self._extract_location_from_message(message)
                if not location:
                    location = "default"  # Could use user's default location

                # Construct formal ToolExecutionContext
                tool_context = ToolExecutionContext(
                    user_id=context.user_id,
                    conversation_id=context.conversation_id,
                    metadata={"correlation_id": context.correlation_id},
                )

                # Weather tool parameters
                parameters = {
                    "location": location,
                    "units": "metric",  # Could be determined from user preferences
                }

                result = await self.tool_integration_service.execute_tool(
                    tool_name="weather", parameters=parameters, context=tool_context
                )

                if result.success:
                    return f"\n\n[Weather Result]\n{result.result}"
                else:
                    return f"\n\n[Weather Error]\n{result.error_message}"
            except Exception as e:
                logger.error(f"Weather tool execution failed: {e}")
                return f"\n\n[Weather Error]\n{str(e)}"

        # Fallback to general tool detection for other tools
        for tool in available_tools:
            tool_name = tool["metadata"]["name"]
            if (
                tool_name in message.lower() and tool_name != "weather"
            ):  # Skip weather since we handled it
                logger.info(
                    f"Detected tool execution request for '{tool_name}': {context.correlation_id}"
                )
                try:
                    # Construct formal ToolExecutionContext
                    tool_context = ToolExecutionContext(
                        user_id=context.user_id,
                        conversation_id=context.conversation_id,
                        metadata={"correlation_id": context.correlation_id},
                    )

                    # Tool parameters would normally be extracted by NLP/LLM
                    parameters = {"content": message}  # Default mapping

                    result = await self.tool_integration_service.execute_tool(
                        tool_name=tool_name, parameters=parameters, context=tool_context
                    )

                    if result.success:
                        return f"\n\n[Tool Result: {tool_name}]\n{result.result}"
                    else:
                        return f"\n\n[Tool Failed: {tool_name}]\n{result.error_message}"
                except Exception as e:
                    logger.error(f"Tool execution failed for '{tool_name}': {e}")
                    return f"\n\n[Tool Error: {tool_name}]\n{str(e)}"

        return None

    def _extract_location_from_message(self, message: str) -> Optional[str]:
        """Extract location from a weather query message."""
        import re

        # Common location patterns
        patterns = [
            r"in\s+([A-Za-z\s,]+)",  # "in London"
            r"for\s+([A-Za-z\s,]+)",  # "for Paris"
            r"(\w+)(?:,\s*\w+)*",  # "New York" or "London, UK"
            r"([A-Za-z\s]+)\s+(?:weather|temperature)",  # "London weather"
        ]

        message_lower = message.lower()

        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                location = match.group(1).strip()
                # Clean up common artifacts
                location = re.sub(
                    r"\b(weather|temperature|forecast)\b", "", location
                ).strip()
                if location:
                    return location

        # Check for common city names in the message
        common_cities = [
            "london",
            "paris",
            "new york",
            "tokyo",
            "berlin",
            "madrid",
            "rome",
            "amsterdam",
            "sydney",
            "moscow",
            "beijing",
            "mumbai",
            "cairo",
            "toronto",
        ]

        for city in common_cities:
            if city in message_lower:
                return city.title()

        return None

    def _is_code_related_message(self, message: str) -> bool:
        """Check if message contains code or code execution intent."""
        # Simple heuristics
        code_markers = [
            "```",
            "import ",
            "def ",
            "function ",
            "const ",
            "let ",
            "var ",
            "SELECT ",
            "print(",
        ]
        return any(marker in message for marker in code_markers)

    def _detect_programming_language(self, message: str) -> str:
        """Heuristically detect the programming language."""
        if "```python" in message or "import " in message or "def " in message:
            return "python"
        if "```javascript" in message or "const " in message or "let " in message:
            return "javascript"
        if "```sql" in message or "SELECT " in message:
            return "sql"
        if "```bash" in message or "ls -l" in message:
            return "bash"
        return "python"  # Default
