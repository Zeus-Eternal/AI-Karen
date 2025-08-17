"""
CopilotKit Error Handler with LLM Provider Fallback Integration

This module provides specialized error handling for CopilotKit integration,
including fallback to existing LLM providers and graceful degradation.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
from enum import Enum

from ai_karen_engine.llm_orchestrator import get_orchestrator

logger = logging.getLogger(__name__)


class CopilotKitErrorType(Enum):
    """Specific CopilotKit error types."""
    
    API_UNAVAILABLE = "api_unavailable"
    AUTHENTICATION_FAILED = "authentication_failed"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    CONTEXT_TOO_LARGE = "context_too_large"
    MODEL_UNAVAILABLE = "model_unavailable"
    TIMEOUT = "timeout"
    INVALID_REQUEST = "invalid_request"
    QUOTA_EXCEEDED = "quota_exceeded"
    NETWORK_ERROR = "network_error"


class CopilotKitFallbackHandler:
    """Handles CopilotKit errors with intelligent fallback strategies."""
    
    def __init__(self):
        self.llm_orchestrator = get_orchestrator()
        self.fallback_cache: Dict[str, Dict[str, Any]] = {}
        self.error_counts: Dict[str, int] = {}
        self.last_error_time: Dict[str, float] = {}
    
    async def handle_code_suggestions_error(
        self, 
        error: Exception, 
        code: str, 
        language: str = "python",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Handle code suggestions error with fallback to LLM providers."""
        error_type = self._classify_error(error)
        
        logger.warning(f"CopilotKit code suggestions failed ({error_type}): {error}")
        
        try:
            # Try fallback using LLM orchestrator
            fallback_suggestions = await self._get_code_suggestions_fallback(
                code, language, error_type, **kwargs
            )
            
            if fallback_suggestions:
                return fallback_suggestions
            
            # If fallback fails, return cached suggestions if available
            cache_key = f"code_suggestions_{hash(code)}_{language}"
            if cache_key in self.fallback_cache:
                cached = self.fallback_cache[cache_key]
                logger.info("Using cached code suggestions")
                return cached["suggestions"]
            
            # Return generic fallback suggestions
            return self._create_generic_code_suggestions(code, language)
            
        except Exception as fallback_error:
            logger.error(f"Code suggestions fallback failed: {fallback_error}")
            return self._create_generic_code_suggestions(code, language)
    
    async def handle_debugging_assistance_error(
        self,
        error: Exception,
        code: str,
        error_message: str = "",
        language: str = "python",
        **kwargs
    ) -> Dict[str, Any]:
        """Handle debugging assistance error with fallback."""
        error_type = self._classify_error(error)
        
        logger.warning(f"CopilotKit debugging assistance failed ({error_type}): {error}")
        
        try:
            # Try fallback using LLM orchestrator
            fallback_assistance = await self._get_debugging_assistance_fallback(
                code, error_message, language, error_type, **kwargs
            )
            
            if fallback_assistance:
                return fallback_assistance
            
            # Return cached assistance if available
            cache_key = f"debug_assistance_{hash(code + error_message)}_{language}"
            if cache_key in self.fallback_cache:
                cached = self.fallback_cache[cache_key]
                logger.info("Using cached debugging assistance")
                return cached["assistance"]
            
            # Return generic fallback assistance
            return self._create_generic_debugging_assistance(code, error_message, language)
            
        except Exception as fallback_error:
            logger.error(f"Debugging assistance fallback failed: {fallback_error}")
            return self._create_generic_debugging_assistance(code, error_message, language)
    
    async def handle_contextual_suggestions_error(
        self,
        error: Exception,
        message: str,
        context: Dict[str, Any],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Handle contextual suggestions error with fallback."""
        error_type = self._classify_error(error)
        
        logger.warning(f"CopilotKit contextual suggestions failed ({error_type}): {error}")
        
        try:
            # Try fallback using LLM orchestrator
            fallback_suggestions = await self._get_contextual_suggestions_fallback(
                message, context, error_type, **kwargs
            )
            
            if fallback_suggestions:
                return fallback_suggestions
            
            # Return cached suggestions if available
            cache_key = f"contextual_suggestions_{hash(message)}_{hash(str(context))}"
            if cache_key in self.fallback_cache:
                cached = self.fallback_cache[cache_key]
                logger.info("Using cached contextual suggestions")
                return cached["suggestions"]
            
            # Return generic fallback suggestions
            return self._create_generic_contextual_suggestions(message, context)
            
        except Exception as fallback_error:
            logger.error(f"Contextual suggestions fallback failed: {fallback_error}")
            return self._create_generic_contextual_suggestions(message, context)
    
    async def handle_documentation_generation_error(
        self,
        error: Exception,
        code: str,
        language: str = "python",
        style: str = "comprehensive",
        **kwargs
    ) -> str:
        """Handle documentation generation error with fallback."""
        error_type = self._classify_error(error)
        
        logger.warning(f"CopilotKit documentation generation failed ({error_type}): {error}")
        
        try:
            # Try fallback using LLM orchestrator
            fallback_docs = await self._get_documentation_generation_fallback(
                code, language, style, error_type, **kwargs
            )
            
            if fallback_docs:
                return fallback_docs
            
            # Return cached documentation if available
            cache_key = f"documentation_{hash(code)}_{language}_{style}"
            if cache_key in self.fallback_cache:
                cached = self.fallback_cache[cache_key]
                logger.info("Using cached documentation")
                return cached["documentation"]
            
            # Return generic fallback documentation
            return self._create_generic_documentation(code, language, style)
            
        except Exception as fallback_error:
            logger.error(f"Documentation generation fallback failed: {fallback_error}")
            return self._create_generic_documentation(code, language, style)
    
    def _classify_error(self, error: Exception) -> CopilotKitErrorType:
        """Classify CopilotKit error by type."""
        error_msg = str(error).lower()
        
        if "unavailable" in error_msg or "connection" in error_msg:
            return CopilotKitErrorType.API_UNAVAILABLE
        elif "authentication" in error_msg or "unauthorized" in error_msg:
            return CopilotKitErrorType.AUTHENTICATION_FAILED
        elif "rate limit" in error_msg or "429" in error_msg:
            return CopilotKitErrorType.RATE_LIMIT_EXCEEDED
        elif "context" in error_msg and ("large" in error_msg or "size" in error_msg):
            return CopilotKitErrorType.CONTEXT_TOO_LARGE
        elif "model" in error_msg and "unavailable" in error_msg:
            return CopilotKitErrorType.MODEL_UNAVAILABLE
        elif "timeout" in error_msg:
            return CopilotKitErrorType.TIMEOUT
        elif "quota" in error_msg or "limit" in error_msg:
            return CopilotKitErrorType.QUOTA_EXCEEDED
        elif "network" in error_msg or "connection" in error_msg:
            return CopilotKitErrorType.NETWORK_ERROR
        else:
            return CopilotKitErrorType.INVALID_REQUEST
    
    async def _get_code_suggestions_fallback(
        self,
        code: str,
        language: str,
        error_type: CopilotKitErrorType,
        **kwargs
    ) -> Optional[List[Dict[str, Any]]]:
        """Get code suggestions using LLM orchestrator fallback."""
        try:
            # Create prompt for code suggestions
            prompt = self._create_code_suggestions_prompt(code, language)
            
            # Use LLM orchestrator with timeout
            response = await asyncio.wait_for(
                self.llm_orchestrator.enhanced_route(prompt, skill="code_assistance", **kwargs),
                timeout=30.0
            )
            
            # Parse response into suggestions format
            suggestions = self._parse_code_suggestions_response(response, language)
            
            # Cache successful response
            cache_key = f"code_suggestions_{hash(code)}_{language}"
            self.fallback_cache[cache_key] = {
                "suggestions": suggestions,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "llm_fallback"
            }
            
            return suggestions
            
        except Exception as e:
            logger.error(f"LLM fallback for code suggestions failed: {e}")
            return None
    
    async def _get_debugging_assistance_fallback(
        self,
        code: str,
        error_message: str,
        language: str,
        error_type: CopilotKitErrorType,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Get debugging assistance using LLM orchestrator fallback."""
        try:
            # Create prompt for debugging assistance
            prompt = self._create_debugging_prompt(code, error_message, language)
            
            # Use LLM orchestrator with timeout
            response = await asyncio.wait_for(
                self.llm_orchestrator.enhanced_route(prompt, skill="debugging", **kwargs),
                timeout=45.0
            )
            
            # Parse response into assistance format
            assistance = self._parse_debugging_response(response, language)
            
            # Cache successful response
            cache_key = f"debug_assistance_{hash(code + error_message)}_{language}"
            self.fallback_cache[cache_key] = {
                "assistance": assistance,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "llm_fallback"
            }
            
            return assistance
            
        except Exception as e:
            logger.error(f"LLM fallback for debugging assistance failed: {e}")
            return None
    
    async def _get_contextual_suggestions_fallback(
        self,
        message: str,
        context: Dict[str, Any],
        error_type: CopilotKitErrorType,
        **kwargs
    ) -> Optional[List[Dict[str, Any]]]:
        """Get contextual suggestions using LLM orchestrator fallback."""
        try:
            # Create prompt for contextual suggestions
            prompt = self._create_contextual_suggestions_prompt(message, context)
            
            # Use LLM orchestrator with timeout
            response = await asyncio.wait_for(
                self.llm_orchestrator.enhanced_route(prompt, skill="conversation", **kwargs),
                timeout=30.0
            )
            
            # Parse response into suggestions format
            suggestions = self._parse_contextual_suggestions_response(response)
            
            # Cache successful response
            cache_key = f"contextual_suggestions_{hash(message)}_{hash(str(context))}"
            self.fallback_cache[cache_key] = {
                "suggestions": suggestions,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "llm_fallback"
            }
            
            return suggestions
            
        except Exception as e:
            logger.error(f"LLM fallback for contextual suggestions failed: {e}")
            return None
    
    async def _get_documentation_generation_fallback(
        self,
        code: str,
        language: str,
        style: str,
        error_type: CopilotKitErrorType,
        **kwargs
    ) -> Optional[str]:
        """Get documentation generation using LLM orchestrator fallback."""
        try:
            # Create prompt for documentation generation
            prompt = self._create_documentation_prompt(code, language, style)
            
            # Use LLM orchestrator with timeout
            response = await asyncio.wait_for(
                self.llm_orchestrator.enhanced_route(prompt, skill="documentation", **kwargs),
                timeout=60.0
            )
            
            # Cache successful response
            cache_key = f"documentation_{hash(code)}_{language}_{style}"
            self.fallback_cache[cache_key] = {
                "documentation": response,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "llm_fallback"
            }
            
            return response
            
        except Exception as e:
            logger.error(f"LLM fallback for documentation generation failed: {e}")
            return None
    
    def _create_code_suggestions_prompt(self, code: str, language: str) -> str:
        """Create prompt for code suggestions."""
        return f"""
Please analyze the following {language} code and provide helpful suggestions for improvement, completion, or fixes:

```{language}
{code}
```

Provide suggestions in the following areas:
1. Code completion if the code appears incomplete
2. Bug fixes if there are obvious issues
3. Performance improvements
4. Best practices and style improvements
5. Security considerations if applicable

Format your response as a list of specific, actionable suggestions.
"""
    
    def _create_debugging_prompt(self, code: str, error_message: str, language: str) -> str:
        """Create prompt for debugging assistance."""
        return f"""
Please help debug the following {language} code that is producing an error:

Code:
```{language}
{code}
```

Error message:
{error_message}

Please provide:
1. Analysis of what's causing the error
2. Step-by-step explanation of the issue
3. Specific fix recommendations
4. Corrected code if applicable
5. Tips to prevent similar issues in the future

Be specific and practical in your debugging assistance.
"""
    
    def _create_contextual_suggestions_prompt(self, message: str, context: Dict[str, Any]) -> str:
        """Create prompt for contextual suggestions."""
        context_str = "\n".join([f"- {k}: {v}" for k, v in context.items() if isinstance(v, (str, int, float, bool))])
        
        return f"""
Based on the user's message and the current context, provide helpful suggestions for what they might want to do next.

User message: "{message}"

Current context:
{context_str}

Provide 3-5 contextual suggestions that would be helpful given this message and context. 
Each suggestion should be:
1. Relevant to the current conversation
2. Actionable
3. Helpful for the user's workflow

Format as a simple list of suggestions.
"""
    
    def _create_documentation_prompt(self, code: str, language: str, style: str) -> str:
        """Create prompt for documentation generation."""
        return f"""
Please generate {style} documentation for the following {language} code:

```{language}
{code}
```

The documentation should include:
1. Overview of what the code does
2. Parameters and their types/descriptions
3. Return values and their types/descriptions
4. Usage examples
5. Any important notes or considerations

Format the documentation appropriately for {language} (e.g., docstrings for Python, JSDoc for JavaScript, etc.).
Make it {style} and professional.
"""
    
    def _parse_code_suggestions_response(self, response: str, language: str) -> List[Dict[str, Any]]:
        """Parse LLM response into code suggestions format."""
        suggestions = []
        lines = response.strip().split('\n')
        
        current_suggestion = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for numbered items or bullet points
            if line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '*')):
                if current_suggestion:
                    suggestions.append(current_suggestion)
                
                # Clean up the line
                clean_line = line
                for prefix in ['1.', '2.', '3.', '4.', '5.', '-', '*']:
                    if clean_line.startswith(prefix):
                        clean_line = clean_line[len(prefix):].strip()
                        break
                
                current_suggestion = {
                    "id": f"suggestion_{len(suggestions) + 1}",
                    "type": "improvement",
                    "content": clean_line,
                    "confidence": 0.8,
                    "language": language,
                    "source": "llm_fallback"
                }
            elif current_suggestion:
                # Continue previous suggestion
                current_suggestion["content"] += " " + line
        
        # Add the last suggestion
        if current_suggestion:
            suggestions.append(current_suggestion)
        
        # If no structured suggestions found, create a general one
        if not suggestions:
            suggestions.append({
                "id": "suggestion_1",
                "type": "general",
                "content": response[:200] + "..." if len(response) > 200 else response,
                "confidence": 0.6,
                "language": language,
                "source": "llm_fallback"
            })
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _parse_debugging_response(self, response: str, language: str) -> Dict[str, Any]:
        """Parse LLM response into debugging assistance format."""
        return {
            "analysis": response,
            "suggestions": [
                {
                    "type": "debug_help",
                    "content": "Review the analysis above for debugging guidance",
                    "confidence": 0.7
                }
            ],
            "source": "llm_fallback",
            "language": language
        }
    
    def _parse_contextual_suggestions_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into contextual suggestions format."""
        suggestions = []
        lines = response.strip().split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Clean up numbered items or bullet points
            for prefix in ['1.', '2.', '3.', '4.', '5.', '-', '*']:
                if line.startswith(prefix):
                    line = line[len(prefix):].strip()
                    break
            
            if line:
                suggestions.append({
                    "id": f"contextual_{i + 1}",
                    "type": "contextual",
                    "content": line,
                    "confidence": 0.7,
                    "source": "llm_fallback"
                })
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _create_generic_code_suggestions(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Create generic code suggestions when all else fails."""
        return [
            {
                "id": "generic_1",
                "type": "general",
                "content": f"Consider reviewing your {language} code for potential improvements",
                "confidence": 0.3,
                "language": language,
                "source": "generic_fallback"
            },
            {
                "id": "generic_2", 
                "type": "general",
                "content": "Check for proper error handling and edge cases",
                "confidence": 0.3,
                "language": language,
                "source": "generic_fallback"
            }
        ]
    
    def _create_generic_debugging_assistance(self, code: str, error_message: str, language: str) -> Dict[str, Any]:
        """Create generic debugging assistance when all else fails."""
        return {
            "analysis": f"Unable to provide specific debugging assistance for this {language} code. Please check the error message and review your code logic.",
            "suggestions": [
                {
                    "type": "general",
                    "content": "Review the error message carefully for clues",
                    "confidence": 0.3
                },
                {
                    "type": "general", 
                    "content": "Check for common issues like syntax errors, undefined variables, or type mismatches",
                    "confidence": 0.3
                }
            ],
            "source": "generic_fallback",
            "language": language
        }
    
    def _create_generic_contextual_suggestions(self, message: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create generic contextual suggestions when all else fails."""
        return [
            {
                "id": "generic_contextual_1",
                "type": "general",
                "content": "Try rephrasing your question for better assistance",
                "confidence": 0.3,
                "source": "generic_fallback"
            },
            {
                "id": "generic_contextual_2",
                "type": "general", 
                "content": "Consider providing more context about what you're trying to achieve",
                "confidence": 0.3,
                "source": "generic_fallback"
            }
        ]
    
    def _create_generic_documentation(self, code: str, language: str, style: str) -> str:
        """Create generic documentation when all else fails."""
        return f"""
# Documentation

Unable to generate specific documentation for this {language} code.

## General Guidelines:
- Review the code structure and functionality
- Add appropriate comments and docstrings
- Document parameters, return values, and usage examples
- Consider the {style} documentation style for your project

Please try again later or provide more specific requirements.
"""


# Global instance
_copilotkit_fallback_handler: Optional[CopilotKitFallbackHandler] = None


def get_copilotkit_fallback_handler() -> CopilotKitFallbackHandler:
    """Get the global CopilotKit fallback handler instance."""
    global _copilotkit_fallback_handler
    if _copilotkit_fallback_handler is None:
        _copilotkit_fallback_handler = CopilotKitFallbackHandler()
    return _copilotkit_fallback_handler


__all__ = [
    "CopilotKitFallbackHandler",
    "CopilotKitErrorType",
    "get_copilotkit_fallback_handler"
]