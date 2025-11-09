"""
CopilotKit Debug Assistant Plugin

Provides AI-powered debugging assistance using CopilotKit integration with Karen's
existing plugin orchestration patterns. Supports code analysis, error debugging,
performance optimization, and code review capabilities.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import re

from ai_karen_engine.llm_orchestrator import get_orchestrator
from ai_karen_engine.hooks.hook_mixin import HookMixin
from ai_karen_engine.hooks.hook_types import HookTypes

logger = logging.getLogger(__name__)


class CopilotKitDebugAssistant(HookMixin):
    """CopilotKit-powered debugging assistant with hook integration."""
    
    def __init__(self):
        super().__init__()
        self.name = "copilotkit_debug_assistant"
        self.orchestrator = get_orchestrator()
        self.supported_languages = [
            "python", "javascript", "typescript", "java", "c++", "rust", "go"
        ]
        
        # Register plugin hooks
        asyncio.create_task(self._register_debug_hooks())
    
    async def _register_debug_hooks(self):
        """Register debugging-specific hooks."""
        try:
            # Pre-execution validation hook
            await self.register_hook(
                "validate_code_input",
                self._validate_code_input,
                priority=10,
                source_name="debug_assistant_validation"
            )
            
            # Post-execution result storage hook
            await self.register_hook(
                "store_debug_results",
                self._store_debug_results,
                priority=90,
                source_name="debug_assistant_storage"
            )
            
            # Error handling fallback hook
            await self.register_hook(
                "fallback_debug_analysis",
                self._fallback_debug_analysis,
                priority=95,
                source_name="debug_assistant_fallback"
            )
            
            logger.info("CopilotKit debug assistant hooks registered successfully")
            
        except Exception as e:
            logger.warning(f"Failed to register debug assistant hooks: {e}")
    
    async def _validate_code_input(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate code input before debugging analysis."""
        code = context.get("code", "")
        language = context.get("language", "python")
        
        validation_result = {
            "valid": True,
            "warnings": [],
            "suggestions": []
        }
        
        # Basic validation checks
        if not code.strip():
            validation_result["valid"] = False
            validation_result["warnings"].append("No code provided for analysis")
            return validation_result
        
        if language not in self.supported_languages:
            validation_result["warnings"].append(f"Language '{language}' may have limited support")
            validation_result["suggestions"].append(f"Supported languages: {', '.join(self.supported_languages)}")
        
        # Check for potentially sensitive information
        sensitive_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]
        
        for pattern in sensitive_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                validation_result["warnings"].append("Code may contain sensitive information")
                validation_result["suggestions"].append("Consider removing or masking sensitive data before analysis")
                break
        
        return validation_result
    
    async def _store_debug_results(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Store debugging results for future reference."""
        try:
            debug_results = context.get("debug_results", {})
            code = context.get("code", "")
            language = context.get("language", "python")
            
            # Create a summary for storage
            storage_data = {
                "timestamp": context.get("timestamp"),
                "language": language,
                "code_length": len(code),
                "issues_found": len(debug_results.get("issues", [])),
                "suggestions_provided": len(debug_results.get("suggestions", [])),
                "analysis_type": debug_results.get("analysis_type", "comprehensive"),
                "confidence": debug_results.get("confidence", 0.0)
            }
            
            # Store in user context for memory system
            if "debug_history" not in user_context:
                user_context["debug_history"] = []
            
            user_context["debug_history"].append(storage_data)
            
            # Keep only last 10 debug sessions
            if len(user_context["debug_history"]) > 10:
                user_context["debug_history"] = user_context["debug_history"][-10:]
            
            return {
                "stored": True,
                "storage_summary": storage_data
            }
            
        except Exception as e:
            logger.error(f"Failed to store debug results: {e}")
            return {"stored": False, "error": str(e)}
    
    async def _fallback_debug_analysis(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide fallback debugging analysis when CopilotKit is unavailable."""
        code = context.get("code", "")
        language = context.get("language", "python")
        error_message = context.get("error_message", "")
        
        # Basic static analysis
        fallback_analysis = {
            "analysis_type": "fallback",
            "issues": [],
            "suggestions": [],
            "confidence": 0.6,
            "provider": "fallback_analyzer"
        }
        
        # Language-specific basic checks
        if language == "python":
            fallback_analysis.update(await self._python_fallback_analysis(code, error_message))
        elif language in ["javascript", "typescript"]:
            fallback_analysis.update(await self._javascript_fallback_analysis(code, error_message))
        else:
            fallback_analysis["suggestions"].append(f"Basic analysis for {language} - consider using a specialized linter")
        
        return fallback_analysis
    
    async def _python_fallback_analysis(self, code: str, error_message: str) -> Dict[str, Any]:
        """Basic Python code analysis."""
        issues = []
        suggestions = []
        
        # Check for common Python issues
        if "IndentationError" in error_message:
            issues.append("Indentation error detected")
            suggestions.append("Check for consistent use of spaces or tabs")
        
        if "ImportError" in error_message or "ModuleNotFoundError" in error_message:
            issues.append("Import error detected")
            suggestions.append("Verify that all required modules are installed")
        
        if "SyntaxError" in error_message:
            issues.append("Syntax error detected")
            suggestions.append("Check for missing colons, parentheses, or quotes")
        
        # Basic code pattern checks
        if "print(" not in code and "logging" not in code:
            suggestions.append("Consider adding logging or print statements for debugging")
        
        if "try:" not in code and "except" not in code:
            suggestions.append("Consider adding error handling with try/except blocks")
        
        return {"issues": issues, "suggestions": suggestions}
    
    async def _javascript_fallback_analysis(self, code: str, error_message: str) -> Dict[str, Any]:
        """Basic JavaScript/TypeScript code analysis."""
        issues = []
        suggestions = []
        
        # Check for common JavaScript issues
        if "ReferenceError" in error_message:
            issues.append("Reference error detected")
            suggestions.append("Check for undefined variables or functions")
        
        if "TypeError" in error_message:
            issues.append("Type error detected")
            suggestions.append("Verify object properties and method calls")
        
        if "SyntaxError" in error_message:
            issues.append("Syntax error detected")
            suggestions.append("Check for missing semicolons, brackets, or quotes")
        
        # Basic code pattern checks
        if "console.log" not in code:
            suggestions.append("Consider adding console.log statements for debugging")
        
        if "try {" not in code and "catch" not in code:
            suggestions.append("Consider adding error handling with try/catch blocks")
        
        return {"issues": issues, "suggestions": suggestions}


async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for CopilotKit debug assistant plugin.
    
    Args:
        params: Plugin parameters containing:
            - code: Code to analyze
            - language: Programming language (default: python)
            - error_message: Optional error message for context
            - analysis_type: Type of analysis (debug, review, optimize)
            - user_context: User context for personalization
    
    Returns:
        Dictionary containing debugging analysis results
    """
    try:
        # Initialize debug assistant
        debug_assistant = CopilotKitDebugAssistant()
        
        # Extract parameters
        code = params.get("code", "")
        language = params.get("language", "python")
        error_message = params.get("error_message", "")
        analysis_type = params.get("analysis_type", "debug")
        user_context = params.get("user_context", {})
        
        # Validate input
        validation_context = {
            "code": code,
            "language": language,
            "analysis_type": analysis_type
        }
        
        validation_result = await debug_assistant.trigger_hook_safe(
            "validate_code_input",
            validation_context,
            user_context
        )
        
        if not validation_result.get("valid", True):
            return {
                "success": False,
                "error": "Input validation failed",
                "validation_warnings": validation_result.get("warnings", []),
                "suggestions": validation_result.get("suggestions", [])
            }
        
        # Get LLM orchestrator for CopilotKit integration
        orchestrator = get_orchestrator()
        
        # Perform debugging analysis based on type
        if analysis_type == "debug":
            debug_results = await orchestrator.get_debugging_assistance(
                code=code,
                error_message=error_message,
                language=language
            )
        elif analysis_type == "review":
            # Use code suggestions for review
            suggestions = await orchestrator.get_code_suggestions(
                code=code,
                language=language
            )
            debug_results = {
                "analysis_type": "review",
                "suggestions": [s.get("content", "") for s in suggestions],
                "issues": [],
                "confidence": 0.8
            }
        elif analysis_type == "optimize":
            # Generate optimization suggestions
            optimization_prompt = f"Optimize this {language} code for better performance:\n\n```{language}\n{code}\n```"
            optimization_response = await orchestrator.enhanced_route(optimization_prompt)
            debug_results = {
                "analysis_type": "optimization",
                "suggestions": [optimization_response],
                "issues": [],
                "confidence": 0.7
            }
        else:
            # Comprehensive analysis
            debug_results = await orchestrator.get_debugging_assistance(
                code=code,
                error_message=error_message,
                language=language
            )
        
        # Store results
        storage_context = {
            "debug_results": debug_results,
            "code": code,
            "language": language,
            "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
                "debug_assistant", 20, __file__, 0, "", (), None
            )) if logger.handlers else None
        }
        
        storage_result = await debug_assistant.trigger_hook_safe(
            "store_debug_results",
            storage_context,
            user_context
        )
        
        # Prepare response
        response = {
            "success": True,
            "analysis_type": analysis_type,
            "language": language,
            "debug_results": debug_results,
            "validation_warnings": validation_result.get("warnings", []),
            "storage_info": storage_result,
            "provider": "copilotkit_debug_assistant",
            "plugin_version": "1.0.0"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"CopilotKit debug assistant failed: {e}")
        
        # Try fallback analysis
        try:
            debug_assistant = CopilotKitDebugAssistant()
            fallback_context = {
                "code": params.get("code", ""),
                "language": params.get("language", "python"),
                "error_message": params.get("error_message", "")
            }
            
            fallback_result = await debug_assistant.trigger_hook_safe(
                "fallback_debug_analysis",
                fallback_context,
                params.get("user_context", {})
            )
            
            return {
                "success": True,
                "analysis_type": "fallback",
                "language": params.get("language", "python"),
                "debug_results": fallback_result,
                "provider": "fallback_analyzer",
                "warning": "CopilotKit unavailable, using fallback analysis"
            }
            
        except Exception as fallback_error:
            logger.error(f"Fallback analysis also failed: {fallback_error}")
            return {
                "success": False,
                "error": str(e),
                "fallback_error": str(fallback_error),
                "provider": "copilotkit_debug_assistant"
            }


# Plugin metadata for discovery
__plugin_info__ = {
    "name": "copilotkit-debug-assistant",
    "version": "1.0.0",
    "description": "CopilotKit-powered debugging assistance",
    "capabilities": ["code_analysis", "error_debugging", "performance_optimization", "code_review"],
    "supported_languages": ["python", "javascript", "typescript", "java", "c++", "rust", "go"]
}