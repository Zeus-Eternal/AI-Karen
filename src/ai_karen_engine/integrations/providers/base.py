"""
Base LLM Provider class with CopilotKit code assistance integration.
"""

from abc import ABC, abstractmethod
import asyncio
from typing import Any, Dict, List, Optional
import logging
import re

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Base class for LLM providers with CopilotKit code assistance capabilities."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = "base"
        self.copilotkit_enabled = config.get("copilotkit_enabled", False)
        self.code_assistance_enabled = config.get("code_assistance_enabled", True)
        self.debugging_assistance_enabled = config.get("debugging_assistance_enabled", True)
        self.documentation_generation_enabled = config.get("documentation_generation_enabled", True)
        
        # Initialize CopilotKit integration if enabled
        self._copilotkit_provider = None
        if self.copilotkit_enabled:
            self._init_copilotkit_integration()
    
    def _init_copilotkit_integration(self):
        """Initialize CopilotKit integration for code assistance."""
        try:
            from ai_karen_engine.integrations.providers.copilotkit_provider import CopilotKitProvider
            
            copilotkit_config = self.config.get("copilotkit_config", {})
            self._copilotkit_provider = CopilotKitProvider(copilotkit_config)
            logger.info(f"CopilotKit integration enabled for {self.provider_name}")
            
        except Exception as e:
            logger.warning(f"Failed to initialize CopilotKit integration for {self.provider_name}: {e}")
            self._copilotkit_provider = None

    def warm_cache(self) -> None:
        """Best-effort cache warmup using a minimal generation request."""
        try:
            asyncio.run(self.generate_response("hello"))
        except Exception as e:  # pragma: no cover - warmup is optional
            logger.debug(f"warm_cache failed for {self.provider_name}: {e}")
    
    def _is_code_related(self, prompt: str) -> bool:
        """Detect if prompt is code-related and should use CopilotKit assistance."""
        code_keywords = [
            'code', 'function', 'class', 'method', 'variable', 'debug', 'error',
            'python', 'javascript', 'typescript', 'java', 'c++', 'rust', 'go',
            'import', 'export', 'def', 'async', 'await', 'return', 'if', 'else',
            'for', 'while', 'try', 'catch', 'exception', 'syntax', 'compile',
            'refactor', 'optimize', 'algorithm', 'data structure', 'api', 'library'
        ]
        
        # Check for code blocks
        if '```' in prompt or '`' in prompt:
            return True
        
        # Check for code-related keywords
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in code_keywords)
    
    def _is_debugging_request(self, prompt: str) -> bool:
        """Detect if prompt is a debugging request."""
        debug_keywords = [
            'debug', 'error', 'exception', 'bug', 'fix', 'issue', 'problem',
            'traceback', 'stack trace', 'crash', 'fail', 'broken', 'not working'
        ]
        
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in debug_keywords)
    
    def _is_documentation_request(self, prompt: str) -> bool:
        """Detect if prompt is a documentation generation request."""
        doc_keywords = [
            'document', 'documentation', 'docstring', 'comment', 'explain',
            'describe', 'what does', 'how does', 'generate docs', 'api docs'
        ]
        
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in doc_keywords)
    
    async def get_code_suggestions(self, code: str, language: str = "python", **kwargs) -> List[Dict[str, Any]]:
        """Get code completion suggestions using CopilotKit if available."""
        if not self.code_assistance_enabled:
            return []
        
        if self._copilotkit_provider:
            try:
                return await self._copilotkit_provider.get_code_completion(
                    code_context=code,
                    language=language,
                    cursor_position=len(code),
                    **kwargs
                )
            except Exception as e:
                logger.warning(f"CopilotKit code suggestions failed: {e}")
        
        # Fallback to basic suggestions
        return await self._fallback_code_suggestions(code, language)
    
    async def get_debugging_assistance(self, code: str, error_message: str = "", language: str = "python", **kwargs) -> Dict[str, Any]:
        """Get debugging assistance using CopilotKit if available."""
        if not self.debugging_assistance_enabled:
            return {"suggestions": [], "analysis": "Debugging assistance disabled"}
        
        if self._copilotkit_provider:
            try:
                return await self._copilotkit_provider.analyze_code(
                    code=code,
                    language=language,
                    analysis_type="debug",
                    error_context=error_message,
                    **kwargs
                )
            except Exception as e:
                logger.warning(f"CopilotKit debugging assistance failed: {e}")
        
        # Fallback to basic debugging assistance
        return await self._fallback_debugging_assistance(code, error_message, language)
    
    async def generate_documentation(self, code: str, language: str = "python", style: str = "comprehensive", **kwargs) -> str:
        """Generate documentation using CopilotKit if available."""
        if not self.documentation_generation_enabled:
            return "Documentation generation disabled"
        
        if self._copilotkit_provider:
            try:
                return await self._copilotkit_provider.generate_documentation(
                    code=code,
                    language=language,
                    style=style,
                    **kwargs
                )
            except Exception as e:
                logger.warning(f"CopilotKit documentation generation failed: {e}")
        
        # Fallback to basic documentation generation
        return await self._fallback_documentation_generation(code, language, style)
    
    async def get_contextual_suggestions(self, message: str, context: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """Get contextual suggestions using CopilotKit if available."""
        if self._copilotkit_provider:
            try:
                return await self._copilotkit_provider.get_contextual_suggestions(
                    context=message,
                    suggestion_type="contextual",
                    **kwargs
                )
            except Exception as e:
                logger.warning(f"CopilotKit contextual suggestions failed: {e}")
        
        # Fallback to basic contextual suggestions
        return await self._fallback_contextual_suggestions(message, context)
    
    async def enhanced_generate_response(self, prompt: str, **kwargs) -> str:
        """Enhanced response generation with CopilotKit assistance."""
        # Check if this is a code-related request
        if self._is_code_related(prompt):
            if self._is_debugging_request(prompt):
                # Extract code from prompt if present
                code_match = re.search(r'```(\w+)?\n(.*?)\n```', prompt, re.DOTALL)
                if code_match:
                    language = code_match.group(1) or "python"
                    code = code_match.group(2)
                    
                    # Get debugging assistance
                    debug_info = await self.get_debugging_assistance(code, prompt, language)
                    
                    # Enhance the original response with debugging insights
                    base_response = await self.generate_response(prompt, **kwargs)
                    
                    if debug_info.get("suggestions"):
                        enhanced_response = f"{base_response}\n\n**Debugging Insights:**\n"
                        for suggestion in debug_info["suggestions"]:
                            enhanced_response += f"- {suggestion}\n"
                        return enhanced_response
                    
                    return base_response
            
            elif self._is_documentation_request(prompt):
                # Extract code from prompt if present
                code_match = re.search(r'```(\w+)?\n(.*?)\n```', prompt, re.DOTALL)
                if code_match:
                    language = code_match.group(1) or "python"
                    code = code_match.group(2)
                    
                    # Generate documentation
                    documentation = await self.generate_documentation(code, language)
                    
                    # Combine with original response
                    base_response = await self.generate_response(prompt, **kwargs)
                    return f"{base_response}\n\n**Generated Documentation:**\n{documentation}"
            
            else:
                # General code assistance
                code_match = re.search(r'```(\w+)?\n(.*?)\n```', prompt, re.DOTALL)
                if code_match:
                    language = code_match.group(1) or "python"
                    code = code_match.group(2)
                    
                    # Get code suggestions
                    suggestions = await self.get_code_suggestions(code, language)
                    
                    # Enhance response with suggestions
                    base_response = await self.generate_response(prompt, **kwargs)
                    
                    if suggestions:
                        enhanced_response = f"{base_response}\n\n**Code Suggestions:**\n"
                        for suggestion in suggestions[:3]:  # Limit to top 3
                            enhanced_response += f"- {suggestion.get('content', 'No content')}\n"
                        return enhanced_response
                    
                    return base_response
        
        # For non-code requests, use regular generation
        return await self.generate_response(prompt, **kwargs)
    
    # Fallback methods for when CopilotKit is not available
    async def _fallback_code_suggestions(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Fallback code suggestions when CopilotKit is unavailable."""
        return [
            {
                "type": "completion",
                "content": f"# Consider adding error handling for {language} code",
                "confidence": 0.6,
                "reasoning": "Basic fallback suggestion"
            }
        ]
    
    async def _fallback_debugging_assistance(self, code: str, error_message: str, language: str) -> Dict[str, Any]:
        """Fallback debugging assistance when CopilotKit is unavailable."""
        suggestions = []
        
        if "import" in error_message.lower() or "module" in error_message.lower():
            suggestions.append("Check if all required modules are installed")
        if "syntax" in error_message.lower():
            suggestions.append("Review code syntax for common errors")
        if "indentation" in error_message.lower():
            suggestions.append("Check code indentation consistency")
        
        return {
            "suggestions": suggestions or ["Review code logic and error context"],
            "analysis": "Basic debugging analysis (CopilotKit unavailable)",
            "confidence": 0.5
        }
    
    async def _fallback_documentation_generation(self, code: str, language: str, style: str) -> str:
        """Fallback documentation generation when CopilotKit is unavailable."""
        return f"""# {language.title()} Code Documentation

This code requires documentation. CopilotKit is currently unavailable for advanced documentation generation.

## Basic Analysis
- Language: {language}
- Style: {style}
- Lines of code: {len(code.split(chr(10)))}

Please add appropriate docstrings and comments manually."""
    
    async def _fallback_contextual_suggestions(self, message: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback contextual suggestions when CopilotKit is unavailable."""
        return [
            {
                "type": "suggestion",
                "content": "CopilotKit is currently unavailable for advanced contextual suggestions",
                "confidence": 0.5,
                "reasoning": "Fallback response"
            }
        ]
    
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response from the LLM."""
        pass
    
    @abstractmethod
    async def stream_response(self, prompt: str, **kwargs):
        """Stream response from the LLM."""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get available models."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get provider status."""
        pass
    
    async def get_enhanced_status(self) -> Dict[str, Any]:
        """Get enhanced provider status including CopilotKit integration."""
        base_status = await self.get_status()
        
        enhanced_status = {
            **base_status,
            "copilotkit_integration": {
                "enabled": self.copilotkit_enabled,
                "available": self._copilotkit_provider is not None,
                "features": {
                    "code_assistance": self.code_assistance_enabled,
                    "debugging_assistance": self.debugging_assistance_enabled,
                    "documentation_generation": self.documentation_generation_enabled
                }
            }
        }
        
        return enhanced_status
    
    async def generate_completion(self, prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> str:
        """Generate completion with specific parameters."""
        return await self.generate_response(
            prompt, 
            max_tokens=max_tokens, 
            temperature=temperature
        )