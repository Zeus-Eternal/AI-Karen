"""
Tests for CopilotKit Debug Assistant Plugin

Tests the CopilotKit debug assistant plugin functionality including
code analysis, error debugging, and hook integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

# Import the plugin handler
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "plugin_marketplace" / "ai" / "copilotkit-debug-assistant"))

from handler import run, CopilotKitDebugAssistant


class TestCopilotKitDebugAssistant:
    """Test CopilotKit debug assistant functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.debug_assistant = CopilotKitDebugAssistant()
    
    @pytest.mark.asyncio
    async def test_validate_code_input_valid(self):
        """Test code input validation with valid input."""
        context = {
            "code": "def hello():\n    print('Hello, World!')",
            "language": "python",
            "analysis_type": "debug"
        }
        user_context = {}
        
        result = await self.debug_assistant._validate_code_input(context, user_context)
        
        assert result["valid"] is True
        assert len(result["warnings"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_code_input_empty_code(self):
        """Test code input validation with empty code."""
        context = {
            "code": "",
            "language": "python",
            "analysis_type": "debug"
        }
        user_context = {}
        
        result = await self.debug_assistant._validate_code_input(context, user_context)
        
        assert result["valid"] is False
        assert "No code provided for analysis" in result["warnings"]
    
    @pytest.mark.asyncio
    async def test_validate_code_input_unsupported_language(self):
        """Test code input validation with unsupported language."""
        context = {
            "code": "print('hello')",
            "language": "cobol",
            "analysis_type": "debug"
        }
        user_context = {}
        
        result = await self.debug_assistant._validate_code_input(context, user_context)
        
        assert result["valid"] is True  # Still valid, just warning
        assert any("may have limited support" in warning for warning in result["warnings"])
    
    @pytest.mark.asyncio
    async def test_validate_code_input_sensitive_data(self):
        """Test code input validation with sensitive data."""
        context = {
            "code": "password = 'secret123'\napi_key = 'abc123'",
            "language": "python",
            "analysis_type": "debug"
        }
        user_context = {}
        
        result = await self.debug_assistant._validate_code_input(context, user_context)
        
        assert result["valid"] is True
        assert any("sensitive information" in warning for warning in result["warnings"])
        assert any("masking sensitive data" in suggestion for suggestion in result["suggestions"])
    
    @pytest.mark.asyncio
    async def test_store_debug_results(self):
        """Test storing debug results."""
        context = {
            "debug_results": {
                "issues": ["Issue 1", "Issue 2"],
                "suggestions": ["Suggestion 1"],
                "analysis_type": "comprehensive",
                "confidence": 0.8
            },
            "code": "def test(): pass",
            "language": "python",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        user_context = {}
        
        result = await self.debug_assistant._store_debug_results(context, user_context)
        
        assert result["stored"] is True
        assert "storage_summary" in result
        
        # Check that debug history was added to user context
        assert "debug_history" in user_context
        assert len(user_context["debug_history"]) == 1
        
        stored_data = user_context["debug_history"][0]
        assert stored_data["language"] == "python"
        assert stored_data["issues_found"] == 2
        assert stored_data["suggestions_provided"] == 1
    
    @pytest.mark.asyncio
    async def test_python_fallback_analysis(self):
        """Test Python fallback analysis."""
        code = """
import unknown_module
try:
    print(x)
except:
    pass
"""
        error_message = "IndentationError: expected an indented block"
        
        result = await self.debug_assistant._python_fallback_analysis(code, error_message)
        
        assert "issues" in result
        assert "suggestions" in result
        assert any("Indentation error detected" in issue for issue in result["issues"])
        assert any("consistent use of spaces or tabs" in suggestion for suggestion in result["suggestions"])
    
    @pytest.mark.asyncio
    async def test_javascript_fallback_analysis(self):
        """Test JavaScript fallback analysis."""
        code = """
function test() {
    console.log(x);
}
"""
        error_message = "ReferenceError: x is not defined"
        
        result = await self.debug_assistant._javascript_fallback_analysis(code, error_message)
        
        assert "issues" in result
        assert "suggestions" in result
        assert any("Reference error detected" in issue for issue in result["issues"])
        assert any("undefined variables" in suggestion for suggestion in result["suggestions"])
    
    @pytest.mark.asyncio
    async def test_fallback_debug_analysis(self):
        """Test fallback debug analysis."""
        context = {
            "code": "def hello():\n    print('Hello')",
            "language": "python",
            "error_message": "SyntaxError: invalid syntax"
        }
        user_context = {}
        
        result = await self.debug_assistant._fallback_debug_analysis(context, user_context)
        
        assert result["analysis_type"] == "fallback"
        assert "issues" in result
        assert "suggestions" in result
        assert result["confidence"] == 0.6
        assert result["provider"] == "fallback_analyzer"


class TestCopilotKitDebugAssistantPlugin:
    """Test the main plugin entry point."""
    
    @pytest.mark.asyncio
    @patch('handler.get_orchestrator')
    async def test_plugin_run_debug_analysis(self, mock_get_orchestrator):
        """Test plugin run with debug analysis."""
        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.get_debugging_assistance = AsyncMock(return_value={
            "analysis_type": "debug",
            "suggestions": ["Add error handling", "Check variable types"],
            "issues": ["Undefined variable 'x'"],
            "confidence": 0.9
        })
        mock_get_orchestrator.return_value = mock_orchestrator
        
        params = {
            "code": "print(x)",
            "language": "python",
            "error_message": "NameError: name 'x' is not defined",
            "analysis_type": "debug",
            "user_context": {}
        }
        
        result = await run(params)
        
        assert result["success"] is True
        assert result["analysis_type"] == "debug"
        assert result["language"] == "python"
        assert "debug_results" in result
        assert result["provider"] == "copilotkit_debug_assistant"
        
        # Verify orchestrator was called correctly
        mock_orchestrator.get_debugging_assistance.assert_called_once_with(
            code="print(x)",
            error_message="NameError: name 'x' is not defined",
            language="python"
        )
    
    @pytest.mark.asyncio
    @patch('handler.get_orchestrator')
    async def test_plugin_run_code_review(self, mock_get_orchestrator):
        """Test plugin run with code review analysis."""
        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.get_code_suggestions = AsyncMock(return_value=[
            {"content": "Add type hints", "confidence": 0.9},
            {"content": "Use list comprehension", "confidence": 0.8}
        ])
        mock_get_orchestrator.return_value = mock_orchestrator
        
        params = {
            "code": "def process_list(items):\n    result = []\n    for item in items:\n        result.append(item * 2)\n    return result",
            "language": "python",
            "analysis_type": "review",
            "user_context": {}
        }
        
        result = await run(params)
        
        assert result["success"] is True
        assert result["analysis_type"] == "review"
        assert result["language"] == "python"
        assert "debug_results" in result
        
        debug_results = result["debug_results"]
        assert debug_results["analysis_type"] == "review"
        assert "Add type hints" in debug_results["suggestions"]
        assert "Use list comprehension" in debug_results["suggestions"]
    
    @pytest.mark.asyncio
    @patch('handler.get_orchestrator')
    async def test_plugin_run_optimization(self, mock_get_orchestrator):
        """Test plugin run with optimization analysis."""
        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.enhanced_route = AsyncMock(return_value="Optimized code suggestions")
        mock_get_orchestrator.return_value = mock_orchestrator
        
        params = {
            "code": "for i in range(len(items)):\n    print(items[i])",
            "language": "python",
            "analysis_type": "optimize",
            "user_context": {}
        }
        
        result = await run(params)
        
        assert result["success"] is True
        assert result["analysis_type"] == "optimize"
        assert result["language"] == "python"
        
        debug_results = result["debug_results"]
        assert debug_results["analysis_type"] == "optimization"
        assert "Optimized code suggestions" in debug_results["suggestions"]
    
    @pytest.mark.asyncio
    async def test_plugin_run_validation_failure(self):
        """Test plugin run with validation failure."""
        params = {
            "code": "",  # Empty code should fail validation
            "language": "python",
            "analysis_type": "debug",
            "user_context": {}
        }
        
        result = await run(params)
        
        assert result["success"] is False
        assert result["error"] == "Input validation failed"
        assert "validation_warnings" in result
        assert any("No code provided" in warning for warning in result["validation_warnings"])
    
    @pytest.mark.asyncio
    @patch('handler.get_orchestrator')
    async def test_plugin_run_with_orchestrator_failure(self, mock_get_orchestrator):
        """Test plugin run when orchestrator fails."""
        # Mock orchestrator to raise exception
        mock_orchestrator = Mock()
        mock_orchestrator.get_debugging_assistance = AsyncMock(side_effect=Exception("Orchestrator failed"))
        mock_get_orchestrator.return_value = mock_orchestrator
        
        params = {
            "code": "print('hello')",
            "language": "python",
            "analysis_type": "debug",
            "user_context": {}
        }
        
        result = await run(params)
        
        # Should fall back to fallback analysis
        assert result["success"] is True
        assert result["analysis_type"] == "fallback"
        assert result["provider"] == "fallback_analyzer"
        assert "warning" in result
        assert "CopilotKit unavailable" in result["warning"]
    
    @pytest.mark.asyncio
    async def test_plugin_run_complete_failure(self):
        """Test plugin run when everything fails."""
        # Mock to cause complete failure
        with patch('handler.CopilotKitDebugAssistant') as mock_class:
            mock_class.side_effect = Exception("Complete failure")
            
            params = {
                "code": "print('hello')",
                "language": "python",
                "analysis_type": "debug",
                "user_context": {}
            }
            
            result = await run(params)
            
            assert result["success"] is False
            assert "error" in result
            assert "fallback_error" in result
            assert result["provider"] == "copilotkit_debug_assistant"
    
    @pytest.mark.asyncio
    @patch('handler.get_orchestrator')
    async def test_plugin_run_with_user_context_storage(self, mock_get_orchestrator):
        """Test plugin run with user context storage."""
        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.get_debugging_assistance = AsyncMock(return_value={
            "analysis_type": "debug",
            "suggestions": ["Test suggestion"],
            "issues": [],
            "confidence": 0.8
        })
        mock_get_orchestrator.return_value = mock_orchestrator
        
        user_context = {"user_id": "test_user"}
        params = {
            "code": "def test(): pass",
            "language": "python",
            "analysis_type": "debug",
            "user_context": user_context
        }
        
        result = await run(params)
        
        assert result["success"] is True
        assert "storage_info" in result
        
        # Check that debug history was stored in user context
        assert "debug_history" in user_context
        assert len(user_context["debug_history"]) == 1
    
    @pytest.mark.asyncio
    @patch('handler.get_orchestrator')
    async def test_plugin_run_multiple_languages(self, mock_get_orchestrator):
        """Test plugin run with different programming languages."""
        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.get_debugging_assistance = AsyncMock(return_value={
            "analysis_type": "debug",
            "suggestions": ["Language-specific suggestion"],
            "issues": [],
            "confidence": 0.8
        })
        mock_get_orchestrator.return_value = mock_orchestrator
        
        languages = ["python", "javascript", "typescript", "java", "c++"]
        
        for language in languages:
            params = {
                "code": "console.log('hello')" if language in ["javascript", "typescript"] else "print('hello')",
                "language": language,
                "analysis_type": "debug",
                "user_context": {}
            }
            
            result = await run(params)
            
            assert result["success"] is True
            assert result["language"] == language
            assert result["provider"] == "copilotkit_debug_assistant"


class TestDebugAssistantHooks:
    """Test debug assistant hook integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.debug_assistant = CopilotKitDebugAssistant()
    
    @pytest.mark.asyncio
    async def test_hook_registration(self):
        """Test that hooks are properly registered."""
        # This is a basic test to ensure hooks can be registered
        # In a real scenario, we'd test the actual hook system integration
        assert hasattr(self.debug_assistant, 'register_hook')
        assert hasattr(self.debug_assistant, 'trigger_hook_safe')
    
    @pytest.mark.asyncio
    async def test_validation_hook_integration(self):
        """Test validation hook integration."""
        context = {
            "code": "def test(): pass",
            "language": "python",
            "analysis_type": "debug"
        }
        user_context = {}
        
        # Test direct hook call
        result = await self.debug_assistant._validate_code_input(context, user_context)
        
        assert isinstance(result, dict)
        assert "valid" in result
        assert "warnings" in result
        assert "suggestions" in result
    
    @pytest.mark.asyncio
    async def test_storage_hook_integration(self):
        """Test storage hook integration."""
        context = {
            "debug_results": {
                "issues": ["Test issue"],
                "suggestions": ["Test suggestion"],
                "analysis_type": "debug",
                "confidence": 0.8
            },
            "code": "def test(): pass",
            "language": "python",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        user_context = {}
        
        # Test direct hook call
        result = await self.debug_assistant._store_debug_results(context, user_context)
        
        assert isinstance(result, dict)
        assert "stored" in result
        assert result["stored"] is True
    
    @pytest.mark.asyncio
    async def test_fallback_hook_integration(self):
        """Test fallback hook integration."""
        context = {
            "code": "def test(): pass",
            "language": "python",
            "error_message": "Test error"
        }
        user_context = {}
        
        # Test direct hook call
        result = await self.debug_assistant._fallback_debug_analysis(context, user_context)
        
        assert isinstance(result, dict)
        assert "analysis_type" in result
        assert result["analysis_type"] == "fallback"


if __name__ == "__main__":
    pytest.main([__file__])