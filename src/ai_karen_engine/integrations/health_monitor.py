"""
Comprehensive Health Monitoring Service for LLM Providers and Runtimes

This module provides comprehensive health monitoring capabilities for the LLM system,
including real-time connectivity testing, model availability verification, capability
detection, performance metrics collection, and intelligent routing decisions.

Key Features:
- Real-time connectivity testing for API endpoints and local models
- Model availability verification that actually tests model access
- Capability detection (streaming, function calling, vision support)
- Performance metrics collection (response time, success rate, error rate)
- Provider ranking based on performance and reliability
- Health status caching with appropriate TTL
- Background health monitoring with configurable intervals
- Automatic recovery detection and status updates
- Detailed health status reporting and diagnostics
"""

import asyncio
import json
import logging
import os
import requests
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Union
from urllib.parse import urljoin

from ai_karen_engine.integrations.registry import get_registry, HealthStatus

logger = logging.getLogger(__name__)

# Optional Prometheus metrics
try:
    from prometheus_client import Counter, Gauge, Histogram
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False
    
    class _DummyMetric:
        def labels(self, **kwargs):
            return self
        def inc(self, n: int = 1):
            pass
        def set(self, v: float):
            pass
        def observe(self, v: float):
            pass
    
    Counter = Gauge = Histogram = _DummyMetric

# Metrics
HEALTH_CHECK_TOTAL = Counter(
    "llm_health_checks_total",
    "Total health checks performed",
    ["component", "status"]
) if METRICS_ENABLED else Counter()

COMPONENT_HEALTH_STATUS = Gauge(
    "llm_component_health_status",
    "Current health status of components (1=healthy, 0=unhealthy)",
    ["component", "type"]
) if METRICS_ENABLED else Gauge()

HEALTH_CHECK_DURATION = Histogram(
    "llm_health_check_duration_seconds",
    "Duration of health checks",
    ["component"]
) if METRICS_ENABLED else Histogram()

FAILOVER_EVENTS = Counter(
    "llm_failover_events_total",
    "Total failover events",
    ["from_component", "to_component", "reason"]
) if METRICS_ENABLED else Counter()


@dataclass
class PerformanceMetrics:
    """Enhanced performance metrics for a provider."""
    average_response_time: float = 0.0
    success_rate: float = 0.0
    error_rate: float = 0.0
    requests_per_minute: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Enhanced metrics
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    
    # Error categorization
    timeout_errors: int = 0
    auth_errors: int = 0
    rate_limit_errors: int = 0
    network_errors: int = 0
    server_errors: int = 0
    unknown_errors: int = 0
    
    # Performance tracking
    response_time_history: List[float] = field(default_factory=list)
    hourly_request_counts: Dict[str, int] = field(default_factory=dict)
    daily_success_rates: Dict[str, float] = field(default_factory=dict)


@dataclass
class ConnectivityResult:
    """Result of connectivity testing."""
    success: bool
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    status_code: Optional[int] = None
    endpoint_url: Optional[str] = None


@dataclass
class ModelAvailabilityResult:
    """Result of model availability verification."""
    available_models: List[str] = field(default_factory=list)
    unavailable_models: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    total_tested: int = 0


@dataclass
class CapabilityDetectionResult:
    """Result of capability detection."""
    streaming_support: bool = False
    function_calling_support: bool = False
    vision_support: bool = False
    embedding_support: bool = False
    detected_capabilities: Dict[str, bool] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class DetailedHealthStatus(HealthStatus):
    """Enhanced health status with detailed information."""
    connectivity_status: str = "unknown"
    model_availability: Dict[str, bool] = field(default_factory=dict)
    capability_status: Dict[str, bool] = field(default_factory=dict)
    performance_metrics: Optional[PerformanceMetrics] = None
    recovery_suggestions: List[str] = field(default_factory=list)
    dependencies_status: Dict[str, bool] = field(default_factory=dict)
    configuration_issues: List[str] = field(default_factory=list)


@dataclass
class HealthEvent:
    """Represents a health status change event."""
    component: str
    old_status: str
    new_status: str
    timestamp: datetime
    error_message: Optional[str] = None
    response_time: Optional[float] = None
    connectivity_result: Optional[ConnectivityResult] = None
    model_availability: Optional[ModelAvailabilityResult] = None
    capability_detection: Optional[CapabilityDetectionResult] = None


@dataclass
class FailoverEvent:
    """Represents a failover event."""
    from_component: str
    to_component: str
    reason: str
    timestamp: datetime
    success: bool = True


