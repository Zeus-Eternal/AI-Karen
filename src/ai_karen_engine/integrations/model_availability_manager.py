"""
Model Availability Manager for LLM Provider System

This module implements model-level health checking within providers, model availability
caching, automatic model fallback within providers, and model performance tracking.

Key Features:
- Model-level health checking within providers
- Model availability caching to avoid repeated failed requests
- Automatic model fallback within providers (GPT-4 → GPT-3.5, etc.)
- Model performance tracking and selection optimization
- Intelligent model selection based on availability and performance
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import threading
import asyncio

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Status of a model within a provider."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"
    RATE_LIMITED = "rate_limited"
    MAINTENANCE = "maintenance"


@dataclass
class ModelHealthCheck:
    """Health check result for a specific model."""
    model_id: str
    provider: str
    status: ModelStatus
    last_check: datetime
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    success_rate: float = 1.0
    consecutive_failures: int = 0
    last_successful_request: Optional[datetime] = None
    capabilities_verified: Set[str] = field(default_factory=set)


@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for a model."""
    model_id: str
    provider: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Request type specific metrics
    request_type_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Time-based metrics (last hour, day, week)
    hourly_success_rate: float = 1.0
    daily_success_rate: float = 1.0
    weekly_success_rate: float = 1.0


@dataclass
class ModelFallbackRule:
    """Rule for model fallback within a provider."""
    provider: str
    primary_model: str
    fallback_models: List[str] = field(default_factory=list)
    fallback_conditions: List[str] = field(default_factory=list)  # unavailable, rate_limited, slow_response
    max_fallback_attempts: int = 3
    fallback_delay: float = 1.0
    enabled: bool = True


@dataclass
class ModelSelectionCriteria:
    """Criteria for selecting the best model from available options."""
    prefer_faster_models: bool = True
    prefer_higher_success_rate: bool = True
    max_acceptable_response_time: Optional[float] = None
    min_acceptable_success_rate: float = 0.8
    request_type: Optional[str] = None
    capability_requirements: Set[str] = field(default_factory=set)


