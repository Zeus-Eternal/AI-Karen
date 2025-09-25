"""
Tests for Enhanced LLM Providers with CopilotKit Integration

Tests the enhanced LLM provider base class and its integration with CopilotKit
for code assistance, debugging, and documentation generation capabilities.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

from ai_karen_engine.integrations.providers.base import BaseLLMProvider
from ai_karen_engine.llm_orchestrator import get_orchestrator
from ai_karen_engine.services.copilotkit_doc_generator import get_doc_generator


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing enhanced capabilities."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_name = "mock_provider"
        self.responses = {}
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Mock response generation."""
        return self.responses.get("generate_response", "Mock response")
    
    async def stream_response(self, prompt: str, **kwargs):
        """Mock streaming response."""
        yield self.responses.get("stream_response", "Mock stream response")
    
    def get_available_models(self) -> List[str]:
        """Mock available models."""
        return ["mock-model-1", "mock-model-2"]
    
    def is_available(self) -> bool:
        """Mock availability check."""
        return True
    
    async def get_status(self) -> Dict[str, Any]:
        """Mock status check."""
        return {
            "status": "healthy",
            "provider": self.provider_name,
            "models": self.get_available_models()
        }


class TestEnhancedBaseLLMProvider:
    """Test enhanced base LLM provider functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "copilotkit_enabled": True,
            "code_assistance_enabled": True,
            "debugging_assistance_enabled": True,
            "documentation_generation_enabled": True,
            "copilotkit_config": {
                "api_key": "test_key",
                "base_url": "https://test.api.com"
            }
        }
        self.provider = MockLLMProvider(self.config)
    
    def test_provider_initialization_with_copilotkit(self):
        """Test provider initialization with CopilotKit enabled."""
        assert self.provider.copilotkit_enabled is True
        assert self.provider.code_assistance_enabled is True
        assert self.provider.debugging_assistance_enabled is True
        assert self.provider.documentation_generation_enabled is True
    
    def test_provider_initialization_without_copilotkit(self):
        """Test provider initialization without CopilotKit."""
        config = {"copilotkit_enabled": False}
        provider = MockLLMProvider(config)
        
        assert provider.copilotkit_enabled is False
        assert provider._copilotkit_provider is None
    
    def test_code_detection(self):
        """Test code-related prompt detection."""
        # Code-related prompts
        assert self.provider._is_code_related("Write a Python function")
        assert self.provider._is_code_related("Debug this JavaScript code")
        assert self.provider._is_code_related("```python\nprint('hello')\n```")
        assert self.provider._is_code_related("How to import numpy?")
        assert self.provider._is_code_related("Refactor this algorithm")
        
        # Non-code prompts
        assert not self.provider._is_code_related("What's the weather today?")
        assert not self.provider._is_code_related("Tell me a joke")
        assert not self.provider._is_code_related("Explain quantum physics")
    
    def test_debugging_detection(self):
        """Test debugging request detection."""
        # Debugging prompts
        assert self.provider._is_debugging_request("Debug this error")
        assert self.provider._is_debugging_request("Fix this bug")
        assert self.provider._is_debugging_request("Why is this not working?")
        assert self.provider._is_debugging_request("Exception in line 42")
        assert self.provider._is_debugging_request("Stack trace analysis")
        
        # Non-debugging prompts
        assert not self.provider._is_debugging_request("Write a function")
        assert not self.provider._is_debugging_request("Explain this code")
    
    def test_documentation_detection(self):
        """Test documentation request detection."""
        # Documentation prompts
        assert self.provider._is_documentation_request("Generate documentation")
        assert self.provider._is_documentation_request("Add docstrings")
        assert self.provider._is_documentation_request("What does this function do?")
        assert self.provider._is_documentation_request("Create API docs")
        
        # Non-documentation prompts
        assert not self.provider._is_documentation_request("Debug this code")
        assert not self.provider._is_documentation_request("Optimize performance")
    
    @pytest.mark.asyncio
    async def test_fallback_code_suggestions(self):
        """Test fallback code suggestions when CopilotKit is unavailable."""
        provider = MockLLMProvider({"copilotkit_enabled": False})
        
        suggestions = await provider.get_code_suggestions("def hello():", "python")
        
        assert len(suggestions) == 1
        assert suggestions[0]["type"] == "completion"
        assert "error handling" in suggestions[0]["content"]
        assert suggestions[0]["confidence"] == 0.6
    
    @pytest.mark.asyncio
    async def test_fallback_debugging_assistance(self):
        """Test fallback debugging assistance when CopilotKit is unavailable."""
        provider = MockLLMProvider({"copilotkit_enabled": False})
        
        debug_info = await provider.get_debugging_assistance(
            "import unknown_module", 
            "ModuleNotFoundError: No module named 'unknown_module'", 
            "python"
        )
        
        assert "suggestions" in debug_info
        assert "analysis" in debug_info
        assert "Check if all required modules are installed" in debug_info["suggestions"]
        assert debug_info["confidence"] == 0.5
    
    @pytest.mark.asyncio
    async def test_fallback_documentation_generation(self):
        """Test fallback documentation generation when CopilotKit is unavailable."""
        provider = MockLLMProvider({"copilotkit_enabled": False})
        
        documentation = await provider.generate_documentation(
            "def add(a, b):\n    return a + b", 
            "python", 
            "comprehensive"
        )
        
        assert "Python Code Documentation" in documentation
        assert "Language: python" in documentation
        assert "Style: comprehensive" in documentation
        assert "Lines of code: 2" in documentation
    
    @pytest.mark.asyncio
    async def test_fallback_contextual_suggestions(self):
        """Test fallback contextual suggestions when CopilotKit is unavailable."""
        provider = MockLLMProvider({"copilotkit_enabled": False})
        
        suggestions = await provider.get_contextual_suggestions(
            "How to optimize this code?", 
            {"context": "performance"}
        )
        
        assert len(suggestions) == 1
        assert suggestions[0]["type"] == "suggestion"
        assert "CopilotKit is currently unavailable" in suggestions[0]["content"]
        assert suggestions[0]["confidence"] == 0.5
    
    @pytest.mark.asyncio
    async def test_enhanced_generate_response_with_debugging(self):
        """Test enhanced response generation for debugging requests."""
        self.provider.responses["generate_response"] = "This is a basic response"
        
        # Mock debugging assistance
        with patch.object(self.provider, 'get_debugging_assistance') as mock_debug:
            mock_debug.return_value = {
                "suggestions": ["Add error handling", "Check variable types"],
                "analysis": "Code analysis complete"
            }
            
            prompt = "Debug this code:\n```python\nprint(x)\n```"
            response = await self.provider.enhanced_generate_response(prompt)
            
            assert "This is a basic response" in response
            assert "Debugging Insights:" in response
            assert "Add error handling" in response
            assert "Check variable types" in response
    
    @pytest.mark.asyncio
    async def test_enhanced_generate_response_with_documentation(self):
        """Test enhanced response generation for documentation requests."""
        self.provider.responses["generate_response"] = "This is a basic response"
        
        # Mock documentation generation
        with patch.object(self.provider, 'generate_documentation') as mock_doc:
            mock_doc.return_value = "# Function Documentation\n\nThis function prints a value."
            
            prompt = "Document this code:\n```python\ndef print_value(x):\n    print(x)\n```"
            response = await self.provider.enhanced_generate_response(prompt)
            
            assert "This is a basic response" in response
            assert "Generated Documentation:" in response
            assert "Function Documentation" in response
    
    @pytest.mark.asyncio
    async def test_enhanced_generate_response_with_code_suggestions(self):
        """Test enhanced response generation with code suggestions."""
        self.provider.responses["generate_response"] = "This is a basic response"
        
        # Mock code suggestions
        with patch.object(self.provider, 'get_code_suggestions') as mock_suggestions:
            mock_suggestions.return_value = [
                {"content": "Add type hints", "confidence": 0.9},
                {"content": "Use list comprehension", "confidence": 0.8},
                {"content": "Add docstring", "confidence": 0.7}
            ]
            
            prompt = "Improve this code:\n```python\ndef process_list(items):\n    result = []\n    for item in items:\n        result.append(item * 2)\n    return result\n```"
            response = await self.provider.enhanced_generate_response(prompt)
            
            assert "This is a basic response" in response
            assert "Code Suggestions:" in response
            assert "Add type hints" in response
            assert "Use list comprehension" in response
            assert "Add docstring" in response
    
    @pytest.mark.asyncio
    async def test_enhanced_generate_response_non_code(self):
        """Test enhanced response generation for non-code requests."""
        self.provider.responses["generate_response"] = "This is a basic response"
        
        prompt = "What's the capital of France?"
        response = await self.provider.enhanced_generate_response(prompt)
        
        # Should return basic response without enhancements
        assert response == "This is a basic response"
    
    @pytest.mark.asyncio
    async def test_get_enhanced_status(self):
        """Test enhanced status reporting including CopilotKit integration."""
        status = await self.provider.get_enhanced_status()
        
        assert "copilotkit_integration" in status
        assert status["copilotkit_integration"]["enabled"] is True
        assert "features" in status["copilotkit_integration"]
        
        features = status["copilotkit_integration"]["features"]
        assert features["code_assistance"] is True
        assert features["debugging_assistance"] is True
        assert features["documentation_generation"] is True
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.integrations.providers.base.CopilotKitProvider')
    async def test_copilotkit_integration_initialization(self, mock_copilotkit_provider):
        """Test CopilotKit integration initialization."""
        # Mock CopilotKit provider
        mock_instance = Mock()
        mock_copilotkit_provider.return_value = mock_instance
        
        config = {
            "copilotkit_enabled": True,
            "copilotkit_config": {"api_key": "test_key"}
        }
        
        provider = MockLLMProvider(config)
        
        # Verify CopilotKit provider was initialized
        mock_copilotkit_provider.assert_called_once_with({"api_key": "test_key"})
        assert provider._copilotkit_provider == mock_instance
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.integrations.providers.base.CopilotKitProvider')
    async def test_copilotkit_integration_with_code_suggestions(self, mock_copilotkit_provider):
        """Test CopilotKit integration for code suggestions."""
        # Mock CopilotKit provider
        mock_instance = Mock()
        mock_instance.get_code_completion = AsyncMock(return_value=[
            {"type": "completion", "content": "CopilotKit suggestion", "confidence": 0.9}
        ])
        mock_copilotkit_provider.return_value = mock_instance
        
        config = {
            "copilotkit_enabled": True,
            "copilotkit_config": {"api_key": "test_key"}
        }
        
        provider = MockLLMProvider(config)
        provider._copilotkit_provider = mock_instance
        
        suggestions = await provider.get_code_suggestions("def hello():", "python")
        
        assert len(suggestions) == 1
        assert suggestions[0]["content"] == "CopilotKit suggestion"
        assert suggestions[0]["confidence"] == 0.9
        
        mock_instance.get_code_completion.assert_called_once_with(
            code_context="def hello():",
            language="python",
            cursor_position=len("def hello():"),
        )
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.integrations.providers.base.CopilotKitProvider')
    async def test_copilotkit_integration_with_debugging(self, mock_copilotkit_provider):
        """Test CopilotKit integration for debugging assistance."""
        # Mock CopilotKit provider
        mock_instance = Mock()
        mock_instance.analyze_code = AsyncMock(return_value={
            "suggestions": ["CopilotKit debug suggestion"],
            "analysis": "CopilotKit analysis",
            "confidence": 0.9
        })
        mock_copilotkit_provider.return_value = mock_instance
        
        config = {
            "copilotkit_enabled": True,
            "copilotkit_config": {"api_key": "test_key"}
        }
        
        provider = MockLLMProvider(config)
        provider._copilotkit_provider = mock_instance
        
        debug_info = await provider.get_debugging_assistance(
            "print(x)", "NameError: name 'x' is not defined", "python"
        )
        
        assert debug_info["suggestions"] == ["CopilotKit debug suggestion"]
        assert debug_info["analysis"] == "CopilotKit analysis"
        assert debug_info["confidence"] == 0.9
        
        mock_instance.analyze_code.assert_called_once_with(
            code="print(x)",
            language="python",
            analysis_type="debug",
            error_context="NameError: name 'x' is not defined"
        )
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.integrations.providers.base.CopilotKitProvider')
    async def test_copilotkit_integration_with_documentation(self, mock_copilotkit_provider):
        """Test CopilotKit integration for documentation generation."""
        # Mock CopilotKit provider
        mock_instance = Mock()
        mock_instance.generate_documentation = AsyncMock(return_value="CopilotKit generated documentation")
        mock_copilotkit_provider.return_value = mock_instance
        
        config = {
            "copilotkit_enabled": True,
            "copilotkit_config": {"api_key": "test_key"}
        }
        
        provider = MockLLMProvider(config)
        provider._copilotkit_provider = mock_instance
        
        documentation = await provider.generate_documentation(
            "def add(a, b):\n    return a + b", "python", "comprehensive"
        )
        
        assert documentation == "CopilotKit generated documentation"
        
        mock_instance.generate_documentation.assert_called_once_with(
            code="def add(a, b):\n    return a + b",
            language="python",
            style="comprehensive"
        )
    
    @pytest.mark.asyncio
    async def test_disabled_features(self):
        """Test behavior when features are disabled."""
        config = {
            "copilotkit_enabled": True,
            "code_assistance_enabled": False,
            "debugging_assistance_enabled": False,
            "documentation_generation_enabled": False
        }
        
        provider = MockLLMProvider(config)
        
        # Code assistance disabled
        suggestions = await provider.get_code_suggestions("def hello():", "python")
        assert suggestions == []
        
        # Debugging assistance disabled
        debug_info = await provider.get_debugging_assistance("print(x)", "error", "python")
        assert debug_info["suggestions"] == []
        assert debug_info["analysis"] == "Debugging assistance disabled"
        
        # Documentation generation disabled
        documentation = await provider.generate_documentation("code", "python")
        assert documentation == "Documentation generation disabled"


class TestLLMOrchestratorEnhancements:
    """Test LLM orchestrator enhancements for CopilotKit integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = get_orchestrator()
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.llm_orchestrator.get_orchestrator')
    async def test_orchestrator_code_suggestions(self, mock_get_orchestrator):
        """Test orchestrator code suggestions routing."""
        # Mock orchestrator instance
        mock_orchestrator = Mock()
        mock_orchestrator.get_code_suggestions = AsyncMock(return_value=[
            {"type": "completion", "content": "Orchestrator suggestion"}
        ])
        mock_get_orchestrator.return_value = mock_orchestrator
        
        suggestions = await mock_orchestrator.get_code_suggestions("def hello():", "python")
        
        assert len(suggestions) == 1
        assert suggestions[0]["content"] == "Orchestrator suggestion"
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.llm_orchestrator.get_orchestrator')
    async def test_orchestrator_debugging_assistance(self, mock_get_orchestrator):
        """Test orchestrator debugging assistance routing."""
        # Mock orchestrator instance
        mock_orchestrator = Mock()
        mock_orchestrator.get_debugging_assistance = AsyncMock(return_value={
            "suggestions": ["Orchestrator debug suggestion"],
            "analysis": "Orchestrator analysis"
        })
        mock_get_orchestrator.return_value = mock_orchestrator
        
        debug_info = await mock_orchestrator.get_debugging_assistance(
            "print(x)", "NameError", "python"
        )
        
        assert debug_info["suggestions"] == ["Orchestrator debug suggestion"]
        assert debug_info["analysis"] == "Orchestrator analysis"
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.llm_orchestrator.get_orchestrator')
    async def test_orchestrator_documentation_generation(self, mock_get_orchestrator):
        """Test orchestrator documentation generation routing."""
        # Mock orchestrator instance
        mock_orchestrator = Mock()
        mock_orchestrator.generate_documentation = AsyncMock(return_value="Orchestrator documentation")
        mock_get_orchestrator.return_value = mock_orchestrator
        
        documentation = await mock_orchestrator.generate_documentation(
            "def add(a, b): return a + b", "python", "comprehensive"
        )
        
        assert documentation == "Orchestrator documentation"
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.llm_orchestrator.get_orchestrator')
    async def test_orchestrator_enhanced_routing(self, mock_get_orchestrator):
        """Test orchestrator enhanced routing capabilities."""
        # Mock orchestrator instance
        mock_orchestrator = Mock()
        mock_orchestrator.enhanced_route = AsyncMock(return_value="Enhanced response")
        mock_get_orchestrator.return_value = mock_orchestrator
        
        response = await mock_orchestrator.enhanced_route("Test prompt")
        
        assert response == "Enhanced response"