class ComprehensiveHealthMonitor:
    """
    Comprehensive health monitoring service for LLM providers and runtimes.
    
    This service provides real-time health monitoring with detailed connectivity testing,
    model availability verification, capability detection, and performance metrics collection.
    """
    
    def __init__(
        self,
        registry=None,
        check_interval: int = 30,
        failure_threshold: int = 3,
        recovery_threshold: int = 2,
        enable_auto_failover: bool = True,
        cache_ttl: int = 300,  # 5 minutes
        connectivity_timeout: float = 10.0,
        model_test_timeout: float = 30.0,
    ):
        self.registry = registry or get_registry()
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        self.enable_auto_failover = enable_auto_failover
        self.cache_ttl = cache_ttl
        self.connectivity_timeout = connectivity_timeout
        self.model_test_timeout = model_test_timeout
        
        # Health tracking
        self.health_history: Dict[str, List[DetailedHealthStatus]] = {}
        self.failure_counts: Dict[str, int] = {}
        self.recovery_counts: Dict[str, int] = {}
        self.last_known_good: Dict[str, datetime] = {}
        
        # Performance tracking
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        self.provider_rankings: Dict[str, float] = {}
        
        # Caching
        self.health_cache: Dict[str, DetailedHealthStatus] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Event tracking
        self.health_events: List[HealthEvent] = []
        self.failover_events: List[FailoverEvent] = []
        
        # Callbacks
        self.health_change_callbacks: List[Callable[[HealthEvent], None]] = []
        self.failover_callbacks: List[Callable[[FailoverEvent], None]] = []
        
        # Monitoring state
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Provider endpoint mappings for connectivity testing
        self.provider_endpoints = {
            "openai": "https://api.openai.com/v1/models",
            "gemini": "https://generativelanguage.googleapis.com/v1/models",
            "deepseek": "https://api.deepseek.com/v1/models",
            "anthropic": "https://api.anthropic.com/v1/messages",
            "huggingface": "https://api-inference.huggingface.co/models",
        }
        
        logger.info(f"Comprehensive health monitor initialized with {check_interval}s interval")
    
    def start_monitoring(self) -> None:
        """Start continuous health monitoring."""
        if self.monitoring_active:
            logger.warning("Health monitoring is already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Started continuous health monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop continuous health monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Stopped health monitoring")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                self.check_all_health()
                self._update_provider_rankings()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(self.check_interval)
    
    def check_provider_health(self, provider_name: str) -> DetailedHealthStatus:
        """Perform comprehensive health check on a provider."""
        # Check cache first
        cache_key = f"provider:{provider_name}"
        if self._is_cache_valid(cache_key):
            return self.health_cache[cache_key]
        
        start_time = time.time()
        
        try:
            # Get provider spec
            provider_spec = self.registry._providers.get(provider_name)
            if not provider_spec:
                status = DetailedHealthStatus(
                    status="not_found",
                    error_message=f"Provider {provider_name} not registered",
                    last_check=time.time()
                )
                self._cache_health_status(cache_key, status)
                return status
            
            # Initialize detailed status
            detailed_status = DetailedHealthStatus(
                status="unknown",
                last_check=time.time(),
                performance_metrics=self.performance_metrics.get(provider_name)
            )
            
            # Test connectivity
            connectivity_result = self.test_provider_connectivity(provider_name)
            detailed_status.connectivity_status = "healthy" if connectivity_result.success else "unhealthy"
            
            # Test model availability
            model_availability = self.verify_model_availability(provider_name)
            detailed_status.model_availability = {
                model: True for model in model_availability.available_models
            }
            detailed_status.model_availability.update({
                model: False for model in model_availability.unavailable_models
            })
            
            # Detect capabilities
            capability_result = self.detect_capabilities(provider_name)
            detailed_status.capability_status = capability_result.detected_capabilities
            
            # Determine overall status
            if connectivity_result.success and model_availability.available_models:
                if len(model_availability.unavailable_models) == 0:
                    detailed_status.status = "healthy"
                else:
                    detailed_status.status = "degraded"
                    detailed_status.recovery_suggestions.append(
                        f"Some models unavailable: {', '.join(model_availability.unavailable_models)}"
                    )
            else:
                detailed_status.status = "unhealthy"
                if not connectivity_result.success:
                    detailed_status.error_message = connectivity_result.error_message
                    detailed_status.recovery_suggestions.append("Check network connectivity and API credentials")
                if not model_availability.available_models:
                    detailed_status.recovery_suggestions.append("No models are available - check API key and permissions")
            
            # Update response time
            detailed_status.response_time = time.time() - start_time
            
            # Cache the result
            self._cache_health_status(cache_key, detailed_status)
            
            return detailed_status
            
        except Exception as e:
            logger.error(f"Health check failed for {provider_name}: {e}")
            status = DetailedHealthStatus(
                status="unhealthy",
                error_message=str(e),
                last_check=time.time(),
                response_time=time.time() - start_time
            )
            self._cache_health_status(cache_key, status)
            return status
    
    def test_provider_connectivity(self, provider_name: str) -> ConnectivityResult:
        """Test network connectivity and API endpoint availability with enhanced testing."""
        try:
            endpoint_url = self.provider_endpoints.get(provider_name)
            if not endpoint_url:
                # For local providers, test local model availability
                if provider_name in ["llama_cpp", "transformers", "local"]:
                    return self._test_local_provider_connectivity(provider_name)
                else:
                    # Unknown provider, assume connectivity is OK
                    return ConnectivityResult(
                        success=True,
                        response_time=0.0,
                        endpoint_url="local"
                    )
            
            start_time = time.time()
            
            # Get API key for authentication
            api_key = self._get_provider_api_key(provider_name)
            headers = {"User-Agent": "AI-Karen-Health-Monitor/1.0"}
            
            if api_key:
                if provider_name == "openai":
                    headers["Authorization"] = f"Bearer {api_key}"
                elif provider_name == "gemini":
                    endpoint_url = f"{endpoint_url}?key={api_key}"
                elif provider_name == "deepseek":
                    headers["Authorization"] = f"Bearer {api_key}"
                elif provider_name == "anthropic":
                    headers["x-api-key"] = api_key
                    headers["anthropic-version"] = "2023-06-01"
                elif provider_name == "huggingface":
                    headers["Authorization"] = f"Bearer {api_key}"
            
            # Make the request with proper error handling
            response = requests.get(
                endpoint_url,
                headers=headers,
                timeout=self.connectivity_timeout,
                allow_redirects=True
            )
            
            response_time = time.time() - start_time
            
            # Enhanced status code handling
            if response.status_code == 200:
                return ConnectivityResult(
                    success=True,
                    response_time=response_time,
                    status_code=response.status_code,
                    endpoint_url=endpoint_url
                )
            elif response.status_code in [401, 403]:
                # Authentication issue but endpoint is reachable
                return ConnectivityResult(
                    success=True,  # Connectivity is OK, just auth issue
                    response_time=response_time,
                    status_code=response.status_code,
                    endpoint_url=endpoint_url,
                    error_message=f"Authentication required (HTTP {response.status_code})"
                )
            elif response.status_code == 429:
                # Rate limited but endpoint is reachable
                return ConnectivityResult(
                    success=True,
                    response_time=response_time,
                    status_code=response.status_code,
                    endpoint_url=endpoint_url,
                    error_message="Rate limited - endpoint is healthy"
                )
            else:
                return ConnectivityResult(
                    success=False,
                    response_time=response_time,
                    error_message=f"HTTP {response.status_code}: {response.text[:200]}",
                    status_code=response.status_code,
                    endpoint_url=endpoint_url
                )
                
        except requests.exceptions.Timeout:
            return ConnectivityResult(
                success=False,
                error_message=f"Connection timeout after {self.connectivity_timeout}s",
                endpoint_url=endpoint_url
            )
        except requests.exceptions.ConnectionError as e:
            return ConnectivityResult(
                success=False,
                error_message=f"Connection error: {str(e)}",
                endpoint_url=endpoint_url
            )
        except requests.exceptions.SSLError as e:
            return ConnectivityResult(
                success=False,
                error_message=f"SSL/TLS error: {str(e)}",
                endpoint_url=endpoint_url
            )
        except Exception as e:
            return ConnectivityResult(
                success=False,
                error_message=f"Connectivity test failed: {str(e)}",
                endpoint_url=endpoint_url
            )
    
    def _test_local_provider_connectivity(self, provider_name: str) -> ConnectivityResult:
        """Test connectivity for local providers by checking dependencies and model files."""
        start_time = time.time()
        
        try:
            if provider_name == "llama_cpp":
                # Check if llama-cpp-python is available
                try:
                    import llama_cpp
                    # Check for model files
                    available_models, _ = self._check_local_models(provider_name)
                    if available_models:
                        return ConnectivityResult(
                            success=True,
                            response_time=time.time() - start_time,
                            endpoint_url="local",
                            error_message=f"Found {len(available_models)} local models"
                        )
                    else:
                        return ConnectivityResult(
                            success=False,
                            response_time=time.time() - start_time,
                            endpoint_url="local",
                            error_message="llama-cpp-python available but no GGUF models found"
                        )
                except ImportError:
                    return ConnectivityResult(
                        success=False,
                        response_time=time.time() - start_time,
                        endpoint_url="local",
                        error_message="llama-cpp-python not installed"
                    )
            
            elif provider_name == "transformers":
                # Check if transformers is available
                try:
                    import transformers
                    import torch
                    # Check for model files
                    available_models, _ = self._check_local_models(provider_name)
                    return ConnectivityResult(
                        success=True,
                        response_time=time.time() - start_time,
                        endpoint_url="local",
                        error_message=f"Transformers available, found {len(available_models)} models"
                    )
                except ImportError as e:
                    return ConnectivityResult(
                        success=False,
                        response_time=time.time() - start_time,
                        endpoint_url="local",
                        error_message=f"Missing dependencies: {str(e)}"
                    )
            
            else:
                # Generic local provider
                return ConnectivityResult(
                    success=True,
                    response_time=time.time() - start_time,
                    endpoint_url="local"
                )
                
        except Exception as e:
            return ConnectivityResult(
                success=False,
                response_time=time.time() - start_time,
                endpoint_url="local",
                error_message=f"Local connectivity test failed: {str(e)}"
            )
    
    def verify_model_availability(self, provider_name: str) -> ModelAvailabilityResult:
        """Verify that provider's models are accessible with actual testing."""
        try:
            # Get provider spec and available models
            provider_spec = self.registry._providers.get(provider_name)
            if not provider_spec:
                return ModelAvailabilityResult(
                    error_message=f"Provider {provider_name} not found"
                )
            
            available_models = []
            unavailable_models = []
            
            # For API-based providers, try to discover models via API
            if provider_name in ["openai", "gemini", "deepseek", "anthropic", "huggingface"]:
                try:
                    if provider_spec.discover:
                        discovered_models = provider_spec.discover()
                        # Test a sample of models to verify actual access
                        for model in discovered_models[:5]:  # Test first 5 models
                            model_name = model.get("name", model.get("id", "unknown"))
                            if self._test_model_access(provider_name, model_name):
                                available_models.append(model_name)
                            else:
                                unavailable_models.append(model_name)
                        
                        # Add remaining models as available (assume they work if first few do)
                        if available_models and len(discovered_models) > 5:
                            remaining_models = [model.get("name", model.get("id", "unknown")) 
                                              for model in discovered_models[5:]]
                            available_models.extend(remaining_models)
                    else:
                        # Use fallback models and test them
                        for model in provider_spec.fallback_models:
                            model_name = model.get("name", model.get("id", "unknown"))
                            if self._test_model_access(provider_name, model_name):
                                available_models.append(model_name)
                            else:
                                unavailable_models.append(model_name)
                                
                except Exception as e:
                    logger.warning(f"Model discovery/testing failed for {provider_name}: {e}")
                    # Fall back to static model list without testing
                    available_models = [model.get("name", model.get("id", "unknown")) 
                                      for model in provider_spec.fallback_models]
            
            # For local providers, check if model files exist and are loadable
            elif provider_name in ["llama_cpp", "transformers", "local"]:
                available_models, unavailable_models = self._check_local_models_with_testing(provider_name)
            
            else:
                # Unknown provider type, use fallback models
                available_models = [model.get("name", model.get("id", "unknown")) 
                                  for model in provider_spec.fallback_models]
            
            return ModelAvailabilityResult(
                available_models=available_models,
                unavailable_models=unavailable_models,
                total_tested=len(available_models) + len(unavailable_models)
            )
            
        except Exception as e:
            return ModelAvailabilityResult(
                error_message=f"Model availability check failed: {str(e)}"
            )
    
    def _test_model_access(self, provider_name: str, model_name: str) -> bool:
        """Test if a specific model is accessible via API."""
        try:
            api_key = self._get_provider_api_key(provider_name)
            if not api_key:
                return False  # Can't test without API key
            
            # Make a minimal test request to verify model access
            if provider_name == "openai":
                import openai
                try:
                    client = openai.OpenAI(api_key=api_key)
                    # Try to get model info
                    client.models.retrieve(model_name)
                    return True
                except Exception:
                    return False
            
            elif provider_name == "gemini":
                # Test with a minimal request
                headers = {"Content-Type": "application/json"}
                test_url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}?key={api_key}"
                response = requests.get(test_url, headers=headers, timeout=5)
                return response.status_code == 200
            
            elif provider_name == "deepseek":
                # Test with model list endpoint
                headers = {"Authorization": f"Bearer {api_key}"}
                response = requests.get("https://api.deepseek.com/v1/models", headers=headers, timeout=5)
                if response.status_code == 200:
                    models = response.json().get("data", [])
                    return any(model.get("id") == model_name for model in models)
                return False
            
            elif provider_name == "anthropic":
                # Anthropic doesn't have a model list endpoint, assume model is available if API key works
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                }
                # Test with a minimal message (this will fail but tells us if auth works)
                test_data = {
                    "model": model_name,
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "test"}]
                }
                response = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=test_data,
                    timeout=5
                )
                # 400 means model exists but request was invalid, 404 means model doesn't exist
                return response.status_code != 404
            
            elif provider_name == "huggingface":
                # Test model info endpoint
                headers = {"Authorization": f"Bearer {api_key}"}
                test_url = f"https://huggingface.co/api/models/{model_name}"
                response = requests.get(test_url, headers=headers, timeout=5)
                return response.status_code == 200
            
            return False  # Unknown provider
            
        except Exception as e:
            logger.debug(f"Model access test failed for {provider_name}/{model_name}: {e}")
            return False
    
    def _check_local_models_with_testing(self, provider_name: str) -> tuple[List[str], List[str]]:
        """Check availability of local model files with actual loading tests."""
        available = []
        unavailable = []
        
        try:
            # Get basic file list first
            file_available, file_unavailable = self._check_local_models(provider_name)
            
            # Test a sample of models to see if they can actually be loaded
            if provider_name == "llama_cpp":
                try:
                    import llama_cpp
                    # Test first few models
                    for model_file in file_available[:3]:  # Test first 3 models
                        try:
                            # Try to create a minimal llama instance
                            model_path = self._find_model_path(model_file)
                            if model_path and os.path.exists(model_path):
                                # Just check if file is readable and has correct format
                                with open(model_path, 'rb') as f:
                                    header = f.read(4)
                                    if header == b'GGUF':  # GGUF magic number
                                        available.append(model_file)
                                    else:
                                        unavailable.append(model_file)
                            else:
                                unavailable.append(model_file)
                        except Exception as e:
                            logger.debug(f"Failed to test model {model_file}: {e}")
                            unavailable.append(model_file)
                    
                    # Add remaining models as available if some tests passed
                    if available and len(file_available) > 3:
                        available.extend(file_available[3:])
                    elif not available:
                        unavailable.extend(file_available[3:])
                        
                except ImportError:
                    # llama-cpp-python not available
                    unavailable.extend(file_available)
            
            elif provider_name == "transformers":
                try:
                    import transformers
                    import torch
                    # Test first few models
                    for model_dir in file_available[:2]:  # Test first 2 models
                        try:
                            model_path = self._find_model_path(model_dir)
                            if model_path and os.path.exists(model_path):
                                # Check if it has required files
                                config_file = os.path.join(model_path, "config.json")
                                if os.path.exists(config_file):
                                    available.append(model_dir)
                                else:
                                    unavailable.append(model_dir)
                            else:
                                unavailable.append(model_dir)
                        except Exception as e:
                            logger.debug(f"Failed to test model {model_dir}: {e}")
                            unavailable.append(model_dir)
                    
                    # Add remaining models as available if some tests passed
                    if available and len(file_available) > 2:
                        available.extend(file_available[2:])
                    elif not available:
                        unavailable.extend(file_available[2:])
                        
                except ImportError:
                    # transformers not available
                    unavailable.extend(file_available)
            
            else:
                # Generic local provider - just return file availability
                available = file_available
                unavailable = file_unavailable
            
        except Exception as e:
            logger.warning(f"Failed to test local models for {provider_name}: {e}")
            # Fall back to basic file checking
            available, unavailable = self._check_local_models(provider_name)
        
        return available, unavailable
    
    def _find_model_path(self, model_name: str) -> Optional[str]:
        """Find the full path to a model file or directory."""
        model_dirs = [
            "models",
            "models/llama-cpp",
            "models/transformers",
            os.path.expanduser("~/.cache/huggingface/transformers"),
            os.path.expanduser("~/.cache/huggingface/hub"),
        ]
        
        for model_dir in model_dirs:
            if os.path.exists(model_dir):
                model_path = os.path.join(model_dir, model_name)
                if os.path.exists(model_path):
                    return model_path
        
        return None
    
    def detect_capabilities(self, provider_name: str) -> CapabilityDetectionResult:
        """Detect and verify provider capabilities with actual testing."""
        try:
            provider_spec = self.registry._providers.get(provider_name)
            if not provider_spec:
                return CapabilityDetectionResult(
                    error_message=f"Provider {provider_name} not found"
                )
            
            # Get capabilities from provider spec as baseline
            spec_capabilities = provider_spec.capabilities or set()
            
            # Initialize detected capabilities
            detected_capabilities = {
                "streaming_support": False,
                "function_calling_support": False,
                "vision_support": False,
                "embedding_support": False,
                "chat_completion": False,
                "text_generation": False,
            }
            
            # Test capabilities based on provider type
            if provider_name == "openai":
                detected_capabilities.update(self._test_openai_capabilities())
            elif provider_name == "gemini":
                detected_capabilities.update(self._test_gemini_capabilities())
            elif provider_name == "deepseek":
                detected_capabilities.update(self._test_deepseek_capabilities())
            elif provider_name == "anthropic":
                detected_capabilities.update(self._test_anthropic_capabilities())
            elif provider_name == "huggingface":
                detected_capabilities.update(self._test_huggingface_capabilities())
            elif provider_name in ["llama_cpp", "transformers", "local"]:
                detected_capabilities.update(self._test_local_capabilities(provider_name))
            else:
                # Unknown provider, use spec capabilities
                detected_capabilities.update({
                    "streaming_support": "streaming" in spec_capabilities,
                    "function_calling_support": "function_calling" in spec_capabilities or "tools" in spec_capabilities,
                    "vision_support": "vision" in spec_capabilities or "multimodal" in spec_capabilities,
                    "embedding_support": "embeddings" in spec_capabilities,
                    "chat_completion": "chat" in spec_capabilities,
                    "text_generation": "text_generation" in spec_capabilities,
                })
            
            return CapabilityDetectionResult(
                streaming_support=detected_capabilities["streaming_support"],
                function_calling_support=detected_capabilities["function_calling_support"],
                vision_support=detected_capabilities["vision_support"],
                embedding_support=detected_capabilities["embedding_support"],
                detected_capabilities=detected_capabilities
            )
            
        except Exception as e:
            return CapabilityDetectionResult(
                error_message=f"Capability detection failed: {str(e)}"
            )
    
    def _test_openai_capabilities(self) -> Dict[str, bool]:
        """Test OpenAI-specific capabilities."""
        capabilities = {
            "streaming_support": True,  # OpenAI supports streaming
            "function_calling_support": True,  # OpenAI supports function calling
            "vision_support": True,  # GPT-4V supports vision
            "embedding_support": True,  # OpenAI has embedding models
            "chat_completion": True,
            "text_generation": True,
        }
        
        # Test if API key is available for actual testing
        api_key = self._get_provider_api_key("openai")
        if api_key:
            try:
                # Test basic API access
                headers = {"Authorization": f"Bearer {api_key}"}
                response = requests.get(
                    "https://api.openai.com/v1/models",
                    headers=headers,
                    timeout=5
                )
                if response.status_code == 200:
                    models = response.json().get("data", [])
                    model_ids = [model.get("id", "") for model in models]
                    
                    # Check for specific model types
                    capabilities["vision_support"] = any("gpt-4" in model_id and "vision" in model_id for model_id in model_ids)
                    capabilities["embedding_support"] = any("embedding" in model_id for model_id in model_ids)
                    
            except Exception as e:
                logger.debug(f"OpenAI capability testing failed: {e}")
        
        return capabilities
    
    def _test_gemini_capabilities(self) -> Dict[str, bool]:
        """Test Gemini-specific capabilities."""
        capabilities = {
            "streaming_support": True,  # Gemini supports streaming
            "function_calling_support": True,  # Gemini supports function calling
            "vision_support": True,  # Gemini Pro Vision supports vision
            "embedding_support": False,  # Gemini doesn't have embedding models
            "chat_completion": True,
            "text_generation": True,
        }
        
        # Test if API key is available
        api_key = self._get_provider_api_key("gemini")
        if api_key:
            try:
                # Test basic API access
                response = requests.get(
                    f"https://generativelanguage.googleapis.com/v1/models?key={api_key}",
                    timeout=5
                )
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [model.get("name", "") for model in models]
                    
                    # Check for vision models
                    capabilities["vision_support"] = any("vision" in name.lower() for name in model_names)
                    
            except Exception as e:
                logger.debug(f"Gemini capability testing failed: {e}")
        
        return capabilities
    
    def _test_deepseek_capabilities(self) -> Dict[str, bool]:
        """Test DeepSeek-specific capabilities."""
        capabilities = {
            "streaming_support": True,  # DeepSeek supports streaming
            "function_calling_support": True,  # DeepSeek supports function calling
            "vision_support": False,  # DeepSeek doesn't have vision models yet
            "embedding_support": False,  # DeepSeek doesn't have embedding models
            "chat_completion": True,
            "text_generation": True,
        }
        
        # Test if API key is available
        api_key = self._get_provider_api_key("deepseek")
        if api_key:
            try:
                # Test basic API access
                headers = {"Authorization": f"Bearer {api_key}"}
                response = requests.get(
                    "https://api.deepseek.com/v1/models",
                    headers=headers,
                    timeout=5
                )
                if response.status_code == 200:
                    models = response.json().get("data", [])
                    model_ids = [model.get("id", "") for model in models]
                    
                    # Check for specific capabilities based on available models
                    capabilities["vision_support"] = any("vision" in model_id.lower() for model_id in model_ids)
                    
            except Exception as e:
                logger.debug(f"DeepSeek capability testing failed: {e}")
        
        return capabilities
    
    def _test_anthropic_capabilities(self) -> Dict[str, bool]:
        """Test Anthropic-specific capabilities."""
        capabilities = {
            "streaming_support": True,  # Anthropic supports streaming
            "function_calling_support": True,  # Anthropic supports function calling (tools)
            "vision_support": True,  # Claude 3 supports vision
            "embedding_support": False,  # Anthropic doesn't have embedding models
            "chat_completion": True,
            "text_generation": True,
        }
        
        # Anthropic doesn't have a models endpoint, so we can't test dynamically
        # These capabilities are based on known Claude model features
        return capabilities
    
    def _test_huggingface_capabilities(self) -> Dict[str, bool]:
        """Test HuggingFace-specific capabilities."""
        capabilities = {
            "streaming_support": True,  # HF Inference API supports streaming
            "function_calling_support": False,  # Most HF models don't support function calling
            "vision_support": True,  # Some HF models support vision
            "embedding_support": True,  # HF has many embedding models
            "chat_completion": True,
            "text_generation": True,
        }
        
        return capabilities
    
    def _test_local_capabilities(self, provider_name: str) -> Dict[str, bool]:
        """Test local provider capabilities."""
        capabilities = {
            "streaming_support": True,  # Local providers can stream
            "function_calling_support": False,  # Most local models don't support function calling
            "vision_support": False,  # Most local models don't support vision
            "embedding_support": True,  # Local providers can do embeddings
            "chat_completion": True,
            "text_generation": True,
        }
        
        if provider_name == "llama_cpp":
            try:
                import llama_cpp
                capabilities["streaming_support"] = True
                # Check if we have any vision-capable models
                available_models, _ = self._check_local_models(provider_name)
                capabilities["vision_support"] = any("vision" in model.lower() or "llava" in model.lower() 
                                                   for model in available_models)
            except ImportError:
                capabilities["streaming_support"] = False
        
        elif provider_name == "transformers":
            try:
                import transformers
                import torch
                capabilities["streaming_support"] = True
                # Check for vision models
                available_models, _ = self._check_local_models(provider_name)
                capabilities["vision_support"] = any("vision" in model.lower() or "clip" in model.lower() 
                                                   for model in available_models)
            except ImportError:
                capabilities["streaming_support"] = False
        
        return capabilities
    
    def check_all_health(self) -> Dict[str, DetailedHealthStatus]:
        """Check health of all components and process status changes."""
        current_health = {}
        
        # Check all providers
        for provider_name in self.registry.list_providers():
            try:
                status = self.check_provider_health(provider_name)
                component_key = f"provider:{provider_name}"
                current_health[component_key] = status
                self._process_health_status(component_key, status)
            except Exception as e:
                logger.error(f"Failed to check health for provider {provider_name}: {e}")
        
        # Check all runtimes
        for runtime_name in self.registry.list_runtimes():
            try:
                status = self._check_runtime_health(runtime_name)
                component_key = f"runtime:{runtime_name}"
                current_health[component_key] = status
                self._process_health_status(component_key, status)
            except Exception as e:
                logger.error(f"Failed to check health for runtime {runtime_name}: {e}")
        
        return current_health
    
    def _check_runtime_health(self, runtime_name: str) -> DetailedHealthStatus:
        """Check health of a runtime component."""
        cache_key = f"runtime:{runtime_name}"
        if self._is_cache_valid(cache_key):
            return self.health_cache[cache_key]
        
        start_time = time.time()
        
        try:
            runtime_spec = self.registry._runtimes.get(runtime_name)
            if not runtime_spec:
                status = DetailedHealthStatus(
                    status="not_found",
                    error_message=f"Runtime {runtime_name} not registered",
                    last_check=time.time()
                )
                self._cache_health_status(cache_key, status)
                return status
            
            # Basic health check
            if runtime_spec.health:
                health_result = runtime_spec.health()
                status = DetailedHealthStatus(
                    status=health_result.get("status", "unknown"),
                    error_message=health_result.get("error_message"),
                    last_check=time.time(),
                    response_time=time.time() - start_time
                )
            else:
                # Default to healthy if no health check function
                status = DetailedHealthStatus(
                    status="healthy",
                    last_check=time.time(),
                    response_time=time.time() - start_time
                )
            
            self._cache_health_status(cache_key, status)
            return status
            
        except Exception as e:
            logger.error(f"Runtime health check failed for {runtime_name}: {e}")
            status = DetailedHealthStatus(
                status="unhealthy",
                error_message=str(e),
                last_check=time.time(),
                response_time=time.time() - start_time
            )
            self._cache_health_status(cache_key, status)
            return status
    
    def _get_provider_api_key(self, provider_name: str) -> Optional[str]:
        """Get API key for a provider."""
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "huggingface": "HUGGINGFACE_API_KEY",
        }
        
        env_var = env_var_map.get(provider_name)
        if env_var:
            import os
            return os.getenv(env_var)
        return None
    
    def _check_local_models(self, provider_name: str) -> tuple[List[str], List[str]]:
        """Check availability of local model files."""
        available = []
        unavailable = []
        
        try:
            # Common model directories
            model_dirs = [
                "models",
                "models/llama-cpp",
                "models/transformers",
                os.path.expanduser("~/.cache/huggingface/transformers"),
                os.path.expanduser("~/.cache/huggingface/hub"),
            ]
            
            for model_dir in model_dirs:
                if os.path.exists(model_dir):
                    for item in os.listdir(model_dir):
                        item_path = os.path.join(model_dir, item)
                        if os.path.isfile(item_path):
                            if item.endswith(('.gguf', '.bin', '.safetensors')):
                                available.append(item)
                        elif os.path.isdir(item_path):
                            # Check if it's a model directory with config files
                            config_files = ['config.json', 'pytorch_model.bin', 'model.safetensors']
                            if any(os.path.exists(os.path.join(item_path, cf)) for cf in config_files):
                                available.append(item)
            
        except Exception as e:
            logger.warning(f"Failed to check local models for {provider_name}: {e}")
        
        return available, unavailable
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached health status is still valid."""
        if cache_key not in self.health_cache:
            return False
        
        timestamp = self.cache_timestamps.get(cache_key)
        if not timestamp:
            return False
        
        return (datetime.now() - timestamp).total_seconds() < self.cache_ttl
    
    def _cache_health_status(self, cache_key: str, status: DetailedHealthStatus) -> None:
        """Cache health status with timestamp."""
        self.health_cache[cache_key] = status
        self.cache_timestamps[cache_key] = datetime.now()
    
    def _update_provider_rankings(self) -> None:
        """Update provider rankings based on performance and reliability with enhanced scoring."""
        for provider_name in self.registry.list_providers():
            metrics = self.performance_metrics.get(provider_name)
            if not metrics:
                # Initialize with default metrics for new providers
                self.provider_rankings[provider_name] = 50.0  # Neutral score
                continue
            
            # Enhanced ranking calculation with multiple factors
            # Factors: success rate (35%), response time (25%), availability (25%), consistency (15%)
            
            # Success rate score (0-35)
            success_score = metrics.success_rate * 35
            
            # Response time score (lower is better, normalize to 0-25)
            if metrics.average_response_time > 0:
                # Penalize high response times more severely
                if metrics.average_response_time < 1.0:
                    response_score = 25
                elif metrics.average_response_time < 3.0:
                    response_score = 20
                elif metrics.average_response_time < 5.0:
                    response_score = 15
                elif metrics.average_response_time < 10.0:
                    response_score = 10
                else:
                    response_score = 5
            else:
                response_score = 25
            
            # Availability score based on recent health checks (0-25)
            recent_health = self._get_recent_health_score(provider_name)
            availability_score = recent_health * 25
            
            # Consistency score based on error patterns (0-15)
            consistency_score = self._calculate_consistency_score(provider_name)
            
            # Bonus points for high-performing providers
            bonus_score = 0
            if metrics.success_rate > 0.95 and metrics.average_response_time < 2.0:
                bonus_score = 5  # Excellent performance bonus
            elif metrics.success_rate > 0.90 and metrics.average_response_time < 5.0:
                bonus_score = 2  # Good performance bonus
            
            # Calculate total score
            total_score = success_score + response_score + availability_score + consistency_score + bonus_score
            
            # Apply penalties for known issues
            penalty = 0
            failure_count = self.failure_counts.get(f"provider:{provider_name}", 0)
            if failure_count > 5:
                penalty = min(failure_count * 2, 20)  # Max 20 point penalty
            
            final_score = max(0, min(100, total_score - penalty))
            self.provider_rankings[provider_name] = final_score
            
            logger.debug(f"Provider {provider_name} ranking: {final_score:.1f} "
                        f"(success: {success_score:.1f}, response: {response_score:.1f}, "
                        f"availability: {availability_score:.1f}, consistency: {consistency_score:.1f}, "
                        f"bonus: {bonus_score}, penalty: {penalty})")
    
    def _calculate_consistency_score(self, provider_name: str) -> float:
        """Calculate consistency score based on error patterns and stability."""
        try:
            # Get recent health history
            history = self.health_history.get(f"provider:{provider_name}", [])
            if len(history) < 5:
                return 7.5  # Neutral score for insufficient data
            
            # Look at last 20 health checks
            recent_checks = history[-20:]
            
            # Calculate consistency metrics
            status_changes = 0
            for i in range(1, len(recent_checks)):
                if recent_checks[i].status != recent_checks[i-1].status:
                    status_changes += 1
            
            # Fewer status changes = more consistent
            if status_changes == 0:
                consistency_score = 15  # Perfect consistency
            elif status_changes <= 2:
                consistency_score = 12  # Good consistency
            elif status_changes <= 5:
                consistency_score = 8   # Fair consistency
            else:
                consistency_score = 3   # Poor consistency
            
            # Adjust based on response time variance
            response_times = [check.response_time for check in recent_checks 
                            if check.response_time is not None]
            if len(response_times) > 3:
                import statistics
                try:
                    variance = statistics.variance(response_times)
                    if variance < 0.5:
                        consistency_score += 0  # No bonus for low variance
                    elif variance > 5.0:
                        consistency_score -= 3  # Penalty for high variance
                except:
                    pass  # Ignore statistics errors
            
            return max(0, min(15, consistency_score))
            
        except Exception as e:
            logger.debug(f"Failed to calculate consistency score for {provider_name}: {e}")
            return 7.5  # Neutral score on error
    
    def _get_recent_health_score(self, provider_name: str) -> float:
        """Get recent health score for a provider (0.0 to 1.0)."""
        history = self.health_history.get(provider_name, [])
        if not history:
            return 0.5  # Unknown
        
        # Look at last 10 health checks
        recent_checks = history[-10:]
        healthy_count = sum(1 for status in recent_checks if status.status == "healthy")
        
        return healthy_count / len(recent_checks)
    
    def _process_health_status(self, component: str, status: DetailedHealthStatus) -> None:
        """Process a health status update for a component."""
        # Record metrics
        HEALTH_CHECK_TOTAL.labels(component=component, status=status.status).inc()
        if status.response_time:
            HEALTH_CHECK_DURATION.labels(component=component).observe(status.response_time)
        
        # Update health gauge
        health_value = 1.0 if status.status in ["healthy", "unknown"] else 0.0
        component_type = "provider" if component.startswith("provider:") else "runtime"
        COMPONENT_HEALTH_STATUS.labels(component=component, type=component_type).set(health_value)
        
        # Update performance metrics for providers
        if component.startswith("provider:"):
            provider_name = component[9:]  # Remove "provider:" prefix
            self._update_performance_metrics(provider_name, status)
        
        # Get previous status
        history = self.health_history.setdefault(component, [])
        previous_status = history[-1].status if history else "unknown"
        
        # Add to history
        history.append(status)
        if len(history) > 100:  # Keep last 100 status checks
            history.pop(0)
        
        # Check for status changes
        if status.status != previous_status:
            self._handle_status_change(component, previous_status, status)
        
        # Update failure/recovery tracking
        if status.status in ["unhealthy", "degraded"]:
            self.failure_counts[component] = self.failure_counts.get(component, 0) + 1
            self.recovery_counts[component] = 0
        elif status.status in ["healthy"]:
            self.recovery_counts[component] = self.recovery_counts.get(component, 0) + 1
            if self.recovery_counts[component] >= self.recovery_threshold:
                self.failure_counts[component] = 0
                self.last_known_good[component] = datetime.now()
    
    def _update_performance_metrics(self, provider_name: str, status: DetailedHealthStatus) -> None:
        """Update enhanced performance metrics for a provider."""
        if provider_name not in self.performance_metrics:
            self.performance_metrics[provider_name] = PerformanceMetrics()
        
        metrics = self.performance_metrics[provider_name]
        metrics.total_requests += 1
        current_time = datetime.now()
        
        # Update success/failure tracking
        if status.status == "healthy":
            metrics.successful_requests += 1
            metrics.consecutive_successes += 1
            metrics.consecutive_failures = 0
            metrics.last_success_time = current_time
        else:
            metrics.failed_requests += 1
            metrics.consecutive_failures += 1
            metrics.consecutive_successes = 0
            metrics.last_failure_time = current_time
            
            # Categorize error types
            if status.error_message:
                error_msg = status.error_message.lower()
                if "timeout" in error_msg:
                    metrics.timeout_errors += 1
                elif "auth" in error_msg or "unauthorized" in error_msg or "forbidden" in error_msg:
                    metrics.auth_errors += 1
                elif "rate limit" in error_msg or "429" in error_msg:
                    metrics.rate_limit_errors += 1
                elif "connection" in error_msg or "network" in error_msg:
                    metrics.network_errors += 1
                elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                    metrics.server_errors += 1
                else:
                    metrics.unknown_errors += 1
        
        # Update rates
        if metrics.total_requests > 0:
            metrics.success_rate = metrics.successful_requests / metrics.total_requests
            metrics.error_rate = metrics.failed_requests / metrics.total_requests
        
        # Update response time metrics
        if status.response_time:
            # Update min/max
            metrics.min_response_time = min(metrics.min_response_time, status.response_time)
            metrics.max_response_time = max(metrics.max_response_time, status.response_time)
            
            # Add to history (keep last 100 measurements)
            metrics.response_time_history.append(status.response_time)
            if len(metrics.response_time_history) > 100:
                metrics.response_time_history.pop(0)
            
            # Update average (exponential moving average)
            if metrics.average_response_time == 0:
                metrics.average_response_time = status.response_time
            else:
                # Use exponential moving average with alpha = 0.1
                metrics.average_response_time = (0.9 * metrics.average_response_time + 
                                               0.1 * status.response_time)
            
            # Calculate percentiles
            if len(metrics.response_time_history) >= 10:
                sorted_times = sorted(metrics.response_time_history)
                p95_index = int(len(sorted_times) * 0.95)
                p99_index = int(len(sorted_times) * 0.99)
                metrics.p95_response_time = sorted_times[p95_index]
                metrics.p99_response_time = sorted_times[p99_index]
        
        # Update hourly request counts
        hour_key = current_time.strftime("%Y-%m-%d-%H")
        metrics.hourly_request_counts[hour_key] = metrics.hourly_request_counts.get(hour_key, 0) + 1
        
        # Clean old hourly data (keep last 24 hours)
        cutoff_time = current_time - timedelta(hours=24)
        cutoff_key = cutoff_time.strftime("%Y-%m-%d-%H")
        keys_to_remove = [k for k in metrics.hourly_request_counts.keys() if k < cutoff_key]
        for key in keys_to_remove:
            del metrics.hourly_request_counts[key]
        
        # Update daily success rates
        day_key = current_time.strftime("%Y-%m-%d")
        if day_key not in metrics.daily_success_rates:
            metrics.daily_success_rates[day_key] = metrics.success_rate
        else:
            # Update daily success rate (simple average for now)
            metrics.daily_success_rates[day_key] = (
                metrics.daily_success_rates[day_key] + metrics.success_rate
            ) / 2
        
        # Clean old daily data (keep last 30 days)
        cutoff_date = current_time - timedelta(days=30)
        cutoff_day = cutoff_date.strftime("%Y-%m-%d")
        days_to_remove = [k for k in metrics.daily_success_rates.keys() if k < cutoff_day]
        for day in days_to_remove:
            del metrics.daily_success_rates[day]
        
        # Update requests per minute (based on recent activity)
        time_diff = (current_time - metrics.last_updated).total_seconds()
        if time_diff > 0:
            # Calculate based on recent hourly data
            recent_requests = sum(metrics.hourly_request_counts.values())
            hours_of_data = len(metrics.hourly_request_counts)
            if hours_of_data > 0:
                metrics.requests_per_minute = (recent_requests / hours_of_data) / 60.0
            else:
                metrics.requests_per_minute = 60.0 / max(time_diff, 1.0)
        
        metrics.last_updated = current_time
    
    def _handle_status_change(self, component: str, old_status: str, new_status: DetailedHealthStatus) -> None:
        """Handle a health status change with enhanced notifications."""
        event = HealthEvent(
            component=component,
            old_status=old_status,
            new_status=new_status.status,
            timestamp=datetime.now(),
            error_message=new_status.error_message,
            response_time=new_status.response_time,
        )
        
        self.health_events.append(event)
        if len(self.health_events) > 1000:  # Keep last 1000 events
            self.health_events.pop(0)
        
        # Enhanced logging with detailed context
        self._log_detailed_status_change(component, old_status, new_status, event)
        
        # Send notifications based on severity
        self._send_status_change_notifications(component, old_status, new_status.status, event)
        
        # Notify callbacks
        for callback in self.health_change_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Health change callback error: {e}")
        
        # Handle automatic failover
        if (self.enable_auto_failover and 
            new_status.status in ["unhealthy", "degraded"] and
            self.failure_counts.get(component, 0) >= self.failure_threshold):
            self._attempt_failover(component)
    
    def _log_detailed_status_change(self, component: str, old_status: str, new_status: DetailedHealthStatus, event: HealthEvent) -> None:
        """Log detailed status change information."""
        # Determine log level based on severity
        if new_status.status == "unhealthy" and old_status in ["healthy", "unknown"]:
            log_level = logging.ERROR
            severity = "CRITICAL"
        elif new_status.status == "degraded" and old_status == "healthy":
            log_level = logging.WARNING
            severity = "WARNING"
        elif new_status.status == "healthy" and old_status in ["unhealthy", "degraded"]:
            log_level = logging.INFO
            severity = "RECOVERY"
        else:
            log_level = logging.INFO
            severity = "INFO"
        
        # Create detailed log message
        log_message = (
            f"[{severity}] Health status change for {component}: "
            f"{old_status} -> {new_status.status}"
        )
        
        # Add context information
        context_info = []
        if new_status.response_time:
            context_info.append(f"response_time={new_status.response_time:.2f}s")
        if new_status.error_message:
            context_info.append(f"error='{new_status.error_message[:100]}'")
        if new_status.connectivity_status:
            context_info.append(f"connectivity={new_status.connectivity_status}")
        
        if context_info:
            log_message += f" ({', '.join(context_info)})"
        
        logger.log(log_level, log_message)
        
        # Log additional diagnostics for failures
        if new_status.status in ["unhealthy", "degraded"]:
            failure_count = self.failure_counts.get(component, 0)
            logger.log(log_level, f"Failure count for {component}: {failure_count}")
            
            if new_status.recovery_suggestions:
                logger.info(f"Recovery suggestions for {component}: {', '.join(new_status.recovery_suggestions)}")
    
    def _send_status_change_notifications(self, component: str, old_status: str, new_status: str, event: HealthEvent) -> None:
        """Send notifications for status changes based on severity."""
        try:
            # Determine notification type
            if new_status == "unhealthy" and old_status in ["healthy", "unknown"]:
                notification_type = "provider_failure"
                priority = "high"
            elif new_status == "degraded" and old_status == "healthy":
                notification_type = "provider_degraded"
                priority = "medium"
            elif new_status == "healthy" and old_status in ["unhealthy", "degraded"]:
                notification_type = "provider_recovery"
                priority = "low"
            else:
                notification_type = "provider_status_change"
                priority = "low"
            
            # Create notification payload
            notification = {
                "type": notification_type,
                "priority": priority,
                "component": component,
                "old_status": old_status,
                "new_status": new_status,
                "timestamp": event.timestamp.isoformat(),
                "error_message": event.error_message,
                "response_time": event.response_time,
            }
            
            # Add provider-specific context
            if component.startswith("provider:"):
                provider_name = component[9:]
                notification.update({
                    "provider_name": provider_name,
                    "ranking_score": self.provider_rankings.get(provider_name, 0.0),
                    "failure_count": self.failure_counts.get(component, 0),
                })
                
                # Add performance context
                performance = self.performance_metrics.get(provider_name)
                if performance:
                    notification.update({
                        "success_rate": performance.success_rate,
                        "average_response_time": performance.average_response_time,
                        "consecutive_failures": performance.consecutive_failures,
                    })
            
            # Store notification for retrieval
            if not hasattr(self, 'notifications'):
                self.notifications = []
            
            self.notifications.append(notification)
            if len(self.notifications) > 500:  # Keep last 500 notifications
                self.notifications.pop(0)
            
            # Log notification
            logger.info(f"Health notification: {notification_type} for {component} (priority: {priority})")
            
        except Exception as e:
            logger.error(f"Failed to send status change notification: {e}")
    
    def get_recent_notifications(self, hours: int = 24, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent health notifications."""
        if not hasattr(self, 'notifications'):
            return []
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = []
        
        for notification in self.notifications:
            notification_time = datetime.fromisoformat(notification['timestamp'])
            if notification_time > cutoff:
                if priority is None or notification.get('priority') == priority:
                    recent.append(notification)
        
        return sorted(recent, key=lambda x: x['timestamp'], reverse=True)
    
    def get_notification_summary(self) -> Dict[str, Any]:
        """Get summary of recent notifications."""
        if not hasattr(self, 'notifications'):
            return {"total": 0, "by_priority": {}, "by_type": {}}
        
        # Get last 24 hours
        recent = self.get_recent_notifications(24)
        
        summary = {
            "total": len(recent),
            "by_priority": {"high": 0, "medium": 0, "low": 0},
            "by_type": {},
            "recent_failures": [],
            "recent_recoveries": [],
        }
        
        for notification in recent:
            # Count by priority
            priority = notification.get('priority', 'low')
            summary['by_priority'][priority] = summary['by_priority'].get(priority, 0) + 1
            
            # Count by type
            notification_type = notification.get('type', 'unknown')
            summary['by_type'][notification_type] = summary['by_type'].get(notification_type, 0) + 1
            
            # Track recent failures and recoveries
            if notification_type == "provider_failure":
                summary['recent_failures'].append({
                    "component": notification['component'],
                    "timestamp": notification['timestamp'],
                    "error": notification.get('error_message'),
                })
            elif notification_type == "provider_recovery":
                summary['recent_recoveries'].append({
                    "component": notification['component'],
                    "timestamp": notification['timestamp'],
                })
        
        return summary
    
    def _attempt_failover(self, failed_component: str) -> None:
        """Attempt to failover from a failed component."""
        logger.warning(f"Attempting failover from failed component: {failed_component}")
        
        # Determine component type
        if failed_component.startswith("provider:"):
            component_type = "provider"
            component_name = failed_component[9:]
            alternatives = self.registry.get_healthy_providers()
        elif failed_component.startswith("runtime:"):
            component_type = "runtime"
            component_name = failed_component[8:]
            alternatives = self.registry.get_healthy_runtimes()
        else:
            logger.error(f"Unknown component type for failover: {failed_component}")
            return
        
        # Find healthy alternatives
        healthy_alternatives = [alt for alt in alternatives if alt != component_name]
        
        if not healthy_alternatives:
            logger.error(f"No healthy alternatives found for {failed_component}")
            return
        
        # Select best alternative (first healthy one for now)
        selected_alternative = healthy_alternatives[0]
        
        # Record failover event
        failover_event = FailoverEvent(
            from_component=failed_component,
            to_component=f"{component_type}:{selected_alternative}",
            reason=f"Health check failures exceeded threshold ({self.failure_threshold})",
            timestamp=datetime.now(),
            success=True,
        )
        
        self.failover_events.append(failover_event)
        if len(self.failover_events) > 100:  # Keep last 100 failover events
            self.failover_events.pop(0)
        
        # Record metrics
        FAILOVER_EVENTS.labels(
            from_component=failed_component,
            to_component=failover_event.to_component,
            reason="health_failure"
        ).inc()
        
        logger.info(f"Failover: {failed_component} -> {failover_event.to_component}")
        
        # Notify callbacks
        for callback in self.failover_callbacks:
            try:
                callback(failover_event)
            except Exception as e:
                logger.error(f"Failover callback error: {e}")
    
    def get_component_health(self, component: str) -> Optional[DetailedHealthStatus]:
        """Get current health status of a component."""
        # Check cache first
        if self._is_cache_valid(component):
            return self.health_cache[component]
        
        # Force a fresh health check
        if component.startswith("provider:"):
            provider_name = component[9:]
            return self.check_provider_health(provider_name)
        elif component.startswith("runtime:"):
            runtime_name = component[8:]
            return self._check_runtime_health(runtime_name)
        
        return None
    
    def get_provider_diagnostics(self, provider_name: str) -> Dict[str, Any]:
        """Get comprehensive diagnostic information for a provider."""
        try:
            provider_spec = self.registry._providers.get(provider_name)
            if not provider_spec:
                return {"error": f"Provider {provider_name} not found"}
            
            # Get current health status
            health_status = self.check_provider_health(provider_name)
            
            # Get performance metrics
            performance = self.performance_metrics.get(provider_name)
            
            # Get recent history
            history = self.health_history.get(f"provider:{provider_name}", [])
            recent_history = history[-20:] if history else []
            
            # Get connectivity test results
            connectivity_result = self.test_provider_connectivity(provider_name)
            
            # Get model availability results
            model_availability = self.verify_model_availability(provider_name)
            
            # Get capability detection results
            capability_result = self.detect_capabilities(provider_name)
            
            diagnostics = {
                "provider_name": provider_name,
                "timestamp": datetime.now().isoformat(),
                "current_status": {
                    "status": health_status.status,
                    "connectivity": health_status.connectivity_status,
                    "error_message": health_status.error_message,
                    "response_time": health_status.response_time,
                    "last_check": health_status.last_check,
                    "health_score": self._calculate_health_score(provider_name),
                },
                "configuration": {
                    "requires_api_key": provider_spec.requires_api_key,
                    "api_key_configured": self._get_provider_api_key(provider_name) is not None,
                    "api_key_valid": self._test_api_key_validity(provider_name),
                    "capabilities": list(provider_spec.capabilities),
                    "required_env_vars": provider_spec.required_env_vars,
                    "required_dependencies": provider_spec.required_dependencies,
                    "missing_env_vars": self._check_missing_env_vars(provider_name),
                    "missing_dependencies": self._check_missing_dependencies(provider_name),
                },
                "connectivity": {
                    "endpoint_reachable": connectivity_result.success,
                    "response_time": connectivity_result.response_time,
                    "status_code": connectivity_result.status_code,
                    "endpoint_url": connectivity_result.endpoint_url,
                    "error_message": connectivity_result.error_message,
                },
                "models": {
                    "available": model_availability.available_models,
                    "unavailable": model_availability.unavailable_models,
                    "total_tested": model_availability.total_tested,
                    "availability_status": health_status.model_availability,
                    "discovery_error": model_availability.error_message,
                },
                "capabilities": {
                    "detected": capability_result.detected_capabilities,
                    "streaming": capability_result.streaming_support,
                    "function_calling": capability_result.function_calling_support,
                    "vision": capability_result.vision_support,
                    "embeddings": capability_result.embedding_support,
                    "detection_error": capability_result.error_message,
                },
                "performance": self._get_detailed_performance_diagnostics(provider_name, performance),
                "reliability": {
                    "failure_count": self.failure_counts.get(f"provider:{provider_name}", 0),
                    "recovery_count": self.recovery_counts.get(f"provider:{provider_name}", 0),
                    "last_known_good": self.last_known_good.get(f"provider:{provider_name}").isoformat() if self.last_known_good.get(f"provider:{provider_name}") else None,
                    "uptime_percentage": self._calculate_uptime_percentage(provider_name),
                    "mtbf": self._calculate_mtbf(provider_name),  # Mean Time Between Failures
                    "mttr": self._calculate_mttr(provider_name),  # Mean Time To Recovery
                },
                "recent_history": [
                    {
                        "status": status.status,
                        "timestamp": status.last_check,
                        "response_time": status.response_time,
                        "error": status.error_message,
                        "connectivity": status.connectivity_status,
                    }
                    for status in recent_history
                ],
                "troubleshooting": {
                    "recovery_suggestions": health_status.recovery_suggestions,
                    "common_issues": self._get_common_issues(provider_name),
                    "next_steps": self._get_troubleshooting_steps(provider_name, health_status),
                },
                "ranking": {
                    "current_score": self.provider_rankings.get(provider_name, 0.0),
                    "rank": self._get_provider_rank(provider_name),
                    "total_providers": len(self.provider_rankings),
                },
            }
            
            return diagnostics
            
        except Exception as e:
            logger.error(f"Failed to get diagnostics for {provider_name}: {e}")
            return {"error": f"Failed to get diagnostics: {str(e)}"}
    
    def _calculate_health_score(self, provider_name: str) -> float:
        """Calculate overall health score for a provider (0-100)."""
        try:
            # Get current health status
            health_status = self.get_component_health(f"provider:{provider_name}")
            if not health_status:
                return 0.0
            
            # Base score from status
            if health_status.status == "healthy":
                base_score = 100.0
            elif health_status.status == "degraded":
                base_score = 70.0
            elif health_status.status == "unhealthy":
                base_score = 30.0
            else:
                base_score = 50.0  # unknown
            
            # Adjust based on performance metrics
            performance = self.performance_metrics.get(provider_name)
            if performance:
                # Factor in success rate
                success_penalty = (1.0 - performance.success_rate) * 30
                base_score -= success_penalty
                
                # Factor in response time
                if performance.average_response_time > 10.0:
                    base_score -= 20
                elif performance.average_response_time > 5.0:
                    base_score -= 10
                
                # Factor in consecutive failures
                if performance.consecutive_failures > 3:
                    base_score -= performance.consecutive_failures * 5
            
            return max(0.0, min(100.0, base_score))
            
        except Exception as e:
            logger.debug(f"Failed to calculate health score for {provider_name}: {e}")
            return 0.0
    
    def _test_api_key_validity(self, provider_name: str) -> bool:
        """Test if the API key for a provider is valid."""
        try:
            api_key = self._get_provider_api_key(provider_name)
            if not api_key:
                return False
            
            # Test with a minimal API call
            connectivity_result = self.test_provider_connectivity(provider_name)
            return connectivity_result.success and connectivity_result.status_code not in [401, 403]
            
        except Exception:
            return False
    
    def _check_missing_env_vars(self, provider_name: str) -> List[str]:
        """Check for missing environment variables."""
        try:
            provider_spec = self.registry._providers.get(provider_name)
            if not provider_spec:
                return []
            
            missing = []
            for env_var in provider_spec.required_env_vars:
                if not os.getenv(env_var):
                    missing.append(env_var)
            
            return missing
            
        except Exception:
            return []
    
    def _check_missing_dependencies(self, provider_name: str) -> List[str]:
        """Check for missing dependencies."""
        try:
            provider_spec = self.registry._providers.get(provider_name)
            if not provider_spec:
                return []
            
            missing = []
            for dependency in provider_spec.required_dependencies:
                try:
                    __import__(dependency)
                except ImportError:
                    missing.append(dependency)
            
            return missing
            
        except Exception:
            return []
    
    def _get_detailed_performance_diagnostics(self, provider_name: str, performance: Optional[PerformanceMetrics]) -> Dict[str, Any]:
        """Get detailed performance diagnostics."""
        if not performance:
            return {
                "status": "no_data",
                "message": "No performance data available"
            }
        
        return {
            "basic_metrics": {
                "total_requests": performance.total_requests,
                "success_rate": performance.success_rate,
                "error_rate": performance.error_rate,
                "average_response_time": performance.average_response_time,
                "requests_per_minute": performance.requests_per_minute,
            },
            "response_time_stats": {
                "min": performance.min_response_time if performance.min_response_time != float('inf') else 0,
                "max": performance.max_response_time,
                "average": performance.average_response_time,
                "p95": performance.p95_response_time,
                "p99": performance.p99_response_time,
            },
            "reliability_stats": {
                "consecutive_failures": performance.consecutive_failures,
                "consecutive_successes": performance.consecutive_successes,
                "last_failure": performance.last_failure_time.isoformat() if performance.last_failure_time else None,
                "last_success": performance.last_success_time.isoformat() if performance.last_success_time else None,
            },
            "error_breakdown": {
                "timeout_errors": performance.timeout_errors,
                "auth_errors": performance.auth_errors,
                "rate_limit_errors": performance.rate_limit_errors,
                "network_errors": performance.network_errors,
                "server_errors": performance.server_errors,
                "unknown_errors": performance.unknown_errors,
            },
            "trends": {
                "hourly_requests": performance.hourly_request_counts,
                "daily_success_rates": performance.daily_success_rates,
            },
        }
    
    def _calculate_uptime_percentage(self, provider_name: str) -> float:
        """Calculate uptime percentage based on recent history."""
        try:
            history = self.health_history.get(f"provider:{provider_name}", [])
            if not history:
                return 0.0
            
            # Look at last 24 hours of data
            cutoff = datetime.now() - timedelta(hours=24)
            recent_history = [h for h in history if datetime.fromtimestamp(h.last_check) > cutoff]
            
            if not recent_history:
                return 0.0
            
            healthy_count = sum(1 for h in recent_history if h.status == "healthy")
            return (healthy_count / len(recent_history)) * 100.0
            
        except Exception:
            return 0.0
    
    def _calculate_mtbf(self, provider_name: str) -> Optional[float]:
        """Calculate Mean Time Between Failures in hours."""
        try:
            history = self.health_history.get(f"provider:{provider_name}", [])
            if len(history) < 2:
                return None
            
            failure_times = []
            for h in history:
                if h.status in ["unhealthy", "degraded"]:
                    failure_times.append(datetime.fromtimestamp(h.last_check))
            
            if len(failure_times) < 2:
                return None
            
            # Calculate time between failures
            intervals = []
            for i in range(1, len(failure_times)):
                interval = (failure_times[i] - failure_times[i-1]).total_seconds() / 3600  # hours
                intervals.append(interval)
            
            return sum(intervals) / len(intervals) if intervals else None
            
        except Exception:
            return None
    
    def _calculate_mttr(self, provider_name: str) -> Optional[float]:
        """Calculate Mean Time To Recovery in minutes."""
        try:
            history = self.health_history.get(f"provider:{provider_name}", [])
            if len(history) < 2:
                return None
            
            recovery_times = []
            failure_start = None
            
            for h in history:
                timestamp = datetime.fromtimestamp(h.last_check)
                if h.status in ["unhealthy", "degraded"] and failure_start is None:
                    failure_start = timestamp
                elif h.status == "healthy" and failure_start is not None:
                    recovery_time = (timestamp - failure_start).total_seconds() / 60  # minutes
                    recovery_times.append(recovery_time)
                    failure_start = None
            
            return sum(recovery_times) / len(recovery_times) if recovery_times else None
            
        except Exception:
            return None
    
    def _get_common_issues(self, provider_name: str) -> List[str]:
        """Get common issues for a provider based on error patterns."""
        try:
            performance = self.performance_metrics.get(provider_name)
            if not performance:
                return []
            
            issues = []
            total_errors = performance.failed_requests
            
            if total_errors == 0:
                return ["No common issues detected"]
            
            # Analyze error patterns
            if performance.auth_errors > total_errors * 0.3:
                issues.append("Frequent authentication failures - check API key")
            
            if performance.rate_limit_errors > 0:
                issues.append("Rate limiting encountered - consider request throttling")
            
            if performance.network_errors > total_errors * 0.2:
                issues.append("Network connectivity issues - check internet connection")
            
            if performance.timeout_errors > total_errors * 0.2:
                issues.append("Request timeouts - provider may be overloaded")
            
            if performance.server_errors > total_errors * 0.1:
                issues.append("Server errors from provider - may be temporary outage")
            
            if performance.consecutive_failures > 5:
                issues.append("Extended failure period - manual intervention may be needed")
            
            return issues if issues else ["No specific patterns identified"]
            
        except Exception:
            return ["Error analyzing issue patterns"]
    
    def _get_troubleshooting_steps(self, provider_name: str, health_status: DetailedHealthStatus) -> List[str]:
        """Get specific troubleshooting steps based on current status."""
        steps = []
        
        if health_status.status == "unhealthy":
            steps.extend([
                "1. Check network connectivity to provider endpoints",
                "2. Verify API key is valid and has necessary permissions",
                "3. Check provider service status page for outages",
                "4. Review error logs for specific failure reasons",
            ])
        elif health_status.status == "degraded":
            steps.extend([
                "1. Monitor for improvement over next few minutes",
                "2. Check if specific models are unavailable",
                "3. Consider switching to alternative provider temporarily",
            ])
        else:
            steps.extend([
                "1. Continue monitoring - no immediate action needed",
                "2. Review performance metrics for optimization opportunities",
            ])
        
        # Add provider-specific steps
        if provider_name in ["llama_cpp", "transformers"]:
            steps.extend([
                "5. Check if model files exist and are readable",
                "6. Verify sufficient disk space and memory",
                "7. Check GPU availability if using GPU acceleration",
            ])
        else:
            steps.extend([
                "5. Check account usage limits and billing status",
                "6. Verify firewall/proxy settings allow API access",
            ])
        
        return steps
    
    def get_health_dashboard_data(self) -> Dict[str, Any]:
        """Get health dashboard data for UI consumption."""
        try:
            all_health = self.check_all_health()
            
            # Categorize components
            providers_health = {}
            runtimes_health = {}
            
            for component, status in all_health.items():
                if component.startswith("provider:"):
                    provider_name = component[9:]
                    providers_health[provider_name] = {
                        "status": status.status,
                        "connectivity": status.connectivity_status,
                        "models_available": len([m for m, available in status.model_availability.items() if available]),
                        "models_total": len(status.model_availability),
                        "capabilities": status.capability_status,
                        "response_time": status.response_time,
                        "error_message": status.error_message,
                        "ranking": self.provider_rankings.get(provider_name, 0.0),
                    }
                elif component.startswith("runtime:"):
                    runtime_name = component[8:]
                    runtimes_health[runtime_name] = {
                        "status": status.status,
                        "response_time": status.response_time,
                        "error_message": status.error_message,
                    }
            
            # Overall system health
            total_components = len(all_health)
            healthy_components = sum(1 for status in all_health.values() if status.status == "healthy")
            
            dashboard_data = {
                "system_overview": {
                    "total_components": total_components,
                    "healthy_components": healthy_components,
                    "health_percentage": (healthy_components / total_components * 100) if total_components > 0 else 0,
                    "last_updated": datetime.now().isoformat(),
                },
                "providers": providers_health,
                "runtimes": runtimes_health,
                "top_providers": self._get_top_providers(5),
                "recent_events": [
                    {
                        "component": event.component,
                        "old_status": event.old_status,
                        "new_status": event.new_status,
                        "timestamp": event.timestamp.isoformat(),
                        "error_message": event.error_message,
                    }
                    for event in self.get_recent_events(1)  # Last 1 hour
                ],
                "performance_summary": self._get_performance_summary(),
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {"error": f"Failed to get dashboard data: {str(e)}"}
    
    def _get_top_providers(self, limit: int) -> List[Dict[str, Any]]:
        """Get top-ranked providers."""
        sorted_providers = sorted(
            self.provider_rankings.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {
                "name": provider,
                "score": score,
                "status": self.get_component_health(f"provider:{provider}").status if self.get_component_health(f"provider:{provider}") else "unknown"
            }
            for provider, score in sorted_providers[:limit]
        ]
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all providers."""
        if not self.performance_metrics:
            return {}
        
        total_requests = sum(m.total_requests for m in self.performance_metrics.values())
        total_successful = sum(m.successful_requests for m in self.performance_metrics.values())
        avg_response_time = sum(m.average_response_time for m in self.performance_metrics.values()) / len(self.performance_metrics)
        
        return {
            "total_requests": total_requests,
            "overall_success_rate": (total_successful / total_requests) if total_requests > 0 else 0.0,
            "average_response_time": avg_response_time,
            "active_providers": len(self.performance_metrics),
        }
    
    def get_performance_metrics(self, provider_name: str) -> Optional[PerformanceMetrics]:
        """Get performance metrics for a specific provider."""
        return self.performance_metrics.get(provider_name)
    
    def get_all_performance_metrics(self) -> Dict[str, PerformanceMetrics]:
        """Get performance metrics for all providers."""
        return self.performance_metrics.copy()
    
    def get_performance_analytics(self, provider_name: str) -> Dict[str, Any]:
        """Get detailed performance analytics for a provider."""
        metrics = self.performance_metrics.get(provider_name)
        if not metrics:
            return {"error": f"No metrics available for {provider_name}"}
        
        # Calculate additional analytics
        analytics = {
            "provider_name": provider_name,
            "basic_metrics": {
                "total_requests": metrics.total_requests,
                "success_rate": metrics.success_rate,
                "error_rate": metrics.error_rate,
                "average_response_time": metrics.average_response_time,
                "requests_per_minute": metrics.requests_per_minute,
            },
            "response_time_stats": {
                "min": metrics.min_response_time if metrics.min_response_time != float('inf') else 0,
                "max": metrics.max_response_time,
                "average": metrics.average_response_time,
                "p95": metrics.p95_response_time,
                "p99": metrics.p99_response_time,
            },
            "reliability_stats": {
                "consecutive_failures": metrics.consecutive_failures,
                "consecutive_successes": metrics.consecutive_successes,
                "last_failure": metrics.last_failure_time.isoformat() if metrics.last_failure_time else None,
                "last_success": metrics.last_success_time.isoformat() if metrics.last_success_time else None,
            },
            "error_breakdown": {
                "timeout_errors": metrics.timeout_errors,
                "auth_errors": metrics.auth_errors,
                "rate_limit_errors": metrics.rate_limit_errors,
                "network_errors": metrics.network_errors,
                "server_errors": metrics.server_errors,
                "unknown_errors": metrics.unknown_errors,
            },
            "trends": {
                "hourly_requests": metrics.hourly_request_counts,
                "daily_success_rates": metrics.daily_success_rates,
            },
            "ranking": {
                "current_score": self.provider_rankings.get(provider_name, 0.0),
                "rank_among_providers": self._get_provider_rank(provider_name),
            },
            "recommendations": self._get_performance_recommendations(provider_name, metrics),
        }
        
        return analytics
    
    def _get_provider_rank(self, provider_name: str) -> int:
        """Get the rank of a provider among all providers (1 = best)."""
        sorted_providers = sorted(
            self.provider_rankings.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for rank, (name, score) in enumerate(sorted_providers, 1):
            if name == provider_name:
                return rank
        
        return len(sorted_providers) + 1  # Not found, worst rank
    
    def _get_performance_recommendations(self, provider_name: str, metrics: PerformanceMetrics) -> List[str]:
        """Get performance improvement recommendations for a provider."""
        recommendations = []
        
        # Response time recommendations
        if metrics.average_response_time > 10.0:
            recommendations.append("High response times detected - consider checking network connectivity")
        elif metrics.average_response_time > 5.0:
            recommendations.append("Moderate response times - monitor for network issues")
        
        # Success rate recommendations
        if metrics.success_rate < 0.8:
            recommendations.append("Low success rate - investigate error patterns and API configuration")
        elif metrics.success_rate < 0.95:
            recommendations.append("Success rate could be improved - check for intermittent issues")
        
        # Error pattern recommendations
        if metrics.auth_errors > metrics.total_requests * 0.1:
            recommendations.append("High authentication error rate - verify API key and permissions")
        
        if metrics.rate_limit_errors > 0:
            recommendations.append("Rate limiting detected - consider implementing request throttling")
        
        if metrics.network_errors > metrics.total_requests * 0.05:
            recommendations.append("Network errors detected - check connectivity and DNS resolution")
        
        if metrics.timeout_errors > metrics.total_requests * 0.05:
            recommendations.append("Timeout errors detected - consider increasing timeout values")
        
        # Consistency recommendations
        if metrics.consecutive_failures > 5:
            recommendations.append("Extended failure period detected - provider may need manual intervention")
        
        # Performance variance recommendations
        if len(metrics.response_time_history) > 10:
            import statistics
            try:
                variance = statistics.variance(metrics.response_time_history)
                if variance > 25.0:  # High variance in response times
                    recommendations.append("High response time variance - provider performance is inconsistent")
            except:
                pass
        
        if not recommendations:
            if metrics.success_rate > 0.98 and metrics.average_response_time < 2.0:
                recommendations.append("Excellent performance - no issues detected")
            else:
                recommendations.append("Performance is acceptable - continue monitoring")
        
        return recommendations
    
    def get_provider_rankings(self) -> Dict[str, float]:
        """Get current provider rankings based on performance."""
        return self.provider_rankings.copy()
    
    def clear_performance_metrics(self, provider_name: Optional[str] = None) -> None:
        """Clear performance metrics for a provider or all providers."""
        if provider_name:
            if provider_name in self.performance_metrics:
                del self.performance_metrics[provider_name]
            if provider_name in self.provider_rankings:
                del self.provider_rankings[provider_name]
            logger.info(f"Cleared performance metrics for {provider_name}")
        else:
            self.performance_metrics.clear()
            self.provider_rankings.clear()
            logger.info("Cleared all performance metrics")
    
    def record_request_metrics(self, provider_name: str, success: bool, response_time: float) -> None:
        """Record metrics for a provider request (for external use)."""
        if provider_name not in self.performance_metrics:
            self.performance_metrics[provider_name] = PerformanceMetrics()
        
        metrics = self.performance_metrics[provider_name]
        metrics.total_requests += 1
        
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        
        # Update rates
        if metrics.total_requests > 0:
            metrics.success_rate = metrics.successful_requests / metrics.total_requests
            metrics.error_rate = metrics.failed_requests / metrics.total_requests
        
        # Update response time (exponential moving average)
        if metrics.average_response_time == 0:
            metrics.average_response_time = response_time
        else:
            metrics.average_response_time = (0.9 * metrics.average_response_time + 
                                           0.1 * response_time)
        
        metrics.last_updated = datetime.now()
        
        # Update ranking
        self._update_provider_rankings()
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get health cache statistics."""
        total_cached = len(self.health_cache)
        valid_cached = sum(1 for key in self.health_cache.keys() if self._is_cache_valid(key))
        
        return {
            "total_cached_entries": total_cached,
            "valid_cached_entries": valid_cached,
            "cache_hit_rate": (valid_cached / total_cached) if total_cached > 0 else 0.0,
            "cache_ttl_seconds": self.cache_ttl,
        }
    
    def clear_health_cache(self, component: Optional[str] = None) -> None:
        """Clear health cache for a component or all components."""
        if component:
            if component in self.health_cache:
                del self.health_cache[component]
            if component in self.cache_timestamps:
                del self.cache_timestamps[component]
            logger.info(f"Cleared health cache for {component}")
        else:
            self.health_cache.clear()
            self.cache_timestamps.clear()
            logger.info("Cleared all health cache")
    
    def get_system_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive system diagnostics."""
        try:
            all_health = self.check_all_health()
            
            # Count components by status
            status_counts = {"healthy": 0, "unhealthy": 0, "degraded": 0, "unknown": 0}
            for status in all_health.values():
                status_counts[status.status] = status_counts.get(status.status, 0) + 1
            
            # Get provider-specific diagnostics
            provider_diagnostics = {}
            for provider_name in self.registry.list_providers():
                provider_diagnostics[provider_name] = self.get_provider_diagnostics(provider_name)
            
            # Get runtime diagnostics
            runtime_diagnostics = {}
            for runtime_name in self.registry.list_runtimes():
                runtime_health = all_health.get(f"runtime:{runtime_name}")
                if runtime_health:
                    runtime_diagnostics[runtime_name] = {
                        "status": runtime_health.status,
                        "response_time": runtime_health.response_time,
                        "error_message": runtime_health.error_message,
                        "last_check": runtime_health.last_check,
                    }
            
            diagnostics = {
                "timestamp": datetime.now().isoformat(),
                "monitoring_active": self.monitoring_active,
                "check_interval": self.check_interval,
                "system_overview": {
                    "total_components": len(all_health),
                    "status_breakdown": status_counts,
                    "health_percentage": (status_counts["healthy"] / len(all_health) * 100) if all_health else 0,
                },
                "providers": provider_diagnostics,
                "runtimes": runtime_diagnostics,
                "performance_summary": self._get_performance_summary(),
                "cache_statistics": self.get_cache_statistics(),
                "recent_events_count": len(self.get_recent_events(24)),
                "recent_failovers_count": len(self.get_recent_failovers(24)),
                "configuration": {
                    "failure_threshold": self.failure_threshold,
                    "recovery_threshold": self.recovery_threshold,
                    "auto_failover_enabled": self.enable_auto_failover,
                    "cache_ttl": self.cache_ttl,
                    "connectivity_timeout": self.connectivity_timeout,
                    "model_test_timeout": self.model_test_timeout,
                },
            }
            
            return diagnostics
            
        except Exception as e:
            logger.error(f"Failed to get system diagnostics: {e}")
            return {"error": f"Failed to get system diagnostics: {str(e)}"}
    
    def get_health_report(self, include_history: bool = False) -> Dict[str, Any]:
        """Generate a comprehensive health report."""
        try:
            report = {
                "report_timestamp": datetime.now().isoformat(),
                "system_status": self.get_health_summary(),
                "component_health": {},
                "performance_metrics": self.get_all_performance_metrics(),
                "provider_rankings": self.get_provider_rankings(),
                "recent_events": [
                    {
                        "component": event.component,
                        "old_status": event.old_status,
                        "new_status": event.new_status,
                        "timestamp": event.timestamp.isoformat(),
                        "error_message": event.error_message,
                        "response_time": event.response_time,
                    }
                    for event in self.get_recent_events(24)
                ],
                "recent_failovers": [
                    {
                        "from_component": event.from_component,
                        "to_component": event.to_component,
                        "reason": event.reason,
                        "timestamp": event.timestamp.isoformat(),
                        "success": event.success,
                    }
                    for event in self.get_recent_failovers(24)
                ],
            }
            
            # Add detailed component health
            all_health = self.check_all_health()
            for component, status in all_health.items():
                report["component_health"][component] = {
                    "status": status.status,
                    "connectivity_status": status.connectivity_status,
                    "response_time": status.response_time,
                    "error_message": status.error_message,
                    "model_availability": status.model_availability,
                    "capability_status": status.capability_status,
                    "recovery_suggestions": status.recovery_suggestions,
                    "last_check": status.last_check,
                }
                
                # Add history if requested
                if include_history:
                    history = self.get_health_history(component, limit=20)
                    report["component_health"][component]["recent_history"] = [
                        {
                            "status": h.status,
                            "timestamp": h.last_check,
                            "response_time": h.response_time,
                            "error_message": h.error_message,
                        }
                        for h in history
                    ]
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate health report: {e}")
            return {"error": f"Failed to generate health report: {str(e)}"}
    
    def add_health_status_notification(self, callback: Callable[[str, DetailedHealthStatus], None]) -> None:
        """Add a callback for health status notifications."""
        def wrapper(event: HealthEvent):
            try:
                # Get current detailed status
                current_status = self.get_component_health(event.component)
                if current_status:
                    callback(event.component, current_status)
            except Exception as e:
                logger.error(f"Health status notification callback error: {e}")
        
        self.add_health_change_callback(wrapper)
    
    def log_health_status_change(self, component: str, old_status: str, new_status: str, 
                                error_message: Optional[str] = None) -> None:
        """Log health status change with appropriate log level."""
        if new_status == "healthy" and old_status in ["unhealthy", "degraded"]:
            logger.info(f"✅ {component} recovered: {old_status} → {new_status}")
        elif new_status in ["unhealthy", "degraded"] and old_status == "healthy":
            logger.warning(f"⚠️  {component} degraded: {old_status} → {new_status}")
            if error_message:
                logger.warning(f"   Error: {error_message}")
        elif new_status == "unhealthy":
            logger.error(f"❌ {component} failed: {old_status} → {new_status}")
            if error_message:
                logger.error(f"   Error: {error_message}")
        else:
            logger.info(f"ℹ️  {component} status change: {old_status} → {new_status}")
    
    def get_troubleshooting_suggestions(self, component: str) -> List[str]:
        """Get troubleshooting suggestions for a component."""
        suggestions = []
        
        try:
            status = self.get_component_health(component)
            if not status:
                return ["Component not found or not monitored"]
            
            if status.status == "healthy":
                return ["Component is healthy - no troubleshooting needed"]
            
            # Add existing recovery suggestions
            suggestions.extend(status.recovery_suggestions)
            
            # Add component-specific suggestions
            if component.startswith("provider:"):
                provider_name = component[9:]
                
                # API key suggestions
                if not self._get_provider_api_key(provider_name):
                    suggestions.append(f"Set {provider_name.upper()}_API_KEY environment variable")
                
                # Connectivity suggestions
                if status.connectivity_status == "unhealthy":
                    suggestions.extend([
                        "Check internet connectivity",
                        "Verify API endpoint is accessible",
                        "Check firewall and proxy settings",
                        "Validate API key permissions",
                    ])
                
                # Model availability suggestions
                if not any(status.model_availability.values()):
                    suggestions.extend([
                        "Check API key has access to models",
                        "Verify account subscription/credits",
                        "Try different model names",
                    ])
                
                # Provider-specific suggestions
                if provider_name == "openai":
                    suggestions.extend([
                        "Check OpenAI service status at status.openai.com",
                        "Verify API key format (starts with sk-)",
                        "Check usage limits and billing",
                    ])
                elif provider_name == "gemini":
                    suggestions.extend([
                        "Check Google AI service status",
                        "Verify API key is for Gemini API",
                        "Enable Gemini API in Google Cloud Console",
                    ])
                elif provider_name in ["llama_cpp", "transformers"]:
                    suggestions.extend([
                        "Check if model files exist in models directory",
                        "Verify model file format (GGUF for llama.cpp)",
                        "Check available disk space",
                        "Verify model file permissions",
                    ])
            
            elif component.startswith("runtime:"):
                runtime_name = component[8:]
                suggestions.extend([
                    f"Check {runtime_name} installation",
                    "Verify runtime dependencies",
                    "Check system resources (CPU, memory, GPU)",
                    "Review runtime configuration",
                ])
            
            # Remove duplicates while preserving order
            seen = set()
            unique_suggestions = []
            for suggestion in suggestions:
                if suggestion not in seen:
                    seen.add(suggestion)
                    unique_suggestions.append(suggestion)
            
            return unique_suggestions
            
        except Exception as e:
            logger.error(f"Failed to get troubleshooting suggestions for {component}: {e}")
            return [f"Error getting suggestions: {str(e)}"]
    
    def get_healthy_components(self, component_type: Optional[str] = None) -> List[str]:
        """Get list of healthy components."""
        if component_type == "provider":
            return self.registry.get_healthy_providers()
        elif component_type == "runtime":
            return self.registry.get_healthy_runtimes()
        else:
            # Return all healthy components
            healthy = []
            healthy.extend([f"provider:{p}" for p in self.registry.get_healthy_providers()])
            healthy.extend([f"runtime:{r}" for r in self.registry.get_healthy_runtimes()])
            return healthy
    
    def get_unhealthy_components(self) -> Dict[str, DetailedHealthStatus]:
        """Get all unhealthy components."""
        unhealthy = {}
        all_health = self.check_all_health()
        
        for component, status in all_health.items():
            if status.status in ["unhealthy", "degraded"]:
                unhealthy[component] = status
        
        return unhealthy
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary."""
        all_health = self.registry.health_check_all()
        
        summary = {
            "total_components": len(all_health),
            "healthy_components": 0,
            "unhealthy_components": 0,
            "unknown_components": 0,
            "degraded_components": 0,
            "providers": {
                "total": len(self.registry.list_providers()),
                "healthy": len(self.registry.get_healthy_providers()),
            },
            "runtimes": {
                "total": len(self.registry.list_runtimes()),
                "healthy": len(self.registry.get_healthy_runtimes()),
            },
            "recent_events": len([e for e in self.health_events if e.timestamp > datetime.now() - timedelta(hours=1)]),
            "recent_failovers": len([f for f in self.failover_events if f.timestamp > datetime.now() - timedelta(hours=1)]),
        }
        
        # Count by status
        for status in all_health.values():
            if status.status == "healthy":
                summary["healthy_components"] += 1
            elif status.status == "unhealthy":
                summary["unhealthy_components"] += 1
            elif status.status == "degraded":
                summary["degraded_components"] += 1
            else:
                summary["unknown_components"] += 1
        
        return summary
    
    def get_health_history(self, component: str, limit: int = 50) -> List[DetailedHealthStatus]:
        """Get health history for a component."""
        history = self.health_history.get(component, [])
        return history[-limit:] if limit else history
    
    def get_recent_events(self, hours: int = 24) -> List[HealthEvent]:
        """Get recent health events."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [event for event in self.health_events if event.timestamp > cutoff]
    
    def get_recent_failovers(self, hours: int = 24) -> List[FailoverEvent]:
        """Get recent failover events."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [event for event in self.failover_events if event.timestamp > cutoff]
    
    def add_health_change_callback(self, callback: Callable[[HealthEvent], None]) -> None:
        """Add a callback for health status changes."""
        self.health_change_callbacks.append(callback)
    
    def add_failover_callback(self, callback: Callable[[FailoverEvent], None]) -> None:
        """Add a callback for failover events."""
        self.failover_callbacks.append(callback)
    
    def force_health_check(self, component: str) -> DetailedHealthStatus:
        """Force an immediate health check for a specific component."""
        # Clear cache to force fresh check
        if component in self.health_cache:
            del self.health_cache[component]
        if component in self.cache_timestamps:
            del self.cache_timestamps[component]
        
        # Perform fresh health check
        if component.startswith("provider:"):
            provider_name = component[9:]
            return self.check_provider_health(provider_name)
        elif component.startswith("runtime:"):
            runtime_name = component[8:]
            return self._check_runtime_health(runtime_name)
        else:
            # Try to determine component type
            if component in self.registry.list_providers():
                return self.check_provider_health(component)
            elif component in self.registry.list_runtimes():
                return self._check_runtime_health(component)
            else:
                return DetailedHealthStatus(
                    status="not_found",
                    error_message=f"Component {component} not found",
                    last_check=time.time()
                )
    
    def reset_failure_count(self, component: str) -> None:
        """Reset failure count for a component (useful for manual recovery)."""
        self.failure_counts[component] = 0
        self.recovery_counts[component] = 0
        logger.info(f"Reset failure count for {component}")
    
    def is_component_healthy(self, component: str) -> bool:
        """Check if a component is currently healthy."""
        status = self.get_component_health(component)
        return status is None or status.status in ["healthy", "unknown"]
    
    def get_best_alternative(self, failed_component: str) -> Optional[str]:
        """Get the best healthy alternative for a failed component."""
        if failed_component.startswith("provider:"):
            alternatives = self.registry.get_healthy_providers()
            component_name = failed_component[9:]
            return next((alt for alt in alternatives if alt != component_name), None)
        elif failed_component.startswith("runtime:"):
            alternatives = self.registry.get_healthy_runtimes()
            component_name = failed_component[8:]
            return next((alt for alt in alternatives if alt != component_name), None)
        else:
            return None


# Global health monitor instance
_global_health_monitor: Optional[ComprehensiveHealthMonitor] = None
_health_monitor_lock = threading.RLock()


def get_health_monitor() -> ComprehensiveHealthMonitor:
    """Get the global health monitor instance."""
    global _global_health_monitor
    if _global_health_monitor is None:
        with _health_monitor_lock:
            if _global_health_monitor is None:
                _global_health_monitor = ComprehensiveHealthMonitor()
    return _global_health_monitor


def initialize_health_monitor(**kwargs) -> ComprehensiveHealthMonitor:
    """Initialize a fresh global health monitor."""
    global _global_health_monitor
    with _health_monitor_lock:
        _global_health_monitor = ComprehensiveHealthMonitor(**kwargs)
    return _global_health_monitor


# Maintain backward compatibility
HealthMonitor = ComprehensiveHealthMonitor


# Convenience functions
def start_health_monitoring() -> None:
    """Start global health monitoring."""
    get_health_monitor().start_monitoring()


def stop_health_monitoring() -> None:
    """Stop global health monitoring."""
    if _global_health_monitor:
        _global_health_monitor.stop_monitoring()


def get_health_summary() -> Dict[str, Any]:
    """Get global health summary."""
    return get_health_monitor().get_health_summary()


def is_healthy(component: str) -> bool:
    """Check if a component is healthy."""
    return get_health_monitor().is_component_healthy(component)


__all__ = [
    "PerformanceMetrics",
    "ConnectivityResult",
    "ModelAvailabilityResult", 
    "CapabilityDetectionResult",
    "DetailedHealthStatus",
    "HealthEvent",
    "FailoverEvent", 
    "ComprehensiveHealthMonitor",
    "HealthMonitor",  # Backward compatibility
    "get_health_monitor",
    "initialize_health_monitor",
    "start_health_monitoring",
    "stop_health_monitoring",
    "get_health_summary",
    "is_healthy",
]