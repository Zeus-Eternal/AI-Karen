"""
Capability-Aware Router for LLM Provider System

This module implements capability-aware routing that checks provider capabilities
before routing requests, implements automatic capability fallback, and validates
capability requirements in routing requests.

Key Features:
- Provider capability checking before routing requests
- Automatic capability fallback (vision → text-only, function calling → regular chat)
- Capability requirement validation in routing requests
- Capability-based provider filtering and selection
- Intelligent capability degradation strategies
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ai_karen_engine.integrations.partial_failure_handler import (
    CapabilityType, CapabilityRequirement, CapabilityFallbackResult,
    get_partial_failure_handler
)

logger = logging.getLogger(__name__)


@dataclass
class CapabilityCheckResult:
    """Result of capability checking for a provider."""
    provider: str
    has_required_capabilities: bool
    missing_capabilities: Set[CapabilityType] = field(default_factory=set)
    available_capabilities: Set[CapabilityType] = field(default_factory=set)
    degradation_options: List[str] = field(default_factory=list)


@dataclass
class RoutingCapabilityRequest:
    """Extended routing request with capability requirements."""
    original_request: Any  # Original RoutingRequest
    capability_requirements: CapabilityRequirement
    allow_capability_degradation: bool = True
    max_degradation_steps: int = 3
    preferred_degradation_order: List[CapabilityType] = field(default_factory=list)


@dataclass
class CapabilityRoutingResult:
    """Result of capability-aware routing."""
    success: bool
    provider: Optional[str] = None
    model: Optional[str] = None
    runtime: Optional[str] = None
    achieved_capabilities: Set[CapabilityType] = field(default_factory=set)
    degraded_capabilities: Set[CapabilityType] = field(default_factory=set)
    routing_reason: Optional[str] = None
    fallback_applied: bool = False
    alternative_options: List[Dict[str, Any]] = field(default_factory=list)


class CapabilityRouter:
    """
    Capability-aware router that ensures requests are routed to providers
    with the required capabilities, with intelligent fallback and degradation.
    """
    
    def __init__(self, registry=None, base_router=None):
        """
        Initialize the capability router.
        
        Args:
            registry: LLM registry instance
            base_router: Base router for standard routing logic
        """
        from ai_karen_engine.integrations.registry import get_registry
        self.registry = registry or get_registry()
        self.base_router = base_router
        self.partial_failure_handler = get_partial_failure_handler(registry=self.registry)
        
        # Capability mappings and caches
        self.provider_capability_cache: Dict[str, Set[CapabilityType]] = {}
        self.model_capability_cache: Dict[str, Set[CapabilityType]] = {}
        
        # Degradation strategies
        self.degradation_strategies = self._initialize_degradation_strategies()
        
        logger.info("Capability router initialized")
    
    def route_with_capabilities(self, request: RoutingCapabilityRequest) -> CapabilityRoutingResult:
        """
        Route a request with capability awareness and fallback.
        
        Args:
            request: Routing request with capability requirements
            
        Returns:
            CapabilityRoutingResult with routing decision and capability information
        """
        logger.info(f"Starting capability-aware routing with requirements: {request.capability_requirements.required}")
        
        # Step 1: Check if any providers have the required capabilities
        capable_providers = self._find_capable_providers(request.capability_requirements)
        
        if capable_providers:
            # Try to route to a provider with full capabilities
            result = self._route_to_capable_provider(request, capable_providers)
            if result.success:
                logger.info(f"Successfully routed to {result.provider} with full capabilities")
                return result
        
        # Step 2: Attempt capability degradation if allowed
        if request.allow_capability_degradation:
            logger.info("Attempting capability degradation routing")
            degradation_result = self._attempt_capability_degradation(request)
            if degradation_result.success:
                logger.info(f"Successfully routed with capability degradation: {degradation_result.degraded_capabilities}")
                return degradation_result
        
        # Step 3: No viable routing found
        logger.warning("No viable capability-aware routing found")
        return CapabilityRoutingResult(
            success=False,
            routing_reason="No providers available with required or degraded capabilities",
            alternative_options=self._generate_alternative_options(request)
        )
    
    def check_provider_capabilities(self, provider: str, requirements: CapabilityRequirement) -> CapabilityCheckResult:
        """
        Check if a provider meets the capability requirements.
        
        Args:
            provider: Name of the provider to check
            requirements: Capability requirements to check against
            
        Returns:
            CapabilityCheckResult with detailed capability information
        """
        provider_capabilities = self._get_provider_capabilities(provider)
        
        missing_capabilities = requirements.required - provider_capabilities
        has_required = len(missing_capabilities) == 0
        
        # Generate degradation options if capabilities are missing
        degradation_options = []
        if missing_capabilities:
            for missing_cap in missing_capabilities:
                if missing_cap in self.degradation_strategies:
                    degradation_options.extend(self.degradation_strategies[missing_cap])
        
        return CapabilityCheckResult(
            provider=provider,
            has_required_capabilities=has_required,
            missing_capabilities=missing_capabilities,
            available_capabilities=provider_capabilities,
            degradation_options=degradation_options
        )
    
    def validate_capability_requirements(self, requirements: CapabilityRequirement) -> Dict[str, Any]:
        """
        Validate capability requirements against available providers.
        
        Args:
            requirements: Capability requirements to validate
            
        Returns:
            Dictionary with validation results and recommendations
        """
        validation_result = {
            "valid": False,
            "capable_providers": [],
            "missing_capabilities": set(),
            "degradation_options": [],
            "recommendations": []
        }
        
        # Check all available providers
        available_providers = self.registry.list_providers(healthy_only=True)
        capable_providers = []
        all_missing_caps = set()
        
        for provider in available_providers:
            if self.partial_failure_handler.is_provider_isolated(provider):
                continue
                
            check_result = self.check_provider_capabilities(provider, requirements)
            if check_result.has_required_capabilities:
                capable_providers.append(provider)
            else:
                all_missing_caps.update(check_result.missing_capabilities)
        
        validation_result["capable_providers"] = capable_providers
        validation_result["valid"] = len(capable_providers) > 0
        
        if not validation_result["valid"]:
            validation_result["missing_capabilities"] = all_missing_caps
            
            # Generate degradation options
            degradation_options = []
            for missing_cap in all_missing_caps:
                if missing_cap in self.degradation_strategies:
                    degradation_options.extend(self.degradation_strategies[missing_cap])
            validation_result["degradation_options"] = list(set(degradation_options))
            
            # Generate recommendations
            recommendations = []
            if CapabilityType.STREAMING in all_missing_caps:
                recommendations.append("Consider using non-streaming responses for better provider compatibility")
            if CapabilityType.FUNCTION_CALLING in all_missing_caps:
                recommendations.append("Consider using text-only responses instead of function calling")
            if CapabilityType.VISION in all_missing_caps:
                recommendations.append("Consider processing images separately and using text-only models")
            
            validation_result["recommendations"] = recommendations
        
        return validation_result
    
    def get_capability_alternatives(self, original_requirements: CapabilityRequirement) -> List[CapabilityRequirement]:
        """
        Generate alternative capability requirements through degradation.
        
        Args:
            original_requirements: Original capability requirements
            
        Returns:
            List of alternative capability requirements in order of preference
        """
        alternatives = []
        
        # Generate alternatives by removing capabilities one by one
        for capability in original_requirements.required:
            if capability in self.degradation_strategies:
                alternative = CapabilityRequirement(
                    required=original_requirements.required - {capability},
                    preferred=original_requirements.preferred,
                    fallback_acceptable=original_requirements.fallback_acceptable | {capability}
                )
                alternatives.append(alternative)
        
        # Generate alternatives by removing multiple capabilities
        if len(original_requirements.required) > 1:
            # Remove streaming and function calling together (common degradation)
            if {CapabilityType.STREAMING, CapabilityType.FUNCTION_CALLING}.issubset(original_requirements.required):
                alternative = CapabilityRequirement(
                    required=original_requirements.required - {CapabilityType.STREAMING, CapabilityType.FUNCTION_CALLING},
                    preferred=original_requirements.preferred,
                    fallback_acceptable=original_requirements.fallback_acceptable | {CapabilityType.STREAMING, CapabilityType.FUNCTION_CALLING}
                )
                alternatives.append(alternative)
            
            # Remove all advanced capabilities, keep only basic ones
            basic_capabilities = {CapabilityType.STREAMING}  # Only keep basic streaming
            advanced_capabilities = original_requirements.required - basic_capabilities
            if advanced_capabilities:
                alternative = CapabilityRequirement(
                    required=original_requirements.required.intersection(basic_capabilities),
                    preferred=original_requirements.preferred,
                    fallback_acceptable=original_requirements.fallback_acceptable | advanced_capabilities
                )
                alternatives.append(alternative)
        
        return alternatives
    
    def _find_capable_providers(self, requirements: CapabilityRequirement) -> List[str]:
        """Find providers that meet the capability requirements."""
        available_providers = self.partial_failure_handler.get_available_providers(
            capability_requirements=requirements,
            exclude_isolated=True
        )
        
        capable_providers = []
        for provider in available_providers:
            check_result = self.check_provider_capabilities(provider, requirements)
            if check_result.has_required_capabilities:
                capable_providers.append(provider)
        
        return capable_providers
    
    def _route_to_capable_provider(self, request: RoutingCapabilityRequest, 
                                 capable_providers: List[str]) -> CapabilityRoutingResult:
        """Route to a provider from the list of capable providers."""
        # Use the base router if available, otherwise select the first capable provider
        if self.base_router and hasattr(self.base_router, 'route'):
            try:
                # Create a modified request with only capable providers
                modified_request = request.original_request
                
                # Try routing with the base router
                for provider in capable_providers:
                    try:
                        # Temporarily modify preferred provider to test routing
                        original_preferred = getattr(modified_request, 'preferred_provider', None)
                        modified_request.preferred_provider = provider
                        
                        route_decision = self.base_router.route(modified_request)
                        
                        # Restore original preference
                        modified_request.preferred_provider = original_preferred
                        
                        if route_decision and route_decision.get('provider') == provider:
                            return CapabilityRoutingResult(
                                success=True,
                                provider=route_decision['provider'],
                                model=route_decision.get('model_id'),
                                runtime=route_decision.get('runtime'),
                                achieved_capabilities=request.capability_requirements.required,
                                routing_reason=f"Routed to capable provider via base router: {route_decision.get('reason', '')}"
                            )
                    except Exception as e:
                        logger.debug(f"Base router failed for provider {provider}: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Base router integration failed: {e}")
        
        # Fallback to simple provider selection
        if capable_providers:
            selected_provider = capable_providers[0]  # Simple selection, could be enhanced
            
            # Try to get a model for this provider
            try:
                models = self.registry.list_models(provider=selected_provider)
                selected_model = models[0].id if models else None
            except Exception:
                selected_model = None
            
            return CapabilityRoutingResult(
                success=True,
                provider=selected_provider,
                model=selected_model,
                achieved_capabilities=request.capability_requirements.required,
                routing_reason=f"Selected first capable provider: {selected_provider}"
            )
        
        return CapabilityRoutingResult(success=False, routing_reason="No capable providers available")
    
    def _attempt_capability_degradation(self, request: RoutingCapabilityRequest) -> CapabilityRoutingResult:
        """Attempt to route with capability degradation."""
        alternatives = self.get_capability_alternatives(request.capability_requirements)
        
        for i, alternative in enumerate(alternatives[:request.max_degradation_steps]):
            logger.debug(f"Trying degradation step {i+1}: {alternative.required}")
            
            capable_providers = self._find_capable_providers(alternative)
            if capable_providers:
                # Create a new request with degraded requirements
                degraded_request = RoutingCapabilityRequest(
                    original_request=request.original_request,
                    capability_requirements=alternative,
                    allow_capability_degradation=False  # Prevent recursive degradation
                )
                
                result = self._route_to_capable_provider(degraded_request, capable_providers)
                if result.success:
                    # Calculate what capabilities were degraded
                    degraded_caps = request.capability_requirements.required - alternative.required
                    
                    result.degraded_capabilities = degraded_caps
                    result.fallback_applied = True
                    result.routing_reason = f"Capability degradation applied: removed {degraded_caps}"
                    
                    return result
        
        return CapabilityRoutingResult(
            success=False,
            routing_reason="No viable providers found even with capability degradation"
        )
    
    def _get_provider_capabilities(self, provider: str) -> Set[CapabilityType]:
        """Get capabilities for a provider with caching."""
        if provider in self.provider_capability_cache:
            return self.provider_capability_cache[provider]
        
        # Use the partial failure handler to get capabilities
        capabilities = self.partial_failure_handler._get_provider_capabilities(provider)
        self.provider_capability_cache[provider] = capabilities
        return capabilities
    
    def _initialize_degradation_strategies(self) -> Dict[CapabilityType, List[str]]:
        """Initialize capability degradation strategies."""
        return {
            CapabilityType.STREAMING: [
                "Use non-streaming response with periodic updates",
                "Buffer response and return complete result",
                "Use polling mechanism for progress updates"
            ],
            CapabilityType.FUNCTION_CALLING: [
                "Convert function calls to text instructions",
                "Use structured text output instead of function calls",
                "Provide function call suggestions in response text"
            ],
            CapabilityType.VISION: [
                "Process images separately and provide text descriptions",
                "Use text-only model with image description input",
                "Convert visual content to textual representation"
            ],
            CapabilityType.MULTIMODAL: [
                "Process each modality separately",
                "Convert non-text modalities to text descriptions",
                "Use text-only processing with modality descriptions"
            ],
            CapabilityType.CODE_GENERATION: [
                "Use general text generation with code formatting",
                "Provide code suggestions in natural language",
                "Use template-based code generation"
            ],
            CapabilityType.REASONING: [
                "Use step-by-step text explanation",
                "Break down complex reasoning into simple steps",
                "Use chain-of-thought prompting"
            ]
        }
    
    def _generate_alternative_options(self, request: RoutingCapabilityRequest) -> List[Dict[str, Any]]:
        """Generate alternative routing options for failed requests."""
        alternatives = []
        
        # Get all available providers and their capabilities
        available_providers = self.registry.list_providers(healthy_only=True)
        
        for provider in available_providers:
            if self.partial_failure_handler.is_provider_isolated(provider):
                continue
            
            provider_caps = self._get_provider_capabilities(provider)
            missing_caps = request.capability_requirements.required - provider_caps
            
            if missing_caps:
                # This provider is missing some capabilities
                degradation_suggestions = []
                for missing_cap in missing_caps:
                    if missing_cap in self.degradation_strategies:
                        degradation_suggestions.extend(self.degradation_strategies[missing_cap][:1])  # Take first suggestion
                
                alternatives.append({
                    "provider": provider,
                    "available_capabilities": list(provider_caps),
                    "missing_capabilities": list(missing_caps),
                    "degradation_suggestions": degradation_suggestions
                })
        
        return alternatives


# Global instance
_capability_router = None


def get_capability_router(registry=None, base_router=None) -> CapabilityRouter:
    """Get the global capability router instance."""
    global _capability_router
    if _capability_router is None:
        _capability_router = CapabilityRouter(registry=registry, base_router=base_router)
    return _capability_router