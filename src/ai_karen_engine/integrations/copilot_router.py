"""
Copilot LLM Router Enhancement

This module enhances the existing LLM router with copilot-specific routing policies,
including strict local-first routing, privacy-level enforcement, and capability-specific routing.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .llm_router import IntelligentLLMRouter, RoutingRequest, RouteDecision, PrivacyLevel, TaskType, PerformanceRequirement
from ..config.profile_manager import get_profile_manager
from ..services.settings_manager import get_settings_manager

logger = logging.getLogger(__name__)


class CopilotCapability(Enum):
    """Copilot-specific capabilities that influence routing."""
    REVIEW = "copilot.review"
    DEBUG = "copilot.debug"
    REFACTOR = "copilot.refactor"
    GENERATE_TESTS = "copilot.generate_tests"


@dataclass
class CopilotContext:
    """Context information for copilot operations."""
    session_id: str
    user_id: str
    surface: str  # "chat" or "copilot"
    capability: Optional[CopilotCapability] = None
    
    # File context
    selected_files: List[str] = None
    workspace_root: Optional[str] = None
    
    # Privacy and security
    privacy_level: PrivacyLevel = PrivacyLevel.INTERNAL
    allow_cloud_routing: bool = False
    
    # Metadata
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.selected_files is None:
            self.selected_files = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CopilotRoutingPolicy:
    """Policy configuration for copilot routing decisions."""
    
    # Local-first enforcement
    enforce_local_first: bool = True
    cloud_fallback_requires_explicit_consent: bool = True
    
    # Privacy-aware routing constraints
    privacy_level_enforcement: Dict[PrivacyLevel, List[str]] = None
    
    # Capability-specific routing preferences
    capability_routing: Dict[CopilotCapability, Dict[str, Any]] = None
    
    # Provider trust levels
    trusted_providers: List[str] = None
    local_providers: List[str] = None
    
    def __post_init__(self):
        if self.privacy_level_enforcement is None:
            self.privacy_level_enforcement = {
                PrivacyLevel.CONFIDENTIAL: ["local", "ollama"],
                PrivacyLevel.INTERNAL: ["local", "ollama", "huggingface"],
                PrivacyLevel.PUBLIC: ["local", "ollama", "huggingface", "openai_cloud", "deepseek"]
            }
        
        if self.capability_routing is None:
            self.capability_routing = {
                CopilotCapability.REVIEW: {
                    "preferred_providers": ["deepseek", "ollama"],
                    "required_capabilities": ["code_analysis"],
                    "privacy_level": PrivacyLevel.INTERNAL
                },
                CopilotCapability.DEBUG: {
                    "preferred_providers": ["openai_cloud", "ollama"],
                    "required_capabilities": ["reasoning"],
                    "privacy_level": PrivacyLevel.INTERNAL
                },
                CopilotCapability.REFACTOR: {
                    "preferred_providers": ["ollama"],  # Always local for refactoring
                    "privacy_level": PrivacyLevel.CONFIDENTIAL,
                    "force_local": True
                },
                CopilotCapability.GENERATE_TESTS: {
                    "preferred_providers": ["deepseek", "ollama"],
                    "required_capabilities": ["code_generation"],
                    "privacy_level": PrivacyLevel.INTERNAL
                }
            }
        
        if self.trusted_providers is None:
            self.trusted_providers = ["local", "ollama", "huggingface"]
        
        if self.local_providers is None:
            self.local_providers = ["local", "ollama"]


class CopilotLLMRouter(IntelligentLLMRouter):
    """
    Enhanced LLM router with copilot-specific policies and local-first routing.
    
    This router implements:
    - Strict local-first routing with cloud gating
    - Privacy-level enforcement (CONFIDENTIAL → local only)
    - Capability-specific routing preferences
    - Comprehensive error messages with actionable guidance
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.copilot_policy = CopilotRoutingPolicy()
        self.profile_manager = get_profile_manager()
        self.settings_manager = get_settings_manager()
        self.logger = logging.getLogger("kari.copilot_router")
    
    async def route_copilot_request(
        self, 
        request: RoutingRequest,
        context: CopilotContext
    ) -> RouteDecision:
        """
        Route copilot request with enhanced policy enforcement.
        
        Args:
            request: Standard routing request
            context: Copilot-specific context
            
        Returns:
            Routing decision with copilot policy enforcement
        """
        try:
            # Step 1: Apply capability-specific routing
            if context.capability:
                decision = await self._route_by_capability(request, context)
                if decision:
                    return decision
            
            # Step 2: Apply privacy-level enforcement
            decision = await self._route_by_privacy_level(request, context)
            if decision:
                return decision
            
            # Step 3: Local-first routing with cloud gating
            decision = await self._route_local_first(request, context)
            if decision:
                return decision
            
            # Step 4: Degraded mode fallback
            return await self._route_degraded_mode(request, context)
            
        except Exception as e:
            self.logger.error(f"Copilot routing failed: {e}")
            return await self._create_error_decision(request, context, str(e))
    
    async def _route_by_capability(
        self, 
        request: RoutingRequest, 
        context: CopilotContext
    ) -> Optional[RouteDecision]:
        """Route based on copilot capability requirements."""
        if not context.capability:
            return None
        
        capability_config = self.copilot_policy.capability_routing.get(context.capability)
        if not capability_config:
            return None
        
        # Check if capability forces local routing
        if capability_config.get("force_local", False):
            return await self._route_local_only(request, context, f"Capability {context.capability.value} requires local-only routing")
        
        # Get preferred providers for this capability
        preferred_providers = capability_config.get("preferred_providers", [])
        required_capabilities = capability_config.get("required_capabilities", [])
        capability_privacy_level = capability_config.get("privacy_level", PrivacyLevel.INTERNAL)
        
        # Ensure privacy level is at least as restrictive as capability requirement
        effective_privacy_level = self._get_most_restrictive_privacy_level(
            context.privacy_level, 
            capability_privacy_level
        )
        
        # Filter providers by privacy constraints
        allowed_providers = self.copilot_policy.privacy_level_enforcement.get(effective_privacy_level, [])
        viable_providers = [p for p in preferred_providers if p in allowed_providers]
        
        if not viable_providers:
            return await self._route_local_only(
                request, 
                context, 
                f"No providers available for capability {context.capability.value} with privacy level {effective_privacy_level.value}"
            )
        
        # Try each viable provider
        for provider in viable_providers:
            if await self._can_use_provider(provider, context):
                decision = await self._create_provider_decision(
                    provider, 
                    request, 
                    context,
                    f"Capability-based routing for {context.capability.value}"
                )
                if decision:
                    return decision
        
        return None
    
    async def _route_by_privacy_level(
        self, 
        request: RoutingRequest, 
        context: CopilotContext
    ) -> Optional[RouteDecision]:
        """Route based on privacy level constraints."""
        allowed_providers = self.copilot_policy.privacy_level_enforcement.get(context.privacy_level, [])
        
        if not allowed_providers:
            return await self._route_local_only(
                request, 
                context, 
                f"No providers allowed for privacy level {context.privacy_level.value}"
            )
        
        # For CONFIDENTIAL data, only use local providers
        if context.privacy_level == PrivacyLevel.CONFIDENTIAL:
            return await self._route_local_only(
                request, 
                context, 
                "Confidential data requires local-only processing"
            )
        
        # Try providers in order of preference (local first)
        ordered_providers = self._order_providers_by_preference(allowed_providers)
        
        for provider in ordered_providers:
            if await self._can_use_provider(provider, context):
                decision = await self._create_provider_decision(
                    provider, 
                    request, 
                    context,
                    f"Privacy-level routing for {context.privacy_level.value}"
                )
                if decision:
                    return decision
        
        return None
    
    async def _route_local_first(
        self, 
        request: RoutingRequest, 
        context: CopilotContext
    ) -> Optional[RouteDecision]:
        """Implement strict local-first routing with cloud gating."""
        # Step 1: Try local providers first
        for provider in self.copilot_policy.local_providers:
            if await self._can_use_provider(provider, context):
                decision = await self._create_provider_decision(
                    provider, 
                    request, 
                    context,
                    "Local-first routing"
                )
                if decision:
                    return decision
        
        # Step 2: Check if cloud fallback is allowed
        if not await self._can_use_cloud_providers(context):
            return await self._route_local_only(
                request, 
                context, 
                "Cloud providers not available - check feature flags and API keys"
            )
        
        # Step 3: Try cloud providers with explicit consent
        cloud_providers = await self._get_available_cloud_providers(context)
        
        for provider in cloud_providers:
            if await self._can_use_provider(provider, context):
                decision = await self._create_provider_decision(
                    provider, 
                    request, 
                    context,
                    "Cloud fallback routing (local providers unavailable)"
                )
                if decision:
                    return decision
        
        return None
    
    async def _route_local_only(
        self, 
        request: RoutingRequest, 
        context: CopilotContext,
        reason: str
    ) -> RouteDecision:
        """Route to local providers only."""
        for provider in self.copilot_policy.local_providers:
            if await self._can_use_provider(provider, context):
                decision = await self._create_provider_decision(
                    provider, 
                    request, 
                    context,
                    f"Local-only routing: {reason}"
                )
                if decision:
                    return decision
        
        # If no local providers available, return error decision
        return await self._create_error_decision(
            request, 
            context, 
            f"No local providers available. {reason}"
        )
    
    async def _route_degraded_mode(
        self, 
        request: RoutingRequest, 
        context: CopilotContext
    ) -> RouteDecision:
        """Route to degraded mode when all else fails."""
        if self.degraded_mode_manager:
            return RouteDecision(
                provider="core_helpers",
                runtime="core_helpers",
                model_id="degraded_mode",
                reason="Degraded mode - all copilot providers failed",
                confidence=0.1,
                fallback_chain=[],
                estimated_cost=0.0,
                estimated_latency=1.0,
                privacy_compliant=True,
                capabilities=["basic_text"]
            )
        
        return await self._create_error_decision(
            request, 
            context, 
            "All routing options exhausted - no providers available"
        )
    
    async def _can_use_provider(self, provider: str, context: CopilotContext) -> bool:
        """Check if a provider can be used based on health and requirements."""
        # Check provider health
        if not self._is_provider_healthy(provider):
            return False
        
        # Check if provider requires cloud gating
        if provider not in self.copilot_policy.local_providers:
            return await self._can_use_cloud_providers(context)
        
        return True
    
    async def _can_use_cloud_providers(self, context: CopilotContext) -> bool:
        """Check if cloud providers can be used based on gating requirements."""
        # Check explicit context permission
        if not context.allow_cloud_routing:
            return False
        
        # Check feature flag
        if not self.settings_manager.get_feature_flag("copilot_cloud_enabled"):
            return False
        
        # Check API key availability
        if not self.settings_manager.has_secret("COPILOT_API_KEY"):
            return False
        
        # Check active profile permissions
        active_profile = self.profile_manager.get_active_profile()
        if active_profile and not active_profile.can_use_cloud_providers(self.settings_manager):
            return False
        
        return True
    
    async def _get_available_cloud_providers(self, context: CopilotContext) -> List[str]:
        """Get list of available cloud providers based on privacy constraints."""
        allowed_providers = self.copilot_policy.privacy_level_enforcement.get(context.privacy_level, [])
        cloud_providers = [p for p in allowed_providers if p not in self.copilot_policy.local_providers]
        
        # Filter by health
        healthy_cloud_providers = [p for p in cloud_providers if self._is_provider_healthy(p)]
        
        return healthy_cloud_providers
    
    def _order_providers_by_preference(self, providers: List[str]) -> List[str]:
        """Order providers by preference (local first, then by priority)."""
        local_providers = [p for p in providers if p in self.copilot_policy.local_providers]
        trusted_providers = [p for p in providers if p in self.copilot_policy.trusted_providers and p not in local_providers]
        other_providers = [p for p in providers if p not in local_providers and p not in trusted_providers]
        
        return local_providers + trusted_providers + other_providers
    
    def _get_most_restrictive_privacy_level(
        self, 
        level1: PrivacyLevel, 
        level2: PrivacyLevel
    ) -> PrivacyLevel:
        """Get the most restrictive of two privacy levels."""
        privacy_order = [PrivacyLevel.PUBLIC, PrivacyLevel.INTERNAL, PrivacyLevel.CONFIDENTIAL, PrivacyLevel.RESTRICTED]
        
        level1_index = privacy_order.index(level1)
        level2_index = privacy_order.index(level2)
        
        return privacy_order[max(level1_index, level2_index)]
    
    async def _create_provider_decision(
        self, 
        provider: str, 
        request: RoutingRequest, 
        context: CopilotContext,
        reason: str
    ) -> Optional[RouteDecision]:
        """Create a routing decision for a specific provider."""
        try:
            # Get provider spec
            provider_spec = self.registry.get_provider_spec(provider)
            if not provider_spec:
                return None
            
            # Check provider capabilities against request requirements
            if request.requires_streaming and "streaming" not in provider_spec.capabilities:
                return None
            
            if request.requires_function_calling and "function_calling" not in provider_spec.capabilities:
                return None
            
            # Select model for provider
            model_id = await self._select_model_for_provider(provider, request, context)
            if not model_id:
                return None
            
            # Find compatible runtime
            runtime = await self._select_runtime_for_provider(provider, model_id)
            if not runtime:
                return None
            
            # Calculate confidence based on routing method
            confidence = self._calculate_routing_confidence(provider, context)
            
            return RouteDecision(
                provider=provider,
                runtime=runtime,
                model_id=model_id,
                reason=reason,
                confidence=confidence,
                fallback_chain=self._build_fallback_chain(context),
                estimated_cost=self._estimate_cost(provider, model_id),
                estimated_latency=self._estimate_latency(provider, runtime),
                privacy_compliant=self._check_privacy_compliance(provider, context),
                capabilities=list(provider_spec.capabilities)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create provider decision for {provider}: {e}")
            return None
    
    async def _select_model_for_provider(
        self, 
        provider: str, 
        request: RoutingRequest, 
        context: CopilotContext
    ) -> Optional[str]:
        """Select appropriate model for provider based on task and capability."""
        # Get active profile
        active_profile = self.profile_manager.get_active_profile()
        if active_profile:
            # Get models from profile for this task type
            task_type = request.task_type.value if request.task_type else "chat"
            suitable_models = active_profile.get_models_for_task(task_type, context.privacy_level)
            
            # Find model for this provider
            for model_config in suitable_models:
                if model_config.provider == provider:
                    return model_config.model
        
        # Fallback to registry default
        provider_info = self.registry.get_provider_info(provider)
        return provider_info.get("default_model") if provider_info else None
    
    async def _select_runtime_for_provider(self, provider: str, model_id: str) -> Optional[str]:
        """Select appropriate runtime for provider and model."""
        # This would integrate with the existing runtime selection logic
        # For now, return a default based on provider type
        runtime_mapping = {
            "ollama": "ollama",
            "local": "llama.cpp",
            "openai_cloud": "api",
            "deepseek": "api",
            "huggingface": "transformers"
        }
        return runtime_mapping.get(provider, "default")
    
    def _calculate_routing_confidence(self, provider: str, context: CopilotContext) -> float:
        """Calculate confidence score for routing decision."""
        confidence = 0.5  # Base confidence
        
        # Higher confidence for local providers
        if provider in self.copilot_policy.local_providers:
            confidence += 0.3
        
        # Higher confidence for trusted providers
        if provider in self.copilot_policy.trusted_providers:
            confidence += 0.2
        
        # Higher confidence for capability-specific routing
        if context.capability:
            capability_config = self.copilot_policy.capability_routing.get(context.capability)
            if capability_config and provider in capability_config.get("preferred_providers", []):
                confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _check_privacy_compliance(self, provider: str, context: CopilotContext) -> bool:
        """Check if provider is compliant with privacy requirements."""
        allowed_providers = self.copilot_policy.privacy_level_enforcement.get(context.privacy_level, [])
        return provider in allowed_providers
    
    def _build_fallback_chain(self, context: CopilotContext) -> List[str]:
        """Build fallback chain based on context and policies."""
        fallback_chain = []
        
        # Always include local providers in fallback
        fallback_chain.extend(self.copilot_policy.local_providers)
        
        # Add degraded mode as final fallback
        if self.degraded_mode_manager:
            fallback_chain.append("core_helpers")
        
        return fallback_chain
    
    async def _create_error_decision(
        self, 
        request: RoutingRequest, 
        context: CopilotContext, 
        error_message: str
    ) -> RouteDecision:
        """Create an error decision with actionable guidance."""
        # Generate actionable error message
        actionable_message = self._generate_actionable_error_message(error_message, context)
        
        return RouteDecision(
            provider="error",
            runtime="error",
            model_id="error",
            reason=actionable_message,
            confidence=0.0,
            fallback_chain=[],
            estimated_cost=None,
            estimated_latency=None,
            privacy_compliant=True,
            capabilities=[]
        )
    
    def _generate_actionable_error_message(self, error: str, context: CopilotContext) -> str:
        """Generate actionable error message with guidance."""
        base_message = f"Copilot routing failed: {error}"
        
        suggestions = []
        
        # Check common issues and provide suggestions
        if "cloud" in error.lower() and "not available" in error.lower():
            if not self.settings_manager.get_feature_flag("copilot_cloud_enabled"):
                suggestions.append("Enable cloud features: Set 'features.copilot_cloud_enabled' to true")
            
            if not self.settings_manager.has_secret("COPILOT_API_KEY"):
                suggestions.append("Configure API key: Set COPILOT_API_KEY in secret storage")
        
        if "local" in error.lower() and "not available" in error.lower():
            suggestions.append("Check local providers: Ensure Ollama or local LLM services are running")
            suggestions.append("Install local models: Run 'ollama pull llama3.2:latest'")
        
        if context.privacy_level == PrivacyLevel.CONFIDENTIAL:
            suggestions.append("Confidential data requires local providers only")
            suggestions.append("Consider using a less restrictive privacy level if appropriate")
        
        if suggestions:
            base_message += "\n\nSuggestions:\n" + "\n".join(f"- {s}" for s in suggestions)
        
        return base_message


# Global copilot router instance
_copilot_router_instance: Optional[CopilotLLMRouter] = None


def get_copilot_router() -> CopilotLLMRouter:
    """Get global copilot router instance."""
    global _copilot_router_instance
    if _copilot_router_instance is None:
        _copilot_router_instance = CopilotLLMRouter()
    return _copilot_router_instance