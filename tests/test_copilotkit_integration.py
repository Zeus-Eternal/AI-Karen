"""
Tests for CopilotKit LLM Provider Integration

Tests the CopilotKit provider integration with Karen's existing LLM infrastructure,
including provider registration, chat orchestrator integration, and fallback mechanisms.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

from ai_karen_engine.integrations.providers.copilotkit_provider import CopilotKitProvider
from ai_karen_engine.integrations.llm_utils import LLMUtils, GenerationFailed, EmbeddingFailed


class TestCopilotKitProvider:
    """Test CopilotKit provider implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider = CopilotKitProvider(
            api_key="test_key",
            model="gpt-4",
            enable_code_assistance=True,
            enable_contextual_suggestions=True
        )
    
    def test_provider_initialization(self):
        """Test CopilotKit provider initialization."""
        assert self.provider.api_key == "test_key"
        assert self.provider.model == "gpt-4"
        assert self.provider.enable_code_assistance is True
        assert self.provider.enable_contextual_suggestions is True
        assert self.provider.timeout == 60
        assert self.provider.max_retries == 3
    
    def test_provider_initialization_without_api_key(self):
        """Test provider initialization without API key."""
        with patch.dict('os.environ', {}, clear=True):
            provider = CopilotKitProvider()
            assert provider.api_key is None
    
    def test_provider_initialization_with_env_vars(self):
        """Test provider initialization with environment variables."""
        with patch.dict('os.environ', {
            'COPILOTKIT_API_KEY': 'env_key',
            'COPILOTKIT_BASE_URL': 'https://custom.api.com'
        }):
            provider = CopilotKitProvider()
            assert provider.api_key == 'env_key'
            assert provider.base_url == 'https://custom.api.com'
    
    @patch('ai_karen_engine.integrations.providers.copilotkit_provider.copilotkit')
    def test_generate_text_success(self, mock_copilotkit):
        """Test successful text generation."""
        # Mock CopilotKit client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Generated response"
        mock_client.generate_text.return_value = mock_response
        mock_copilotkit.CopilotKit.return_value = mock_client
        
        # Create provider with mocked client
        provider = CopilotKitProvider(api_key="test_key")
        provider.client = mock_client
        
        result = provider.generate_text("Test prompt")
        
        assert result == "Generated response"
        mock_client.generate_text.assert_called_once()
    
    @patch('ai_karen_engine.integrations.providers.copilotkit_provider.copilotkit')
    def test_generate_text_code_related(self, mock_copilotkit):
        """Test text generation for code-related prompts."""
        # Mock CopilotKit client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Code response"
        mock_client.generate_code_assistance.return_value = mock_response
        mock_copilotkit.CopilotKit.return_value = mock_client
        
        # Create provider with mocked client
        provider = CopilotKitProvider(api_key="test_key", enable_code_assistance=True)
        provider.client = mock_client
        
        result = provider.generate_text("Write a Python function")
        
        assert result == "Code response"
        mock_client.generate_code_assistance.assert_called_once()
    
    def test_generate_text_without_api_key(self):
        """Test text generation without API key."""
        provider = CopilotKitProvider()
        
        with pytest.raises(GenerationFailed, match="CopilotKit API key required"):
            provider.generate_text("Test prompt")
    
    @patch('ai_karen_engine.integrations.providers.copilotkit_provider.copilotkit')
    def test_generate_text_with_retry(self, mock_copilotkit):
        """Test text generation with retry logic."""
        # Mock CopilotKit client
        mock_client = Mock()
        mock_client.generate_text.side_effect = [
            Exception("Rate limit exceeded"),  # First attempt fails
            Mock(text="Success after retry")   # Second attempt succeeds
        ]
        mock_copilotkit.CopilotKit.return_value = mock_client
        
        # Create provider with mocked client
        provider = CopilotKitProvider(api_key="test_key", max_retries=2)
        provider.client = mock_client
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = provider.generate_text("Test prompt")
        
        assert result == "Success after retry"
        assert mock_client.generate_text.call_count == 2
    
    @patch('ai_karen_engine.integrations.providers.copilotkit_provider.copilotkit')
    def test_get_code_suggestions(self, mock_copilotkit):
        """Test code suggestions functionality."""
        # Mock CopilotKit client
        mock_client = Mock()
        mock_suggestions = [
            {
                "type": "completion",
                "content": "def hello():\n    print('Hello')",
                "confidence": 0.9,
                "explanation": "Function definition"
            }
        ]
        mock_client.get_code_suggestions.return_value = mock_suggestions
        mock_copilotkit.CopilotKit.return_value = mock_client
        
        # Create provider with mocked client
        provider = CopilotKitProvider(api_key="test_key", enable_code_assistance=True)
        provider.client = mock_client
        
        result = provider.get_code_suggestions("def hello", "python")
        
        assert len(result) == 1
        assert result[0]["type"] == "completion"
        assert result[0]["content"] == "def hello():\n    print('Hello')"
        assert result[0]["language"] == "python"
        mock_client.get_code_suggestions.assert_called_once_with(
            code="def hello", language="python"
        )
    
    @patch('ai_karen_engine.integrations.providers.copilotkit_provider.copilotkit')
    def test_get_contextual_suggestions(self, mock_copilotkit):
        """Test contextual suggestions functionality."""
        # Mock CopilotKit client
        mock_client = Mock()
        mock_suggestions = [
            {
                "type": "contextual",
                "content": "Consider using async/await",
                "confidence": 0.8,
                "explanation": "Performance improvement",
                "actionable": True
            }
        ]
        mock_client.get_contextual_suggestions.return_value = mock_suggestions
        mock_copilotkit.CopilotKit.return_value = mock_client
        
        # Create provider with mocked client
        provider = CopilotKitProvider(api_key="test_key", enable_contextual_suggestions=True)
        provider.client = mock_client
        
        context = {"conversation_history": ["Hello", "How to optimize code?"]}
        result = provider.get_contextual_suggestions("Optimize my code", context)
        
        assert len(result) == 1
        assert result[0]["type"] == "contextual"
        assert result[0]["content"] == "Consider using async/await"
        assert result[0]["actionable"] is True
        mock_client.get_contextual_suggestions.assert_called_once_with(
            message="Optimize my code", context=context
        )
    
    @patch('ai_karen_engine.integrations.providers.copilotkit_provider.copilotkit')
    def test_embed_text(self, mock_copilotkit):
        """Test text embedding functionality."""
        # Mock CopilotKit client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.embedding = [0.1, 0.2, 0.3]
        mock_client.create_embedding.return_value = mock_response
        mock_copilotkit.CopilotKit.return_value = mock_client
        
        # Create provider with mocked client
        provider = CopilotKitProvider(api_key="test_key")
        provider.client = mock_client
        
        result = provider.embed("Test text")
        
        assert result == [0.1, 0.2, 0.3]
        mock_client.create_embedding.assert_called_once_with(text="Test text")
    
    def test_embed_without_api_key(self):
        """Test embedding without API key."""
        provider = CopilotKitProvider()
        
        with pytest.raises(EmbeddingFailed, match="CopilotKit API key required"):
            provider.embed("Test text")
    
    def test_is_code_related(self):
        """Test code detection functionality."""
        provider = CopilotKitProvider()
        
        # Code-related messages
        assert provider._is_code_related("Write a Python function")
        assert provider._is_code_related("Debug this JavaScript code")
        assert provider._is_code_related("```python\nprint('hello')\n```")
        assert provider._is_code_related("How to import numpy?")
        
        # Non-code messages
        assert not provider._is_code_related("What's the weather today?")
        assert not provider._is_code_related("Tell me a joke")
    
    def test_get_provider_info(self):
        """Test provider info retrieval."""
        provider = CopilotKitProvider(
            api_key="test_key",
            model="gpt-4",
            enable_code_assistance=True,
            enable_contextual_suggestions=True
        )
        
        info = provider.get_provider_info()
        
        assert info["name"] == "copilotkit"
        assert info["model"] == "gpt-4"
        assert info["has_api_key"] is True
        assert info["supports_embeddings"] is True
        assert info["supports_code_assistance"] is True
        assert info["supports_contextual_suggestions"] is True
    
    @patch('ai_karen_engine.integrations.providers.copilotkit_provider.copilotkit')
    def test_health_check_success(self, mock_copilotkit):
        """Test successful health check."""
        # Mock CopilotKit client
        mock_client = Mock()
        mock_client.generate_text.return_value = Mock(text="OK")
        mock_copilotkit.CopilotKit.return_value = mock_client
        
        # Create provider with mocked client
        provider = CopilotKitProvider(api_key="test_key")
        provider.client = mock_client
        
        result = provider.health_check()
        
        assert result["status"] == "healthy"
        assert "response_time" in result
        assert result["model_tested"] == "gpt-4"
    
    def test_health_check_no_api_key(self):
        """Test health check without API key."""
        provider = CopilotKitProvider()
        
        result = provider.health_check()
        
        assert result["status"] == "unhealthy"
        assert "No API key provided" in result["error"]


