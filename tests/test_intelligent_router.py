"""
Tests for the Intelligent LLM Router

This module tests the intelligent routing system including policy-based selection,
health monitoring integration, and degraded mode fallback.
"""

import pytest
from unittest.mock import Mock, patch

from ai_karen_engine.integrations.llm_router import (
    IntelligentLLMRouter,
    RoutingRequest,
    RouteDecision,
    RoutingPolicy,
    TaskType,
    PrivacyLevel,
    PerformanceRequirement,
    _get_default_routing_policy,
)
from ai_karen_engine.integrations.registry import ProviderSpec, RuntimeSpec, ModelMetadata


class TestIntelligentLLMRouter:
    """Test cases for the IntelligentLLMRouter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock registry
        self.mock_registry = Mock()
        self.mock_registry.get_provider_spec.return_value = ProviderSpec(
            name="test_provider",
            requires_api_key=False,
            capabilities={"streaming", "function_calling"}
        )
        self.mock_registry.get_runtime_spec.return_value = RuntimeSpec(
            name="test_runtime",
            family=["llama"],
            supports=["gguf"],
            priority=50
        )
        self.mock_registry.get_health_status.return_value = None
        self.mock_registry.compatible_runtimes.return_value = ["test_runtime"]
        self.mock_registry.list_providers.return_value = ["test_provider"]
        self.mock_registry.list_runtimes.return_value = ["test_runtime"]
        self.mock_registry._is_compatible.return_value = True
        
        # Create router with mocked dependencies
        self.router = IntelligentLLMRouter(
            registry=self.mock_registry,
            enable_degraded_mode=False,
            enable_health_monitoring=False
        )
    
    def test_default_routing_policy(self):
        """Test that default routing policy is properly configured."""
        policy = _get_default_routing_policy()
        
        assert policy.name == "default"
        assert TaskType.CHAT in policy.task_provider_map
        assert TaskType.CODE in policy.task_runtime_map
        assert PrivacyLevel.PUBLIC in policy.privacy_provider_map
        assert PerformanceRequirement.INTERACTIVE in policy.performance_provider_map
        
        # Check that weights sum to 1.0
        total_weight = (policy.privacy_weight + policy.performance_weight + 
                       policy.cost_weight + policy.availability_weight)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_explicit_preference_routing(self):
        """Test routing with explicit user preferences."""
        request = RoutingRequest(
            prompt="Test prompt",
            preferred_provider="test_provider",
            preferred_model="test_model",
            preferred_runtime="test_runtime"
        )
        
        decision = self.router.route(request)
        
        assert decision["provider"] == "test_provider"
        assert decision["model_id"] == "test_model"
        assert decision["runtime"] == "test_runtime"
        assert decision["confidence"] == 1.0
        assert "Explicit user preference" in decision["reason"]
    
    def test_policy_based_routing(self):
        """Test policy-based routing when no explicit preferences."""
        request = RoutingRequest(
            prompt="Test prompt",
            task_type=TaskType.CHAT,
            privacy_level=PrivacyLevel.PUBLIC,
            performance_req=PerformanceRequirement.INTERACTIVE
        )
        
        # Mock the model selection
        with patch.object(self.router, '_select_model_for_provider', return_value="selected_model"):
            decision = self.router.route(request)
        
        assert decision["provider"] in ["openai", "test_provider"]  # Policy or fallback
        assert decision["model_id"] == "selected_model"
        assert decision["confidence"] > 0.0
        assert "Policy-based selection" in decision["reason"]
    
    def test_privacy_compliance_filtering(self):
        """Test that privacy constraints are properly enforced."""
        request = RoutingRequest(
            prompt="Confidential data",
            privacy_level=PrivacyLevel.CONFIDENTIAL,
            preferred_provider="openai"  # Should be rejected for confidential data
        )
        
        # Should not use OpenAI for confidential data
        decision = self.router.route(request)
        assert decision["provider"] != "openai"
        assert decision["privacy_compliant"] == True
    
    def test_health_based_filtering(self):
        """Test that unhealthy providers are avoided."""
        # Mock unhealthy provider for specific provider
        def mock_health_status(component):
            if component == "provider:test_provider":
                return Mock(status="unhealthy")
            return None
        
        self.mock_registry.get_health_status.side_effect = mock_health_status
        
        # Mock healthy alternatives
        self.mock_registry.list_providers.return_value = ["openai", "local"]
        
        request = RoutingRequest(
            prompt="Test prompt",
            preferred_provider="test_provider"
        )
        
        with patch.object(self.router, '_select_model_for_provider', return_value="fallback_model"):
            decision = self.router.route(request)
        
        # Should use a different provider since preferred is unhealthy
        assert decision["provider"] != "test_provider"
    
    def test_dry_run_functionality(self):
        """Test dry-run routing analysis."""
        request = RoutingRequest(
            prompt="Test prompt",
            task_type=TaskType.CODE,
            privacy_level=PrivacyLevel.INTERNAL
        )
        
        dry_run_result = self.router.dry_run(request)
        
        assert "request_summary" in dry_run_result
        assert "routing_steps" in dry_run_result
        assert "available_providers" in dry_run_result
        assert "available_runtimes" in dry_run_result
        assert "policy_analysis" in dry_run_result
        
        # Check request summary
        summary = dry_run_result["request_summary"]
        assert summary["task_type"] == "code"
        assert summary["privacy_level"] == "internal"
    
    def test_routing_statistics(self):
        """Test routing statistics collection."""
        initial_stats = self.router.get_routing_stats()
        assert initial_stats["total_requests"] == 0
        
        request = RoutingRequest(prompt="Test prompt")
        
        with patch.object(self.router, '_select_model_for_provider', return_value="test_model"):
            self.router.route(request)
        
        updated_stats = self.router.get_routing_stats()
        assert updated_stats["total_requests"] == 1
        assert updated_stats["successful_routes"] >= 0
    
    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        request = RoutingRequest(
            prompt="Test prompt",
            task_type=TaskType.CHAT
        )
        
        # Test with matching policy preferences
        confidence = self.router._calculate_confidence(request, "openai", "vllm")
        assert 0.0 <= confidence <= 1.0
        
        # Test with non-matching preferences
        confidence_low = self.router._calculate_confidence(request, "unknown_provider", "unknown_runtime")
        assert confidence_low < confidence
    
    def test_fallback_chain_building(self):
        """Test fallback chain construction."""
        request = RoutingRequest(
            prompt="Test prompt",
            privacy_level=PrivacyLevel.PUBLIC
        )
        
        fallback_chain = self.router._build_fallback_chain(request)
        
        assert isinstance(fallback_chain, list)
        assert len(fallback_chain) > 0
        assert "local" in fallback_chain  # Should always include local as fallback
    
    def test_cost_estimation(self):
        """Test cost estimation for different providers."""
        # Local providers should be free
        cost_local = self.router._estimate_cost("local", "test_model")
        assert cost_local == 0.0
        
        # API providers should have positive cost
        cost_openai = self.router._estimate_cost("openai", "gpt-4o")
        assert cost_openai is None or cost_openai > 0.0
    
    def test_latency_estimation(self):
        """Test latency estimation for different runtimes."""
        latency_vllm = self.router._estimate_latency("test_provider", "vllm")
        latency_llama_cpp = self.router._estimate_latency("test_provider", "llama.cpp")
        
        # vLLM should be faster than llama.cpp for GPU inference
        if latency_vllm and latency_llama_cpp:
            assert latency_vllm < latency_llama_cpp
    
    def test_policy_update(self):
        """Test updating routing policy."""
        original_policy = self.router.policy.name
        
        new_policy = RoutingPolicy(
            name="test_policy",
            description="Test policy"
        )
        
        self.router.update_policy(new_policy)
        assert self.router.policy.name == "test_policy"
        assert self.router.policy.name != original_policy
    
    def test_alternative_generation(self):
        """Test generation of alternative routing options."""
        request = RoutingRequest(
            prompt="Test prompt",
            task_type=TaskType.CHAT
        )
        
        alternatives = self.router._generate_alternatives(request)
        
        assert isinstance(alternatives, list)
        # Should be sorted by confidence
        if len(alternatives) > 1:
            assert alternatives[0]["confidence"] >= alternatives[1]["confidence"]
    
    @patch('ai_karen_engine.integrations.llm_router.get_degraded_mode_manager')
    def test_degraded_mode_fallback(self, mock_degraded_manager):
        """Test fallback to degraded mode when all else fails."""
        # Mock degraded mode manager
        mock_manager = Mock()
        mock_manager.get_status.return_value = Mock(is_active=False)
        mock_manager.activate_degraded_mode.return_value = None
        mock_degraded_manager.return_value = mock_manager
        
        # Create router with degraded mode enabled
        router = IntelligentLLMRouter(
            registry=self.mock_registry,
            enable_degraded_mode=True,
            enable_health_monitoring=False
        )
        router.degraded_mode_manager = mock_manager  # Ensure it's set
        
        # Mock all providers and runtimes as unavailable
        self.mock_registry.list_providers.return_value = []
        self.mock_registry.list_runtimes.return_value = []
        self.mock_registry.get_healthy_providers.return_value = []
        self.mock_registry.get_healthy_runtimes.return_value = []
        
        # Mock model selection to return None (no models available)
        with patch.object(router, '_select_model_for_provider', return_value=None):
            request = RoutingRequest(prompt="Test prompt")
            decision = router.route(request)
        
        assert decision["provider"] == "core_helpers"
        assert decision["runtime"] == "core_helpers"
        assert "degraded mode" in decision["reason"].lower()
        assert decision["confidence"] < 0.5  # Low confidence for degraded mode


class TestRoutingRequest:
    """Test cases for RoutingRequest data model."""
    
    def test_default_values(self):
        """Test default values for RoutingRequest."""
        request = RoutingRequest(prompt="Test")
        
        assert request.task_type == TaskType.CHAT
        assert request.privacy_level == PrivacyLevel.PUBLIC
        assert request.performance_req == PerformanceRequirement.INTERACTIVE
        assert request.requires_streaming == False
        assert request.requires_function_calling == False
        assert request.requires_vision == False
    
    def test_custom_values(self):
        """Test custom values for RoutingRequest."""
        request = RoutingRequest(
            prompt="Code review",
            task_type=TaskType.CODE,
            privacy_level=PrivacyLevel.CONFIDENTIAL,
            performance_req=PerformanceRequirement.BATCH,
            requires_streaming=True,
            preferred_provider="deepseek",
            user_id="test_user"
        )
        
        assert request.task_type == TaskType.CODE
        assert request.privacy_level == PrivacyLevel.CONFIDENTIAL
        assert request.performance_req == PerformanceRequirement.BATCH
        assert request.requires_streaming == True
        assert request.preferred_provider == "deepseek"
        assert request.user_id == "test_user"


class TestRoutingPolicy:
    """Test cases for RoutingPolicy data model."""
    
    def test_policy_creation(self):
        """Test creating a routing policy."""
        policy = RoutingPolicy(
            name="test_policy",
            description="Test policy",
            privacy_weight=0.5,
            performance_weight=0.3,
            cost_weight=0.1,
            availability_weight=0.1
        )
        
        assert policy.name == "test_policy"
        assert policy.privacy_weight == 0.5
        assert policy.performance_weight == 0.3
        
        # Check that weights sum to 1.0
        total = policy.privacy_weight + policy.performance_weight + policy.cost_weight + policy.availability_weight
        assert abs(total - 1.0) < 0.01


if __name__ == "__main__":
    pytest.main([__file__])