"""
Unit tests for the enhanced unified LLM client.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.core.response.unified_client import (
    UnifiedLLMClient, 
    ModelSelector, 
    TinyLlamaClient, 
    OllamaClient, 
    FallbackLLM,
    create_local_first_client,
    create_local_only_client
)
from src.core.response.protocols import LLMClient


class MockLLMClient:
    """Mock LLM client for testing."""
    
    def __init__(self, name: str = "mock", should_fail: bool = False):
        self.name = name
        self.should_fail = should_fail
        self._warmed = False
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if self.should_fail:
            raise RuntimeError(f"Mock {self.name} client failed")
        return f"Response from {self.name}: {messages[-1]['content']}"
    
    def warmup(self):
        self._warmed = True


class TestFallbackLLM:
    """Test the fallback LLM."""
    
    def test_fallback_response(self):
        """Test fallback returns configured message."""
        fallback = FallbackLLM("Test message")
        messages = [{"role": "user", "content": "Hello"}]
        
        response = fallback.generate(messages)
        assert response == "Test message"
    
    def test_default_fallback_message(self):
        """Test default fallback message."""
        fallback = FallbackLLM()
        messages = [{"role": "user", "content": "Hello"}]
        
        response = fallback.generate(messages)
        assert "fallback mode" in response.lower()


class TestModelSelector:
    """Test the enhanced model selector."""
    
    def test_local_first_selection(self):
        """Test local-first selection logic."""
        local_client = MockLLMClient("local")
        remote_client = MockLLMClient("remote")
        
        selector = ModelSelector([local_client], remote_client, local_only=False)
        
        # Should select local by default
        selected = selector.select_client()
        assert selected == local_client
    
    def test_local_only_mode(self):
        """Test local-only mode never selects remote."""
        local_client = MockLLMClient("local")
        remote_client = MockLLMClient("remote")
        
        selector = ModelSelector([local_client], remote_client, local_only=True)
        
        # Should always select local even with cloud hint
        selected = selector.select_client(cloud_hint=True)
        assert selected == local_client
    
    def test_cloud_routing_with_large_context(self):
        """Test cloud routing for large context."""
        local_client = MockLLMClient("local")
        remote_client = MockLLMClient("remote")
        
        selector = ModelSelector([local_client], remote_client, local_only=False)
        
        # Large context should suggest cloud
        selected = selector.select_client(context_size=5000, cloud_hint=True)
        assert selected == remote_client
    
    def test_complex_intent_routing(self):
        """Test cloud routing for complex intents."""
        local_client = MockLLMClient("local")
        remote_client = MockLLMClient("remote")
        
        selector = ModelSelector([local_client], remote_client, local_only=False)
        
        # Complex intent should suggest cloud
        selected = selector.select_client(intent="code_optimization", cloud_hint=True)
        assert selected == remote_client
    
    def test_ordered_clients(self):
        """Test ordered client list."""
        local1 = MockLLMClient("local1")
        local2 = MockLLMClient("local2")
        remote = MockLLMClient("remote")
        
        selector = ModelSelector([local1, local2], remote, local_only=False)
        
        # Local only
        clients = selector.ordered(cloud_enabled=False)
        assert clients == [local1, local2]
        
        # With cloud
        clients = selector.ordered(cloud_enabled=True)
        assert clients == [local1, local2, remote]
    
    def test_performance_recording(self):
        """Test performance metrics recording."""
        selector = ModelSelector([MockLLMClient()], None)
        
        selector.record_performance("test_client", 1.5)
        selector.record_performance("test_client", 2.0)
        
        assert len(selector._performance_history["test_client"]) == 2
        assert selector._performance_history["test_client"] == [1.5, 2.0]


class TestUnifiedLLMClient:
    """Test the enhanced unified LLM client."""
    
    def test_successful_generation(self):
        """Test successful response generation."""
        local_client = MockLLMClient("local")
        
        client = UnifiedLLMClient(
            local_clients=[local_client],
            auto_warmup=False
        )
        
        messages = [{"role": "user", "content": "Hello"}]
        response = client.generate(messages)
        
        assert "Response from local" in response
        assert "Hello" in response
    
    def test_fallback_on_failure(self):
        """Test fallback when primary client fails."""
        failing_client = MockLLMClient("failing", should_fail=True)
        working_client = MockLLMClient("working")
        
        client = UnifiedLLMClient(
            local_clients=[failing_client, working_client],
            auto_warmup=False
        )
        
        messages = [{"role": "user", "content": "Hello"}]
        response = client.generate(messages)
        
        assert "Response from working" in response
    
    def test_final_fallback(self):
        """Test final fallback when all clients fail."""
        failing_client = MockLLMClient("failing", should_fail=True)
        
        client = UnifiedLLMClient(
            local_clients=[failing_client],
            auto_warmup=False
        )
        
        messages = [{"role": "user", "content": "Hello"}]
        response = client.generate(messages)
        
        assert "fallback mode" in response.lower()
    
    def test_local_only_mode(self):
        """Test local-only mode ignores cloud hints."""
        local_client = MockLLMClient("local")
        remote_client = MockLLMClient("remote")
        
        client = UnifiedLLMClient(
            local_clients=[local_client],
            remote_client=remote_client,
            local_only=True,
            auto_warmup=False
        )
        
        messages = [{"role": "user", "content": "Hello"}]
        response = client.generate(messages, cloud_hint=True)
        
        assert "Response from local" in response
    
    def test_cloud_routing_when_enabled(self):
        """Test cloud routing when local_only=False."""
        local_client = MockLLMClient("local")
        remote_client = MockLLMClient("remote")
        
        client = UnifiedLLMClient(
            local_clients=[local_client],
            remote_client=remote_client,
            local_only=False,
            auto_warmup=False
        )
        
        messages = [{"role": "user", "content": "Hello"}]
        response = client.generate(
            messages, 
            intent="code_optimization", 
            cloud_hint=True
        )
        
        # Should use remote for complex intent
        assert "Response from remote" in response
    
    def test_get_available_models(self):
        """Test getting available models info."""
        local_client = MockLLMClient("local")
        remote_client = MockLLMClient("remote")
        
        client = UnifiedLLMClient(
            local_clients=[local_client],
            remote_client=remote_client,
            local_only=False,
            auto_warmup=False
        )
        
        models = client.get_available_models()
        
        assert "local" in models
        assert "remote" in models
        assert "fallback" in models
        assert models["fallback"] is True
        assert len(models["local"]) == 1
        assert models["local"][0]["type"] == "MockLLMClient"
    
    def test_legacy_generate_method(self):
        """Test backward compatibility with legacy generate method."""
        local_client = MockLLMClient("local")
        
        client = UnifiedLLMClient(
            local_clients=[local_client],
            auto_warmup=False
        )
        
        response = client.generate_legacy("Hello world")
        assert "Response from local" in response
        assert "Hello world" in response


class TestTinyLlamaClient:
    """Test TinyLLaMA client (mocked)."""
    
    @patch('llama_cpp.Llama')
    def test_model_loading(self, mock_llama):
        """Test TinyLLaMA model loading."""
        mock_model = Mock()
        mock_llama.return_value = mock_model
        
        with patch.object(TinyLlamaClient, '_find_tinyllama_model', return_value='test_model.gguf'):
            client = TinyLlamaClient()
            client._load_model()
            
            assert client.model == mock_model
            mock_llama.assert_called_once()
    
    def test_messages_to_prompt(self):
        """Test message to prompt conversion."""
        with patch.object(TinyLlamaClient, '_find_tinyllama_model', return_value='test_model.gguf'):
            client = TinyLlamaClient()
            
            messages = [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
                {"role": "user", "content": "How are you?"}
            ]
            
            prompt = client._messages_to_prompt(messages)
            
            assert "<|im_start|>system" in prompt
            assert "<|im_start|>user" in prompt
            assert "<|im_start|>assistant" in prompt
            assert "You are helpful" in prompt
            assert "Hello" in prompt
            assert "How are you?" in prompt


class TestOllamaClient:
    """Test Ollama client (mocked)."""
    
    @patch('ollama.Client')
    def test_client_creation(self, mock_ollama_client):
        """Test Ollama client creation."""
        mock_client = Mock()
        mock_ollama_client.return_value = mock_client
        
        client = OllamaClient()
        ollama_client = client._get_client()
        
        assert ollama_client == mock_client
        mock_ollama_client.assert_called_once_with(host="http://localhost:11434")
    
    def test_messages_to_prompt(self):
        """Test message to prompt conversion."""
        client = OllamaClient()
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]
        
        prompt = client._messages_to_prompt(messages)
        
        assert "System: You are helpful" in prompt
        assert "User: Hello" in prompt
        assert "Assistant:" in prompt


class TestFactoryFunctions:
    """Test factory functions."""
    
    @patch.object(TinyLlamaClient, '__init__', return_value=None)
    @patch.object(OllamaClient, '__init__', return_value=None)
    def test_create_local_first_client(self, mock_ollama, mock_tinyllama):
        """Test creating local-first client."""
        with patch.object(TinyLlamaClient, '_find_tinyllama_model', return_value='test.gguf'):
            client = create_local_first_client(local_only=True)
            
            assert isinstance(client, UnifiedLLMClient)
            assert client.local_only is True
    
    def test_create_local_only_client(self):
        """Test creating local-only client."""
        with patch('src.core.response.unified_client.TinyLlamaClient') as mock_tiny:
            with patch('src.core.response.unified_client.OllamaClient') as mock_ollama:
                mock_tiny.side_effect = Exception("No model")
                mock_ollama.side_effect = Exception("No ollama")
                
                client = create_local_only_client()
                
                assert isinstance(client, UnifiedLLMClient)
                assert client.local_only is True


if __name__ == "__main__":
    pytest.main([__file__])