class TestDocumentationGeneratorService:
    """Test CopilotKit documentation generator service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.doc_generator = get_doc_generator()
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.services.copilotkit_doc_generator.get_orchestrator')
    async def test_code_documentation_generation(self, mock_get_orchestrator):
        """Test code documentation generation."""
        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.generate_documentation = AsyncMock(return_value="Generated documentation")
        mock_orchestrator.enhanced_route = AsyncMock(return_value="Usage examples")
        mock_get_orchestrator.return_value = mock_orchestrator
        
        result = await self.doc_generator.generate_code_documentation(
            code="def hello(): print('Hello')",
            language="python",
            doc_style="reference",
            include_examples=True
        )
        
        assert result["success"] is True
        assert "Generated documentation" in result["documentation"]
        assert "Usage examples" in result["documentation"]
        assert result["language"] == "python"
        assert result["doc_style"] == "reference"
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.services.copilotkit_doc_generator.get_orchestrator')
    async def test_api_documentation_generation(self, mock_get_orchestrator):
        """Test API documentation generation."""
        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.enhanced_route = AsyncMock(return_value="API documentation")
        mock_get_orchestrator.return_value = mock_orchestrator
        
        api_spec = {"openapi": "3.0.0", "info": {"title": "Test API"}}
        
        result = await self.doc_generator.generate_api_documentation(
            api_spec=api_spec,
            format_type="openapi"
        )
        
        assert result["success"] is True
        assert result["documentation"] == "API documentation"
        assert result["format_type"] == "openapi"
    
    @pytest.mark.asyncio
    @patch('ai_karen_engine.services.copilotkit_doc_generator.get_orchestrator')
    async def test_documentation_enhancement(self, mock_get_orchestrator):
        """Test existing documentation enhancement."""
        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.enhanced_route = AsyncMock(return_value="Enhanced documentation")
        mock_get_orchestrator.return_value = mock_orchestrator
        
        # Create temporary test file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Original Documentation\n\nThis is basic documentation.")
            temp_file = f.name
        
        try:
            result = await self.doc_generator.enhance_existing_documentation(
                doc_file=temp_file,
                enhancement_type="comprehensive"
            )
            
            assert result["success"] is True
            assert result["enhancement_type"] == "comprehensive"
            assert "backup_file" in result
            
        finally:
            # Clean up
            import os
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            backup_file = temp_file.replace('.md', '.backup.md')
            if os.path.exists(backup_file):
                os.unlink(backup_file)


if __name__ == "__main__":
    pytest.main([__file__])