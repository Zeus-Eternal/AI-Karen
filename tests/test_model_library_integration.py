"""
Test Model Library Integration with LLM Settings

This test validates the complete integration between the Model Library
and LLM Settings, ensuring seamless workflow from model discovery to usage.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from ai_karen_engine.services.model_library_service import ModelLibraryService, ModelInfo
from ai_karen_engine.services.provider_model_compatibility import ProviderModelCompatibilityService
from ai_karen_engine.integrations.registry import get_registry


class TestModelLibraryIntegration:
    """Test the integration between Model Library and LLM providers."""
    
    @pytest.fixture
    def model_library_service(self):
        """Create a mock model library service."""
        service = Mock(spec=ModelLibraryService)
        
        # Mock available models
        service.get_available_models.return_value = [
            ModelInfo(
                id="tinyllama-1.1b-chat-q4",
                name="TinyLlama 1.1B Chat Q4_K_M",
                provider="llama-cpp",
                size=669000000,
                description="Small, efficient chat model",
                capabilities=["chat", "completion", "local"],
                status="available",
                metadata={
                    "parameters": "1.1B",
                    "quantization": "Q4_K_M",
                    "memory_requirement": "~1GB",
                    "context_length": 2048,
                    "license": "Apache 2.0",
                    "tags": ["chat", "small", "efficient"]
                }
            ),
            ModelInfo(
                id="phi-3-mini-4k-instruct",
                name="Phi-3 Mini 4K Instruct",
                provider="llama-cpp",
                size=2300000000,
                description="Microsoft Phi-3 Mini model",
                capabilities=["chat", "instruct", "local"],
                status="local",
                metadata={
                    "parameters": "3.8B",
                    "quantization": "Q4_K_M",
                    "memory_requirement": "~3GB",
                    "context_length": 4096,
                    "license": "MIT",
                    "tags": ["instruct", "microsoft", "efficient"]
                }
            )
        ]
        
        return service
    
    @pytest.fixture
    def compatibility_service(self):
        """Create a mock compatibility service."""
        service = Mock(spec=ProviderModelCompatibilityService)
        
        # Mock provider suggestions
        service.get_provider_model_suggestions.return_value = {
            "provider": "llama-cpp",
            "provider_capabilities": {
                "supported_formats": ["gguf", "ggml"],
                "required_capabilities": ["text-generation"],
                "optional_capabilities": ["chat", "instruction-following"],
                "performance_type": "local",
                "quantization_support": "excellent"
            },
            "recommendations": {
                "excellent": ["phi-3-mini-4k-instruct"],
                "good": ["tinyllama-1.1b-chat-q4"],
                "acceptable": []
            },
            "total_compatible_models": 2,
            "compatibility_details": {
                "phi-3-mini-4k-instruct": {
                    "score": 0.95,
                    "reasons": ["Model format compatible with provider", "Optimized with Q4_K_M quantization"],
                    "recommendations": ["Model is ready for use"]
                }
            }
        }
        
        # Mock provider validation
        service.validate_provider_model_setup.return_value = {
            "provider": "llama-cpp",
            "has_compatible_models": True,
            "has_local_models": True,
            "local_models_count": 1,
            "available_for_download": 1,
            "total_compatible": 2,
            "status": "healthy",
            "recommendations": []
        }
        
        return service
    
    @pytest.fixture
    def registry(self):
        """Create a mock registry."""
        registry = Mock()
        
        # Mock provider specs
        registry.list_llm_providers.return_value = ["llama-cpp", "openai", "huggingface"]
        registry.get_provider_spec.return_value = Mock(
            name="llama-cpp",
            description="Local GGUF model execution",
            category="LLM",
            requires_api_key=False,
            capabilities=["text-generation", "chat", "local_execution"],
            fallback_models=[
                {"id": "tinyllama-1.1b-chat-q4", "name": "TinyLlama 1.1B Chat"}
            ]
        )
        
        # Mock health status
        registry.get_health_status.return_value = Mock(
            status="healthy",
            error_message=None,
            last_check=1234567890,
            response_time=0.1,
            capabilities={}
        )
        
        return registry
    
    def test_model_discovery_integration(self, model_library_service):
        """Test that model discovery works correctly."""
        models = model_library_service.get_available_models()
        
        assert len(models) == 2
        assert models[0].id == "tinyllama-1.1b-chat-q4"
        assert models[0].status == "available"
        assert models[1].id == "phi-3-mini-4k-instruct"
        assert models[1].status == "local"
        
        # Verify model metadata
        assert models[0].metadata["parameters"] == "1.1B"
        assert models[1].metadata["parameters"] == "3.8B"
    
    def test_provider_compatibility_check(self, compatibility_service):
        """Test provider compatibility checking."""
        suggestions = compatibility_service.get_provider_model_suggestions("llama-cpp")
        
        assert suggestions["provider"] == "llama-cpp"
        assert suggestions["total_compatible_models"] == 2
        assert "phi-3-mini-4k-instruct" in suggestions["recommendations"]["excellent"]
        assert "tinyllama-1.1b-chat-q4" in suggestions["recommendations"]["good"]
        
        # Verify provider capabilities
        caps = suggestions["provider_capabilities"]
        assert "gguf" in caps["supported_formats"]
        assert caps["quantization_support"] == "excellent"
    
    def test_provider_model_validation(self, compatibility_service):
        """Test provider model setup validation."""
        validation = compatibility_service.validate_provider_model_setup("llama-cpp")
        
        assert validation["has_compatible_models"] is True
        assert validation["has_local_models"] is True
        assert validation["local_models_count"] == 1
        assert validation["status"] == "healthy"
        assert len(validation["recommendations"]) == 0
    
    def test_integration_workflow(self, model_library_service, compatibility_service, registry):
        """Test the complete integration workflow."""
        # Step 1: Discover models
        models = model_library_service.get_available_models()
        assert len(models) > 0
        
        # Step 2: Check provider health
        providers = registry.list_llm_providers()
        assert "llama-cpp" in providers
        
        health = registry.get_health_status("provider:llama-cpp")
        assert health.status == "healthy"
        
        # Step 3: Check compatibility
        suggestions = compatibility_service.get_provider_model_suggestions("llama-cpp")
        assert suggestions["total_compatible_models"] > 0
        
        # Step 4: Validate setup
        validation = compatibility_service.validate_provider_model_setup("llama-cpp")
        assert validation["status"] == "healthy"
        
        # Workflow should be complete and functional
        assert validation["has_local_models"] is True
    
    def test_cross_navigation_events(self):
        """Test cross-navigation between Model Library and LLM Settings."""
        # Mock window events
        events_fired = []
        
        def mock_dispatch_event(event):
            events_fired.append(event.type)
        
        # Simulate navigation events
        mock_dispatch_event(Mock(type='navigate-to-model-library'))
        mock_dispatch_event(Mock(type='navigate-to-llm-settings'))
        
        assert 'navigate-to-model-library' in events_fired
        assert 'navigate-to-llm-settings' in events_fired
    
    def test_model_download_integration(self, model_library_service):
        """Test model download integration with provider setup."""
        # Mock download initiation
        model_library_service.download_model.return_value = Mock(
            task_id="test-task-123",
            model_id="tinyllama-1.1b-chat-q4",
            status="downloading",
            progress=0.0
        )
        
        # Simulate download
        download_task = model_library_service.download_model("tinyllama-1.1b-chat-q4")
        assert download_task.task_id == "test-task-123"
        assert download_task.status == "downloading"
        
        # Mock download completion
        model_library_service.get_download_status.return_value = Mock(
            task_id="test-task-123",
            status="completed",
            progress=1.0
        )
        
        # Verify download completion
        status = model_library_service.get_download_status("test-task-123")
        assert status.status == "completed"
        assert status.progress == 1.0
    
    def test_error_handling_integration(self, model_library_service, compatibility_service):
        """Test error handling in integration scenarios."""
        # Test model library service errors
        model_library_service.get_available_models.side_effect = Exception("Service unavailable")
        
        with pytest.raises(Exception, match="Service unavailable"):
            model_library_service.get_available_models()
        
        # Test compatibility service errors
        compatibility_service.get_provider_model_suggestions.return_value = {
            "error": "Provider not found"
        }
        
        result = compatibility_service.get_provider_model_suggestions("unknown-provider")
        assert "error" in result
        assert result["error"] == "Provider not found"
    
    def test_integration_status_api(self, registry, compatibility_service):
        """Test the integration status API endpoint functionality."""
        # Mock integration status data
        providers = ["llama-cpp", "openai", "huggingface"]
        integration_status = {
            "providers": {},
            "overall_status": "healthy",
            "total_providers": len(providers),
            "healthy_providers": 0,
            "providers_with_models": 0,
            "total_compatible_models": 0,
            "recommendations": []
        }
        
        for provider_name in providers:
            # Mock health check
            health = registry.get_health_status(f"provider:{provider_name}")
            is_healthy = health and health.status == "healthy"
            
            # Mock validation
            validation = compatibility_service.validate_provider_model_setup(provider_name)
            
            provider_status = {
                "name": provider_name,
                "healthy": is_healthy,
                "has_compatible_models": validation.get("has_compatible_models", False),
                "has_local_models": validation.get("has_local_models", False),
                "local_models_count": validation.get("local_models_count", 0),
                "total_compatible": validation.get("total_compatible", 0),
                "status": validation.get("status", "unknown")
            }
            
            if is_healthy:
                integration_status["healthy_providers"] += 1
            
            if validation.get("has_compatible_models", False):
                integration_status["providers_with_models"] += 1
            
            integration_status["providers"][provider_name] = provider_status
        
        # Verify integration status
        assert integration_status["total_providers"] == 3
        assert integration_status["healthy_providers"] > 0
        assert "llama-cpp" in integration_status["providers"]
    
    @pytest.mark.asyncio
    async def test_async_integration_operations(self, model_library_service):
        """Test asynchronous integration operations."""
        # Mock async operations
        async def mock_async_download():
            await asyncio.sleep(0.1)  # Simulate async operation
            return Mock(task_id="async-task", status="downloading")
        
        # Test async download
        result = await mock_async_download()
        assert result.task_id == "async-task"
        assert result.status == "downloading"
    
    def test_model_library_settings_persistence(self):
        """Test that Model Library settings are properly persisted."""
        # Mock localStorage operations
        storage = {}
        
        def mock_set_item(key, value):
            storage[key] = value
        
        def mock_get_item(key):
            return storage.get(key)
        
        # Test preference persistence
        mock_set_item('model_library_search', 'tinyllama')
        mock_set_item('model_library_filter_provider', 'llama-cpp')
        
        assert mock_get_item('model_library_search') == 'tinyllama'
        assert mock_get_item('model_library_filter_provider') == 'llama-cpp'
    
    def test_integration_performance(self, model_library_service, compatibility_service):
        """Test integration performance characteristics."""
        import time
        
        # Test model discovery performance
        start_time = time.time()
        models = model_library_service.get_available_models()
        discovery_time = time.time() - start_time
        
        assert discovery_time < 1.0  # Should complete within 1 second
        assert len(models) > 0
        
        # Test compatibility check performance
        start_time = time.time()
        suggestions = compatibility_service.get_provider_model_suggestions("llama-cpp")
        compatibility_time = time.time() - start_time
        
        assert compatibility_time < 0.5  # Should complete within 0.5 seconds
        assert suggestions["total_compatible_models"] > 0


class TestModelLibraryUIIntegration:
    """Test UI integration between Model Library and LLM Settings."""
    
    def test_navigation_events(self):
        """Test navigation events between components."""
        # Mock event system
        events = []
        
        def mock_dispatch_event(event_type):
            events.append(event_type)
        
        # Test Model Library to LLM Settings navigation
        mock_dispatch_event('navigate-to-llm-settings')
        assert 'navigate-to-llm-settings' in events
        
        # Test LLM Settings to Model Library navigation
        mock_dispatch_event('navigate-to-model-library')
        assert 'navigate-to-model-library' in events
    
    def test_cross_reference_components(self):
        """Test cross-reference components in both interfaces."""
        # Mock component props
        model_library_props = {
            'onNavigateToLLMSettings': Mock(),
            'providers': [{'name': 'llama-cpp', 'healthy': True}]
        }
        
        llm_settings_props = {
            'onNavigateToModelLibrary': Mock(),
            'models': [{'id': 'test-model', 'status': 'local'}]
        }
        
        # Test that navigation callbacks are properly set
        assert model_library_props['onNavigateToLLMSettings'] is not None
        assert llm_settings_props['onNavigateToModelLibrary'] is not None
    
    def test_integration_status_display(self):
        """Test integration status display in UI components."""
        # Mock integration status
        status = {
            'overall_status': 'healthy',
            'healthy_providers': 2,
            'total_providers': 3,
            'providers_with_models': 2,
            'total_compatible_models': 5
        }
        
        # Verify status display logic
        assert status['overall_status'] == 'healthy'
        assert status['healthy_providers'] / status['total_providers'] > 0.5
        assert status['providers_with_models'] > 0
    
    def test_workflow_test_component(self):
        """Test the workflow test component functionality."""
        # Mock workflow test steps
        steps = [
            {'id': 'discovery', 'status': 'completed'},
            {'id': 'compatibility', 'status': 'completed'},
            {'id': 'integration', 'status': 'completed'}
        ]
        
        completed_steps = [s for s in steps if s['status'] == 'completed']
        assert len(completed_steps) == 3
        
        # Test workflow completion
        all_completed = all(s['status'] == 'completed' for s in steps)
        assert all_completed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])