class ModelAvailabilityManager:
    """
    Manages model availability, health checking, and intelligent selection
    within providers with performance tracking and fallback mechanisms.
    """
    
    def __init__(self, registry=None, health_check_interval: int = 300,
                 cache_ttl: int = 600, max_concurrent_checks: int = 5):
        """
        Initialize the model availability manager.
        
        Args:
            registry: LLM registry instance
            health_check_interval: Interval in seconds between health checks
            cache_ttl: Time-to-live for availability cache in seconds
            max_concurrent_checks: Maximum concurrent health checks
        """
        from ai_karen_engine.integrations.registry import get_registry
        self.registry = registry or get_registry()
        self.health_check_interval = health_check_interval
        self.cache_ttl = cache_ttl
        self.max_concurrent_checks = max_concurrent_checks
        
        # Model health and availability tracking
        self.model_health: Dict[str, ModelHealthCheck] = {}
        self.model_performance: Dict[str, ModelPerformanceMetrics] = {}
        self.availability_cache: Dict[str, Tuple[bool, datetime]] = {}
        
        # Fallback rules
        self.fallback_rules: Dict[str, ModelFallbackRule] = {}
        self.default_fallback_rules = self._initialize_default_fallback_rules()
        
        # Background monitoring
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        
        # Concurrency control
        self.health_check_semaphore = threading.Semaphore(max_concurrent_checks)
        
        logger.info("Model availability manager initialized")
    
    def start_monitoring(self) -> None:
        """Start background model health monitoring."""
        if self.monitoring_active:
            logger.warning("Model monitoring already active")
            return
        
        self.monitoring_active = True
        self._stop_monitoring.clear()
        
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name="ModelAvailabilityMonitor",
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info("Model availability monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop background model health monitoring."""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        self._stop_monitoring.set()
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        
        logger.info("Model availability monitoring stopped")
    
    def check_model_availability(self, provider: str, model_id: str, 
                                force_check: bool = False) -> ModelHealthCheck:
        """
        Check availability of a specific model within a provider.
        
        Args:
            provider: Name of the provider
            model_id: ID of the model to check
            force_check: Force a fresh check, ignoring cache
            
        Returns:
            ModelHealthCheck with current status
        """
        model_key = f"{provider}:{model_id}"
        
        # Check cache first unless force_check is True
        if not force_check and model_key in self.model_health:
            health_check = self.model_health[model_key]
            cache_age = datetime.now() - health_check.last_check
            if cache_age.total_seconds() < self.cache_ttl:
                logger.debug(f"Using cached health status for {model_key}: {health_check.status}")
                return health_check
        
        # Perform fresh health check
        logger.debug(f"Performing health check for model {model_key}")
        health_check = self._perform_model_health_check(provider, model_id)
        self.model_health[model_key] = health_check
        
        return health_check
    
    def get_available_models(self, provider: str, 
                           selection_criteria: Optional[ModelSelectionCriteria] = None) -> List[str]:
        """
        Get list of available models for a provider, optionally filtered by criteria.
        
        Args:
            provider: Name of the provider
            selection_criteria: Criteria for filtering models
            
        Returns:
            List of available model IDs
        """
        try:
            all_models = self.registry.list_models(provider=provider)
        except Exception as e:
            logger.error(f"Failed to get models for provider {provider}: {e}")
            return []
        
        available_models = []
        
        for model in all_models:
            # Check model availability
            health_check = self.check_model_availability(provider, model.id)
            
            if health_check.status not in [ModelStatus.AVAILABLE, ModelStatus.DEGRADED]:
                logger.debug(f"Skipping unavailable model {model.id}: {health_check.status}")
                continue
            
            # Apply selection criteria if provided
            if selection_criteria and not self._meets_selection_criteria(
                provider, model.id, selection_criteria
            ):
                logger.debug(f"Model {model.id} does not meet selection criteria")
                continue
            
            available_models.append(model.id)
        
        # Sort by preference if criteria provided
        if selection_criteria:
            available_models = self._sort_models_by_preference(provider, available_models, selection_criteria)
        
        return available_models
    
    def select_best_model(self, provider: str, model_options: List[str],
                         selection_criteria: Optional[ModelSelectionCriteria] = None) -> Optional[str]:
        """
        Select the best model from available options based on criteria.
        
        Args:
            provider: Name of the provider
            model_options: List of model IDs to choose from
            selection_criteria: Criteria for selection
            
        Returns:
            ID of the best model, or None if no suitable model found
        """
        if not model_options:
            return None
        
        # Filter available models
        available_models = []
        for model_id in model_options:
            health_check = self.check_model_availability(provider, model_id)
            if health_check.status in [ModelStatus.AVAILABLE, ModelStatus.DEGRADED]:
                available_models.append(model_id)
        
        if not available_models:
            logger.warning(f"No available models from options: {model_options}")
            return None
        
        # Apply selection criteria
        if selection_criteria:
            suitable_models = []
            for model_id in available_models:
                if self._meets_selection_criteria(provider, model_id, selection_criteria):
                    suitable_models.append(model_id)
            
            if suitable_models:
                available_models = suitable_models
            else:
                logger.warning("No models meet selection criteria, using all available models")
        
        # Sort by preference and return the best
        sorted_models = self._sort_models_by_preference(provider, available_models, selection_criteria)
        best_model = sorted_models[0] if sorted_models else None
        
        if best_model:
            logger.info(f"Selected best model for {provider}: {best_model}")
        
        return best_model
    
    def attempt_model_fallback(self, provider: str, failed_model: str,
                              request_type: Optional[str] = None) -> Optional[str]:
        """
        Attempt to find a fallback model when the primary model fails.
        
        Args:
            provider: Name of the provider
            failed_model: Model that failed
            request_type: Type of request for context
            
        Returns:
            ID of fallback model, or None if no suitable fallback found
        """
        logger.info(f"Attempting model fallback for {provider}:{failed_model}")
        
        # Record the failure
        self._record_model_failure(provider, failed_model, request_type)
        
        # Get fallback rule for this model
        fallback_rule = self._get_fallback_rule(provider, failed_model)
        
        if not fallback_rule or not fallback_rule.enabled:
            logger.debug(f"No fallback rule found for {provider}:{failed_model}")
            return None
        
        # Try fallback models in order
        for fallback_model in fallback_rule.fallback_models:
            health_check = self.check_model_availability(provider, fallback_model, force_check=True)
            
            if health_check.status == ModelStatus.AVAILABLE:
                logger.info(f"Found fallback model: {provider}:{fallback_model}")
                return fallback_model
            elif health_check.status == ModelStatus.DEGRADED:
                # Degraded model might still work
                logger.info(f"Using degraded fallback model: {provider}:{fallback_model}")
                return fallback_model
            else:
                logger.debug(f"Fallback model {fallback_model} not available: {health_check.status}")
        
        # No suitable fallback found
        logger.warning(f"No suitable fallback found for {provider}:{failed_model}")
        return None
    
    def record_model_performance(self, provider: str, model_id: str, 
                               response_time: float, success: bool,
                               request_type: Optional[str] = None) -> None:
        """
        Record performance metrics for a model.
        
        Args:
            provider: Name of the provider
            model_id: ID of the model
            response_time: Response time in seconds
            success: Whether the request was successful
            request_type: Type of request for categorized metrics
        """
        model_key = f"{provider}:{model_id}"
        
        if model_key not in self.model_performance:
            self.model_performance[model_key] = ModelPerformanceMetrics(
                model_id=model_id,
                provider=provider
            )
        
        metrics = self.model_performance[model_key]
        
        # Update overall metrics
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        
        # Update response time metrics
        if success and response_time > 0:
            old_avg = metrics.average_response_time
            old_count = metrics.successful_requests - 1
            metrics.average_response_time = (old_avg * old_count + response_time) / metrics.successful_requests
            metrics.min_response_time = min(metrics.min_response_time, response_time)
            metrics.max_response_time = max(metrics.max_response_time, response_time)
        
        # Update request type specific metrics
        if request_type:
            if request_type not in metrics.request_type_metrics:
                metrics.request_type_metrics[request_type] = {
                    "total": 0, "successful": 0, "avg_response_time": 0.0
                }
            
            type_metrics = metrics.request_type_metrics[request_type]
            type_metrics["total"] += 1
            if success:
                type_metrics["successful"] += 1
                if response_time > 0:
                    old_avg = type_metrics["avg_response_time"]
                    old_count = type_metrics["successful"] - 1
                    if old_count > 0:
                        type_metrics["avg_response_time"] = (old_avg * old_count + response_time) / type_metrics["successful"]
                    else:
                        type_metrics["avg_response_time"] = response_time
        
        metrics.last_updated = datetime.now()
        
        # Update model health based on recent performance
        self._update_model_health_from_performance(provider, model_id)
    
    def get_model_performance_report(self, provider: Optional[str] = None,
                                   time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Get performance report for models.
        
        Args:
            provider: Specific provider to report on (None for all)
            time_window: Time window for the report (None for all time)
            
        Returns:
            Dictionary with performance report
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "time_window": str(time_window) if time_window else "all_time",
            "models": {},
            "summary": {
                "total_models": 0,
                "available_models": 0,
                "degraded_models": 0,
                "unavailable_models": 0
            }
        }
        
        cutoff_time = datetime.now() - time_window if time_window else datetime.min
        
        for model_key, metrics in self.model_performance.items():
            model_provider, model_id = model_key.split(":", 1)
            
            # Filter by provider if specified
            if provider and model_provider != provider:
                continue
            
            # Filter by time window
            if metrics.last_updated < cutoff_time:
                continue
            
            # Get current health status
            health_check = self.model_health.get(model_key)
            status = health_check.status.value if health_check else "unknown"
            
            model_report = {
                "provider": model_provider,
                "model_id": model_id,
                "status": status,
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate": metrics.successful_requests / max(metrics.total_requests, 1),
                "average_response_time": metrics.average_response_time,
                "min_response_time": metrics.min_response_time if metrics.min_response_time != float('inf') else None,
                "max_response_time": metrics.max_response_time,
                "last_updated": metrics.last_updated.isoformat(),
                "request_type_metrics": metrics.request_type_metrics
            }
            
            report["models"][model_key] = model_report
            report["summary"]["total_models"] += 1
            
            if status == "available":
                report["summary"]["available_models"] += 1
            elif status == "degraded":
                report["summary"]["degraded_models"] += 1
            else:
                report["summary"]["unavailable_models"] += 1
        
        return report
    
    def add_fallback_rule(self, rule: ModelFallbackRule) -> None:
        """Add a custom fallback rule for a model."""
        rule_key = f"{rule.provider}:{rule.primary_model}"
        self.fallback_rules[rule_key] = rule
        logger.info(f"Added fallback rule for {rule_key}: {rule.fallback_models}")
    
    def _perform_model_health_check(self, provider: str, model_id: str) -> ModelHealthCheck:
        """Perform actual health check for a model."""
        start_time = time.time()
        
        health_check = ModelHealthCheck(
            model_id=model_id,
            provider=provider,
            status=ModelStatus.UNKNOWN,
            last_check=datetime.now()
        )
        
        try:
            # Try to get the provider instance
            provider_instance = self.registry.get_provider_instance(provider)
            if not provider_instance:
                health_check.status = ModelStatus.UNAVAILABLE
                health_check.error_message = "Provider instance not available"
                return health_check
            
            # Check if the model exists in the provider's model list
            try:
                models = self.registry.list_models(provider=provider)
                model_exists = any(m.id == model_id for m in models)
                if not model_exists:
                    health_check.status = ModelStatus.UNAVAILABLE
                    health_check.error_message = "Model not found in provider"
                    return health_check
            except Exception as e:
                logger.debug(f"Could not verify model existence: {e}")
            
            # Perform a lightweight test if the provider supports it
            if hasattr(provider_instance, 'test_model'):
                try:
                    test_result = provider_instance.test_model(model_id)
                    if test_result.get('available', False):
                        health_check.status = ModelStatus.AVAILABLE
                        health_check.response_time = time.time() - start_time
                        health_check.capabilities_verified = set(test_result.get('capabilities', []))
                    else:
                        health_check.status = ModelStatus.UNAVAILABLE
                        health_check.error_message = test_result.get('error', 'Model test failed')
                except Exception as e:
                    health_check.status = ModelStatus.DEGRADED
                    health_check.error_message = f"Model test error: {str(e)}"
            else:
                # Provider doesn't support model testing, assume available if provider is healthy
                provider_health = self.registry.get_health_status(f"provider:{provider}")
                if provider_health and provider_health.status == "healthy":
                    health_check.status = ModelStatus.AVAILABLE
                    health_check.response_time = time.time() - start_time
                else:
                    health_check.status = ModelStatus.DEGRADED
                    health_check.error_message = "Provider health check failed"
        
        except Exception as e:
            health_check.status = ModelStatus.UNAVAILABLE
            health_check.error_message = f"Health check failed: {str(e)}"
            logger.error(f"Model health check failed for {provider}:{model_id}: {e}")
        
        # Update consecutive failure count
        model_key = f"{provider}:{model_id}"
        if model_key in self.model_health:
            previous_health = self.model_health[model_key]
            if health_check.status == ModelStatus.UNAVAILABLE:
                health_check.consecutive_failures = previous_health.consecutive_failures + 1
            else:
                health_check.consecutive_failures = 0
                health_check.last_successful_request = datetime.now()
        
        return health_check
    
    def _meets_selection_criteria(self, provider: str, model_id: str,
                                criteria: ModelSelectionCriteria) -> bool:
        """Check if a model meets the selection criteria."""
        model_key = f"{provider}:{model_id}"
        
        # Check performance metrics if available
        if model_key in self.model_performance:
            metrics = self.model_performance[model_key]
            
            # Check success rate
            success_rate = metrics.successful_requests / max(metrics.total_requests, 1)
            if success_rate < criteria.min_acceptable_success_rate:
                return False
            
            # Check response time
            if (criteria.max_acceptable_response_time and 
                metrics.average_response_time > criteria.max_acceptable_response_time):
                return False
            
            # Check request type specific metrics
            if criteria.request_type and criteria.request_type in metrics.request_type_metrics:
                type_metrics = metrics.request_type_metrics[criteria.request_type]
                type_success_rate = type_metrics["successful"] / max(type_metrics["total"], 1)
                if type_success_rate < criteria.min_acceptable_success_rate:
                    return False
        
        # Check capability requirements
        if criteria.capability_requirements:
            health_check = self.model_health.get(model_key)
            if health_check:
                if not criteria.capability_requirements.issubset(health_check.capabilities_verified):
                    # If capabilities not verified, we can't be sure - allow it for now
                    pass
        
        return True
    
    def _sort_models_by_preference(self, provider: str, models: List[str],
                                 criteria: Optional[ModelSelectionCriteria]) -> List[str]:
        """Sort models by preference based on criteria."""
        if not criteria or len(models) <= 1:
            return models
        
        def model_score(model_id: str) -> float:
            score = 0.0
            model_key = f"{provider}:{model_id}"
            
            # Health status score
            health_check = self.model_health.get(model_key)
            if health_check:
                if health_check.status == ModelStatus.AVAILABLE:
                    score += 10.0
                elif health_check.status == ModelStatus.DEGRADED:
                    score += 5.0
                
                # Penalize consecutive failures
                score -= health_check.consecutive_failures * 2.0
            
            # Performance score
            if model_key in self.model_performance:
                metrics = self.model_performance[model_key]
                
                # Success rate score
                if criteria.prefer_higher_success_rate:
                    success_rate = metrics.successful_requests / max(metrics.total_requests, 1)
                    score += success_rate * 10.0
                
                # Response time score (lower is better)
                if criteria.prefer_faster_models and metrics.average_response_time > 0:
                    # Invert response time for scoring (faster = higher score)
                    score += max(0, 10.0 - metrics.average_response_time)
            
            return score
        
        return sorted(models, key=model_score, reverse=True)
    
    def _get_fallback_rule(self, provider: str, model_id: str) -> Optional[ModelFallbackRule]:
        """Get fallback rule for a model."""
        rule_key = f"{provider}:{model_id}"
        
        # Check custom rules first
        if rule_key in self.fallback_rules:
            return self.fallback_rules[rule_key]
        
        # Check default rules
        if rule_key in self.default_fallback_rules:
            return self.default_fallback_rules[rule_key]
        
        # Generate dynamic fallback rule based on available models
        try:
            all_models = self.registry.list_models(provider=provider)
            other_models = [m.id for m in all_models if m.id != model_id]
            
            if other_models:
                # Sort by preference (smaller models first for fallback)
                other_models.sort(key=lambda m: self._get_model_size_priority(m))
                
                return ModelFallbackRule(
                    provider=provider,
                    primary_model=model_id,
                    fallback_models=other_models[:3],  # Limit to top 3 fallbacks
                    fallback_conditions=["unavailable", "rate_limited"],
                    enabled=True
                )
        except Exception as e:
            logger.debug(f"Could not generate dynamic fallback rule for {rule_key}: {e}")
        
        return None
    
    def _initialize_default_fallback_rules(self) -> Dict[str, ModelFallbackRule]:
        """Initialize default fallback rules for common models."""
        rules = {}
        
        # OpenAI fallback rules
        rules["openai:gpt-4"] = ModelFallbackRule(
            provider="openai",
            primary_model="gpt-4",
            fallback_models=["gpt-4-turbo", "gpt-3.5-turbo"],
            fallback_conditions=["unavailable", "rate_limited", "slow_response"]
        )
        
        rules["openai:gpt-4-turbo"] = ModelFallbackRule(
            provider="openai",
            primary_model="gpt-4-turbo",
            fallback_models=["gpt-3.5-turbo", "gpt-3.5-turbo-16k"],
            fallback_conditions=["unavailable", "rate_limited"]
        )
        
        # Gemini fallback rules
        rules["gemini:gemini-pro"] = ModelFallbackRule(
            provider="gemini",
            primary_model="gemini-pro",
            fallback_models=["gemini-pro-vision", "gemini-1.5-flash"],
            fallback_conditions=["unavailable", "rate_limited"]
        )
        
        # DeepSeek fallback rules
        rules["deepseek:deepseek-coder"] = ModelFallbackRule(
            provider="deepseek",
            primary_model="deepseek-coder",
            fallback_models=["deepseek-chat"],
            fallback_conditions=["unavailable", "rate_limited"]
        )
        
        return rules
    
    def _record_model_failure(self, provider: str, model_id: str, request_type: Optional[str]) -> None:
        """Record a model failure for tracking."""
        model_key = f"{provider}:{model_id}"
        
        # Update health check
        if model_key in self.model_health:
            health_check = self.model_health[model_key]
            health_check.consecutive_failures += 1
            health_check.status = ModelStatus.UNAVAILABLE
            health_check.last_check = datetime.now()
        
        # Update performance metrics
        if model_key in self.model_performance:
            metrics = self.model_performance[model_key]
            metrics.failed_requests += 1
            metrics.total_requests += 1
            metrics.last_updated = datetime.now()
    
    def _update_model_health_from_performance(self, provider: str, model_id: str) -> None:
        """Update model health status based on recent performance."""
        model_key = f"{provider}:{model_id}"
        
        if model_key not in self.model_performance:
            return
        
        metrics = self.model_performance[model_key]
        
        # Calculate recent success rate (last 10 requests)
        recent_success_rate = metrics.successful_requests / max(metrics.total_requests, 1)
        
        # Update health status based on performance
        if model_key in self.model_health:
            health_check = self.model_health[model_key]
            
            if recent_success_rate >= 0.9:
                health_check.status = ModelStatus.AVAILABLE
            elif recent_success_rate >= 0.5:
                health_check.status = ModelStatus.DEGRADED
            else:
                health_check.status = ModelStatus.UNAVAILABLE
            
            health_check.success_rate = recent_success_rate
    
    def _get_model_size_priority(self, model_id: str) -> int:
        """Get priority for model ordering (lower number = higher priority for fallback)."""
        model_lower = model_id.lower()
        
        # Prefer smaller, faster models for fallback
        if any(size in model_lower for size in ["7b", "small", "mini", "flash"]):
            return 1
        elif any(size in model_lower for size in ["13b", "medium", "turbo"]):
            return 2
        elif any(size in model_lower for size in ["70b", "large", "pro"]):
            return 3
        else:
            return 4
    
    def _monitoring_loop(self) -> None:
        """Background monitoring loop for model health checks."""
        logger.info("Model availability monitoring loop started")
        
        while not self._stop_monitoring.is_set():
            try:
                # Get all models from all providers
                providers = self.registry.list_providers(healthy_only=False)
                
                for provider in providers:
                    if self._stop_monitoring.is_set():
                        break
                    
                    try:
                        models = self.registry.list_models(provider=provider)
                        
                        for model in models:
                            if self._stop_monitoring.is_set():
                                break
                            
                            # Use semaphore to limit concurrent checks
                            with self.health_check_semaphore:
                                if self._stop_monitoring.is_set():
                                    break
                                
                                # Check if model needs health check
                                model_key = f"{provider}:{model.id}"
                                needs_check = True
                                
                                if model_key in self.model_health:
                                    last_check = self.model_health[model_key].last_check
                                    time_since_check = datetime.now() - last_check
                                    needs_check = time_since_check.total_seconds() >= self.health_check_interval
                                
                                if needs_check:
                                    logger.debug(f"Background health check for {model_key}")
                                    self.check_model_availability(provider, model.id, force_check=True)
                    
                    except Exception as e:
                        logger.error(f"Error monitoring models for provider {provider}: {e}")
                
                # Wait before next monitoring cycle
                self._stop_monitoring.wait(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in model monitoring loop: {e}")
                self._stop_monitoring.wait(60)  # Wait a minute before retrying
        
        logger.info("Model availability monitoring loop stopped")


# Global instance
_model_availability_manager = None


def get_model_availability_manager(registry=None) -> ModelAvailabilityManager:
    """Get the global model availability manager instance."""
    global _model_availability_manager
    if _model_availability_manager is None:
        _model_availability_manager = ModelAvailabilityManager(registry=registry)
    return _model_availability_manager