class TestLLMUtilsCopilotKitIntegration:
    """Test CopilotKit integration with LLMUtils."""
    
    def test_llm_utils_with_copilotkit(self):
        """Test LLMUtils can use CopilotKit provider."""
        with patch.dict('os.environ', {'COPILOTKIT_API_KEY': 'test_key'}):
            llm_utils = LLMUtils(use_registry=True)
            
            # Verify CopilotKit is available
            providers = llm_utils.list_available_providers()
            assert "copilotkit" in providers
            
            # Test getting CopilotKit provider
            provider = llm_utils.get_provider("copilotkit")
            assert isinstance(provider, CopilotKitProvider)
    
    @patch('ai_karen_engine.integrations.providers.copilotkit_provider.copilotkit')
    def test_llm_utils_generate_text_with_copilotkit(self, mock_copilotkit):
        """Test text generation through LLMUtils with CopilotKit."""
        # Mock CopilotKit client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "CopilotKit generated text"
        mock_client.generate_text.return_value = mock_response
        mock_copilotkit.CopilotKit.return_value = mock_client
        
        with patch.dict('os.environ', {'COPILOTKIT_API_KEY': 'test_key'}):
            llm_utils = LLMUtils(use_registry=True)
            
            # Mock the provider to use our mocked client
            provider = llm_utils.get_provider("copilotkit")
            provider.client = mock_client
            
            result = llm_utils.generate_text(
                "Test prompt",
                provider="copilotkit"
            )
            
            assert result == "CopilotKit generated text"
    
    def test_llm_utils_health_check_copilotkit(self):
        """Test health check for CopilotKit through LLMUtils."""
        with patch.dict('os.environ', {'COPILOTKIT_API_KEY': 'test_key'}):
            llm_utils = LLMUtils(use_registry=True)
            
            # Mock health check
            with patch.object(CopilotKitProvider, 'health_check') as mock_health:
                mock_health.return_value = {"status": "healthy", "response_time": 0.5}
                
                result = llm_utils.health_check_provider("copilotkit")
                
                assert result["status"] == "healthy"
                assert "response_time" in result


if __name__ == "__main__":
    pytest.main([__file__])