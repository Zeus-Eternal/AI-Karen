"""
Capability-Aware Provider Selection Algorithm
- Intelligent matching of required capabilities to available providers
- Performance-based ranking with fallback considerations
- Context-aware selection based on network conditions
- Cost optimization through smart provider choice
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from collections import defaultdict

from .intelligent_provider_registry import (
    IntelligentProviderRegistry,
    ProviderType,
    ProviderPriority,
    ProviderMetrics,
    IntelligentProviderRegistration,
    CapabilityMatcher,
    get_intelligent_provider_registry
)
from ..monitoring.network_connectivity import NetworkStatus, get_network_monitor

logger = logging.getLogger(__name__)


class SelectionStrategy(Enum):
    """Provider selection strategies"""
    CAPABILITY_FIRST = auto()  # Prioritize capability match
    PERFORMANCE_FIRST = auto()  # Prioritize performance
    COST_FIRST = auto()  # Prioritize cost efficiency
    RELIABILITY_FIRST = auto()  # Prioritize reliability
    LOCAL_FIRST = auto()  # Prioritize local providers
    ADAPTIVE = auto()  # Adaptive based on context


class RequestContext(Enum):
    """Request context types for selection optimization"""
    REALTIME = auto()  # Real-time response needed
    BATCH = auto()  # Batch processing
    CREATIVE = auto()  # Creative/generative tasks
    ANALYTICAL = auto()  # Analysis/reasoning tasks
    CODE = auto()  # Code generation/assistance
    CONVERSATION = auto()  # Chat/conversation
    EMBEDDING = auto()  # Embedding generation


@dataclass
class CapabilityRequirement:
    """Detailed capability requirement specification"""
    name: str
    priority: float = 1.0  # 1.0 = critical, 0.5 = nice-to-have
    min_quality: float = 0.7  # Minimum quality threshold (0-1)
    preferred_providers: List[str] = field(default_factory=list)
    excluded_providers: List[str] = field(default_factory=list)
    max_latency: Optional[float] = None
    max_cost: Optional[float] = None


@dataclass
class SelectionCriteria:
    """Criteria for provider selection"""
    required_capabilities: List[CapabilityRequirement]
    context: RequestContext = RequestContext.REALTIME
    strategy: SelectionStrategy = SelectionStrategy.ADAPTIVE
    network_preference: str = "auto"  # auto, online, offline
    cost_sensitivity: float = 0.5  # 0 = cost insensitive, 1 = cost sensitive
    performance_weight: float = 0.5  # Weight for performance in scoring
    reliability_weight: float = 0.5  # Weight for reliability in scoring
    local_preference: float = 0.5  # Preference for local providers
    excluded_providers: List[str] = field(default_factory=list)


@dataclass
class ProviderScore:
    """Score breakdown for a provider"""
    provider_name: str
    total_score: float
    capability_score: float
    performance_score: float
    cost_score: float
    reliability_score: float
    network_score: float
    context_score: float
    breakdown: Dict[str, float] = field(default_factory=dict)


class CapabilityAwareSelector:
    """Intelligent provider selection based on capabilities and context"""
    
    def __init__(self, registry: Optional[IntelligentProviderRegistry] = None):
        self.registry = registry or get_intelligent_provider_registry()
        self.network_monitor = get_network_monitor()
        self.capability_matcher = CapabilityMatcher()
        
        # Selection history for learning
        self.selection_history: List[Dict[str, Any]] = []
        self.max_history_size = 500
        
        # Performance weights for different contexts
        self.context_weights = {
            RequestContext.REALTIME: {
                'performance': 0.8,
                'reliability': 0.6,
                'capability': 0.4,
                'cost': 0.2
            },
            RequestContext.BATCH: {
                'performance': 0.3,
                'reliability': 0.7,
                'capability': 0.6,
                'cost': 0.8
            },
            RequestContext.CREATIVE: {
                'performance': 0.4,
                'reliability': 0.5,
                'capability': 0.8,
                'cost': 0.3
            },
            RequestContext.ANALYTICAL: {
                'performance': 0.6,
                'reliability': 0.8,
                'capability': 0.7,
                'cost': 0.4
            },
            RequestContext.CODE: {
                'performance': 0.7,
                'reliability': 0.6,
                'capability': 0.8,
                'cost': 0.3
            },
            RequestContext.CONVERSATION: {
                'performance': 0.5,
                'reliability': 0.7,
                'capability': 0.6,
                'cost': 0.5
            },
            RequestContext.EMBEDDING: {
                'performance': 0.6,
                'reliability': 0.8,
                'capability': 0.9,
                'cost': 0.7
            }
        }
    
    def select_provider(
        self,
        criteria: SelectionCriteria
    ) -> Tuple[Optional[str], Optional[ProviderScore]]:
        """Select best provider based on criteria"""
        
        # Get current network status
        network_status = self.network_monitor.get_current_status()
        
        # Get candidate providers
        candidates = self._get_candidate_providers(criteria, network_status)
        
        if not candidates:
            logger.warning("No suitable providers found for criteria")
            return None, None
        
        # Score each candidate
        scored_providers = []
        for provider_name, reg in candidates:
            score = self._score_provider(provider_name, reg, criteria, network_status)
            scored_providers.append((provider_name, score))
        
        # Sort by total score (descending)
        scored_providers.sort(key=lambda x: x[1].total_score, reverse=True)
        
        # Return best provider
        best_provider, best_score = scored_providers[0]
        
        # Record selection for learning
        self._record_selection(best_provider, best_score, criteria)
        
        logger.info(
            f"Selected provider {best_provider} with score {best_score.total_score:.3f} "
            f"for context {criteria.context.name}"
        )
        
        return best_provider, best_score
    
    def _get_candidate_providers(
        self,
        criteria: SelectionCriteria,
        network_status: NetworkStatus
    ) -> List[Tuple[str, IntelligentProviderRegistration]]:
        """Get list of candidate providers that meet basic criteria"""
        candidates = []
        
        # Get all registered providers
        all_providers = self.registry._registrations
        
        for provider_name, reg in all_providers.items():
            # Check exclusions
            if provider_name in criteria.excluded_providers:
                continue
            
            # Check network compatibility
            if not self._check_network_compatibility(reg, network_status, criteria):
                continue
            
            # Check basic capability match
            provider_capabilities = set()
            for model in reg.base_registration.models:
                provider_capabilities.update(model.capabilities)
            
            required_caps = set(req.name for req in criteria.required_capabilities)
            capability_score = self.capability_matcher.calculate_capability_score(
                required_caps, provider_capabilities
            )
            
            # Check minimum capability requirements
            min_quality = min(req.min_quality for req in criteria.required_capabilities)
            if capability_score < min_quality:
                continue
            
            # Check performance constraints
            if not self._check_performance_constraints(reg, criteria):
                continue
            
            candidates.append((provider_name, reg))
        
        return candidates
    
    def _check_network_compatibility(
        self,
        reg: IntelligentProviderRegistration,
        network_status: NetworkStatus,
        criteria: SelectionCriteria
    ) -> bool:
        """Check if provider is compatible with current network status"""
        
        if criteria.network_preference == "offline":
            # Only offline-capable providers
            return not reg.network_dependent or reg.offline_capable
        elif criteria.network_preference == "online":
            # Only network-dependent providers
            return reg.network_dependent
        else:  # auto
            # Prefer local when offline
            if network_status == NetworkStatus.OFFLINE:
                return not reg.network_dependent or reg.offline_capable
            elif network_status == NetworkStatus.DEGRADED:
                # Prefer reliable providers when degraded
                return reg.reliability_score > 0.7 or not reg.network_dependent
            else:
                # All providers are acceptable when online
                return True
    
    def _check_performance_constraints(
        self,
        reg: IntelligentProviderRegistration,
        criteria: SelectionCriteria
    ) -> bool:
        """Check if provider meets performance constraints"""
        
        # Check latency constraints
        max_latency = None
        for req in criteria.required_capabilities:
            if req.max_latency and (max_latency is None or req.max_latency < max_latency):
                max_latency = req.max_latency
        
        if max_latency and reg.metrics.average_latency > max_latency:
            return False
        
        # Check cost constraints
        max_cost = None
        for req in criteria.required_capabilities:
            if req.max_cost and (max_cost is None or req.max_cost < max_cost):
                max_cost = req.max_cost
        
        if max_cost and reg.metrics.cost_per_request > max_cost:
            return False
        
        return True
    
    def _score_provider(
        self,
        provider_name: str,
        reg: IntelligentProviderRegistration,
        criteria: SelectionCriteria,
        network_status: NetworkStatus
    ) -> ProviderScore:
        """Calculate comprehensive score for a provider"""
        
        # Get provider capabilities
        provider_capabilities = set()
        for model in reg.base_registration.models:
            provider_capabilities.update(model.capabilities)
        
        # Calculate individual scores
        capability_score = self._calculate_capability_score(
            provider_name, reg, provider_capabilities, criteria
        )
        
        performance_score = self._calculate_performance_score(reg, criteria)
        cost_score = self._calculate_cost_score(reg, criteria)
        reliability_score = self._calculate_reliability_score(reg, criteria)
        network_score = self._calculate_network_score(reg, network_status, criteria)
        context_score = self._calculate_context_score(reg, criteria)
        
        # Calculate weighted total score based on strategy
        total_score = self._calculate_total_score(
            capability_score, performance_score, cost_score, 
            reliability_score, network_score, context_score, criteria
        )
        
        return ProviderScore(
            provider_name=provider_name,
            total_score=total_score,
            capability_score=capability_score,
            performance_score=performance_score,
            cost_score=cost_score,
            reliability_score=reliability_score,
            network_score=network_score,
            context_score=context_score,
            breakdown={
                'capability': capability_score,
                'performance': performance_score,
                'cost': cost_score,
                'reliability': reliability_score,
                'network': network_score,
                'context': context_score
            }
        )
    
    def _calculate_capability_score(
        self,
        provider_name: str,
        reg: IntelligentProviderRegistration,
        provider_capabilities: Set[str],
        criteria: SelectionCriteria
    ) -> float:
        """Calculate capability match score"""
        
        required_caps = set(req.name for req in criteria.required_capabilities)
        
        # Base capability score
        base_score = self.capability_matcher.calculate_capability_score(
            required_caps, provider_capabilities, reg.capabilities_weight
        )
        
        # Apply priority weighting
        weighted_score = 0.0
        total_weight = 0.0
        
        for req in criteria.required_capabilities:
            weight = req.priority
            total_weight += weight
            
            if req.name in provider_capabilities:
                weighted_score += weight * base_score
            else:
                # Check for similar capabilities
                similar_found = self.capability_matcher._find_similar_capability(
                    req.name, provider_capabilities
                )
                if similar_found:
                    weighted_score += weight * base_score * 0.7
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_performance_score(
        self,
        reg: IntelligentProviderRegistration,
        criteria: SelectionCriteria
    ) -> float:
        """Calculate performance score"""
        
        # Normalize latency (lower is better)
        if reg.metrics.average_latency <= 0:
            latency_score = 1.0
        elif reg.metrics.average_latency <= 1.0:  # < 1 second
            latency_score = 0.9
        elif reg.metrics.average_latency <= 3.0:  # < 3 seconds
            latency_score = 0.7
        elif reg.metrics.average_latency <= 10.0:  # < 10 seconds
            latency_score = 0.5
        else:
            latency_score = 0.2
        
        # Factor in success rate
        success_rate_score = reg.metrics.success_rate
        
        # Combine performance metrics
        return (latency_score * 0.6) + (success_rate_score * 0.4)
    
    def _calculate_cost_score(
        self,
        reg: IntelligentProviderRegistration,
        criteria: SelectionCriteria
    ) -> float:
        """Calculate cost efficiency score"""
        
        # Base cost score from tier
        tier_scores = {
            'free': 1.0,
            'standard': 0.7,
            'premium': 0.4
        }
        base_score = tier_scores.get(reg.cost_tier, 0.5)
        
        # Apply cost sensitivity
        if criteria.cost_sensitivity > 0.7:
            # High cost sensitivity - heavily favor cheaper options
            return base_score * 1.5
        elif criteria.cost_sensitivity < 0.3:
            # Low cost sensitivity - cost less important
            return base_score * 0.7
        else:
            return base_score
    
    def _calculate_reliability_score(
        self,
        reg: IntelligentProviderRegistration,
        criteria: SelectionCriteria
    ) -> float:
        """Calculate reliability score"""
        
        # Base reliability score
        reliability_score = reg.reliability_score
        
        # Factor in recent performance
        if reg.metrics.total_requests > 10:
            # Use recent success rate if enough data
            recent_reliability = reg.metrics.success_rate
            reliability_score = (reliability_score * 0.3) + (recent_reliability * 0.7)
        
        # Penalize providers with consecutive failures
        if reg.metrics.consecutive_failures > 0:
            failure_penalty = min(0.5, reg.metrics.consecutive_failures * 0.1)
            reliability_score -= failure_penalty
        
        return max(0.0, reliability_score)
    
    def _calculate_network_score(
        self,
        reg: IntelligentProviderRegistration,
        network_status: NetworkStatus,
        criteria: SelectionCriteria
    ) -> float:
        """Calculate network compatibility score"""
        
        if network_status == NetworkStatus.ONLINE:
            # All providers work well online
            if reg.provider_type == ProviderType.LOCAL:
                return 0.8  # Slightly prefer local even online
            else:
                return 1.0
        elif network_status == NetworkStatus.DEGRADED:
            # Prefer reliable/local providers when degraded
            if reg.provider_type == ProviderType.LOCAL:
                return 1.0
            elif reg.reliability_score > 0.8:
                return 0.8
            else:
                return 0.4
        elif network_status == NetworkStatus.OFFLINE:
            # Only offline-capable providers work
            if reg.offline_capable:
                return 1.0
            else:
                return 0.0
        else:
            return 0.5
    
    def _calculate_context_score(
        self,
        reg: IntelligentProviderRegistration,
        criteria: SelectionCriteria
    ) -> float:
        """Calculate context-appropriate score"""
        
        # Get weights for this context
        context_weights = self.context_weights.get(criteria.context, {
            'performance': 0.5,
            'reliability': 0.5,
            'capability': 0.5,
            'cost': 0.5
        })
        
        # Apply provider type preferences for context
        context_multiplier = 1.0
        
        if criteria.context == RequestContext.CODE:
            # Prefer providers with code capabilities
            provider_caps = set()
            for model in reg.base_registration.models:
                provider_caps.update(model.capabilities)
            if any(cap in provider_caps for cap in ['code', 'coding', 'programming']):
                context_multiplier *= 1.2
        
        elif criteria.context == RequestContext.EMBEDDING:
            # Prefer embedding-specialized providers
            provider_caps = set()
            for model in reg.base_registration.models:
                provider_caps.update(model.capabilities)
            if 'embeddings' in provider_caps:
                context_multiplier *= 1.3
        
        elif criteria.context == RequestContext.REALTIME:
            # Prefer fast, reliable providers for realtime
            if reg.metrics.average_latency < 2.0 and reg.reliability_score > 0.8:
                context_multiplier *= 1.2
        
        return min(1.0, context_multiplier)
    
    def _calculate_total_score(
        self,
        capability_score: float,
        performance_score: float,
        cost_score: float,
        reliability_score: float,
        network_score: float,
        context_score: float,
        criteria: SelectionCriteria
    ) -> float:
        """Calculate total weighted score based on strategy"""
        
        if criteria.strategy == SelectionStrategy.CAPABILITY_FIRST:
            weights = {'capability': 0.5, 'performance': 0.2, 'cost': 0.1, 'reliability': 0.2}
        elif criteria.strategy == SelectionStrategy.PERFORMANCE_FIRST:
            weights = {'capability': 0.2, 'performance': 0.5, 'cost': 0.1, 'reliability': 0.2}
        elif criteria.strategy == SelectionStrategy.COST_FIRST:
            weights = {'capability': 0.2, 'performance': 0.1, 'cost': 0.5, 'reliability': 0.2}
        elif criteria.strategy == SelectionStrategy.RELIABILITY_FIRST:
            weights = {'capability': 0.2, 'performance': 0.2, 'cost': 0.1, 'reliability': 0.5}
        elif criteria.strategy == SelectionStrategy.LOCAL_FIRST:
            weights = {'capability': 0.3, 'performance': 0.2, 'cost': 0.1, 'reliability': 0.2}
            # Extra weight for local providers
            local_bonus = 0.3 if criteria.local_preference > 0.7 else 0.0
        else:  # ADAPTIVE
            # Use context-specific weights
            context_weights = self.context_weights.get(criteria.context, {
                'performance': 0.5,
                'reliability': 0.5,
                'capability': 0.5,
                'cost': 0.5
            })
            weights = {
                'capability': context_weights['capability'] * 0.4,
                'performance': context_weights['performance'] * 0.3,
                'cost': context_weights['cost'] * 0.1,
                'reliability': context_weights['reliability'] * 0.2
            }
            local_bonus = 0.0
        
        # Calculate weighted score
        total = (
            capability_score * weights.get('capability', 0.25) +
            performance_score * weights.get('performance', 0.25) +
            cost_score * weights.get('cost', 0.25) +
            reliability_score * weights.get('reliability', 0.25)
        )
        
        # Apply network and context multipliers
        total *= network_score * context_score
        
        # Add local preference bonus if applicable
        if 'local_bonus' in locals():
            total += local_bonus
        
        return min(1.0, total)
    
    def _record_selection(
        self,
        provider_name: str,
        score: ProviderScore,
        criteria: SelectionCriteria
    ) -> None:
        """Record selection for learning and analytics"""
        
        record = {
            'timestamp': time.time(),
            'provider': provider_name,
            'score': score.total_score,
            'context': criteria.context.name,
            'strategy': criteria.strategy.name,
            'capability_breakdown': score.breakdown
        }
        
        self.selection_history.append(record)
        
        # Trim history if too large
        if len(self.selection_history) > self.max_history_size:
            self.selection_history = self.selection_history[-self.max_history_size:]
    
    def get_selection_analytics(self) -> Dict[str, Any]:
        """Get analytics about provider selections"""
        
        if not self.selection_history:
            return {}
        
        # Provider usage statistics
        provider_usage = defaultdict(int)
        provider_scores = defaultdict(list)
        
        for record in self.selection_history:
            provider = record['provider']
            provider_usage[provider] += 1
            provider_scores[provider].append(record['score'])
        
        # Calculate statistics
        total_selections = len(self.selection_history)
        analytics = {
            'total_selections': total_selections,
            'provider_usage': dict(provider_usage),
            'provider_success_rates': {},
            'average_scores': {},
            'context_distribution': defaultdict(int),
            'strategy_distribution': defaultdict(int)
        }
        
        # Calculate success rates and average scores per provider
        for provider, scores in provider_scores.items():
            if scores:
                analytics['average_scores'][provider] = sum(scores) / len(scores)
                # Success rate based on scores > 0.5
                success_count = sum(1 for s in scores if s > 0.5)
                analytics['provider_success_rates'][provider] = success_count / len(scores)
        
        # Calculate context and strategy distributions
        for record in self.selection_history:
            analytics['context_distribution'][record['context']] += 1
            analytics['strategy_distribution'][record['strategy']] += 1
        
        return analytics
    
    def reset_analytics(self) -> None:
        """Reset selection analytics"""
        self.selection_history.clear()
        logger.info("Selection analytics reset")


# Global selector instance
_capability_selector: Optional[CapabilityAwareSelector] = None


def get_capability_selector() -> CapabilityAwareSelector:
    """Get global capability selector instance"""
    global _capability_selector
    if _capability_selector is None:
        _capability_selector = CapabilityAwareSelector()
    return _capability_selector


def initialize_capability_selector(
    registry: Optional[IntelligentProviderRegistry] = None
) -> CapabilityAwareSelector:
    """Initialize capability selector with custom registry"""
    global _capability_selector
    _capability_selector = CapabilityAwareSelector(registry)
    return _capability_selector


__all__ = [
    "SelectionStrategy",
    "RequestContext",
    "CapabilityRequirement",
    "SelectionCriteria",
    "ProviderScore",
    "CapabilityAwareSelector",
    "get_capability_selector",
    "initialize_capability_selector",
]