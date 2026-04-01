from __future__ import annotations
import logging
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING
from ai_karen_engine.chat.code_execution_service import CodeExecutionRequest, CodeLanguage, SecurityLevel
from ai_karen_engine.chat.tool_integration_service import ToolExecutionContext

if TYPE_CHECKING:
    from ai_karen_engine.chat.ChatOrchestrator.models import ChatRequest, ProcessingContext
    from ai_karen_engine.chat.ChatOrchestrator.base import ChatOrchestratorProtocol
    Base = ChatOrchestratorProtocol
else:
    Base = object

logger = logging.getLogger(__name__)

class ChatToolMixin(Base):
    """Methods for tool and code execution detection and handling."""

    async def _handle_code_execution_request(self, message: str, context: ProcessingContext) -> Optional[str]:
        """Detect and execute code if requested in the message."""
        if not self._is_code_related_message(message) or not self.code_execution_service:
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
                metadata={"correlation_id": context.correlation_id}
            )
            
            response = await self.code_execution_service.execute_code(exec_request)
            
            if response.success and response.result:
                return f"\n\n[Code Execution Result]\nSTDOUT: {response.result.stdout}\nSTDERR: {response.result.stderr}"
            else:
                return f"\n\n[Code Execution Failed]\n{response.message}"
        except Exception as e:
            logger.error(f"Code execution handler failed: {e}")
            return f"\n\n[Code Execution Error]\n{str(e)}"

    async def _handle_tool_execution_request(self, message: str, context: ProcessingContext) -> Optional[str]:
        """Detect and execute integrated tools if requested."""
        if not self.tool_integration_service:
            return None

        # Simple keyword-based tool detection for demonstration
        # In production, this would be handled by an intent classifier or LLM function calling
        available_tools = self.tool_integration_service.get_available_tools()
        for tool in available_tools:
            tool_name = tool["metadata"]["name"]
            if tool_name in message.lower():
                logger.info(f"Detected tool execution request for '{tool_name}': {context.correlation_id}")
                try:
                    # Construct formal ToolExecutionContext
                    tool_context = ToolExecutionContext(
                        user_id=context.user_id,
                        conversation_id=context.conversation_id,
                        metadata={"correlation_id": context.correlation_id}
                    )
                    
                    # Tool parameters would normally be extracted by NLP/LLM
                    parameters = {"content": message} # Default mapping
                    
                    result = await self.tool_integration_service.execute_tool(
                        tool_name=tool_name,
                        parameters=parameters,
                        context=tool_context
                    )
                    
                    if result.success:
                        return f"\n\n[Tool Result: {tool_name}]\n{result.result}"
                    else:
                        return f"\n\n[Tool Failed: {tool_name}]\n{result.error_message}"
                except Exception as e:
                    logger.error(f"Tool execution failed for '{tool_name}': {e}")
                    return f"\n\n[Tool Error: {tool_name}]\n{str(e)}"
        
        return None

    def _is_code_related_message(self, message: str) -> bool:
        """Check if message contains code or code execution intent."""
        # Simple heuristics
        code_markers = ["```", "import ", "def ", "function ", "const ", "let ", "var ", "SELECT ", "print("]
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
        return "python" # Default
