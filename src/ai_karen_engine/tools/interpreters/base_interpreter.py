from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class InterpreterError(Exception):
    """Exception raised when code execution encounters resolvable errors"""
    pass

class BaseInterpreter(ABC):
    """Abstract base class for code interpreters in AI-Karen system"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logger

    @abstractmethod
    async def run(self, code: str, code_type: str) -> str:
        """
        Executes the given code based on its type.

        Args:
            code: The code to be executed
            code_type: The type of the code, must be one of supported_code_types()

        Returns:
            The result of the code execution. If execution fails, includes
            sufficient information to diagnose and correct the issue.

        Raises:
            InterpreterError: If code execution encounters errors that
                could be resolved by modifying or regenerating the code.
        """
        pass

    @abstractmethod
    def supported_code_types(self) -> List[str]:
        """Returns list of supported code types by the interpreter"""
        pass

    @abstractmethod
    def update_action_space(self, action_space: Dict[str, Any]) -> None:
        """Updates action space for interpreter capabilities"""
        pass

    def validate_code_type(self, code_type: str) -> bool:
        """Validate if code type is supported"""
        return code_type in self.supported_code_types()

    async def cleanup(self) -> None:
        """Cleanup resources used by interpreter"""
        pass
