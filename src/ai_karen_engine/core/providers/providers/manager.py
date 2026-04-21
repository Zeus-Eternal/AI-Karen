"""
Provider Manager for the production chat system.
Manages multiple LLM providers with fallback mechanisms and load balancing.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum

from .base import BaseLLMProvider, AIRequest, AIResponse, AIStreamChunk, ProviderStatus
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .gemini import GeminiProvider
from .local import LocalModelProvider

logger = logging.getLogger(__name__)


class ProviderState(Enum):
    """Provider state enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class ProviderMetrics:
    """Provider performance metrics."""
    provider_id: str
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    uptime_percentage: float = 100.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.request_count == 0:
            return 1.0
        return self.success_count / self.request_count
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        return 1.0 - self.success_rate
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time."""
        if self.success_count == 0:
            return 0.0
        return self.total_response_time / self.success_count


@dataclass
class FallbackConfig:
    """Fallback configuration for providers."""
    provider_id: str
    priority: int = 0
    enabled: bool = True
    max_consecutive_failures: int = 3
    cooldown_minutes: int = 5
    retry_after_minutes: int = 30


class ProviderManager:
    """Manager for LLM providers with fallback and load balancing."""
    
    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._provider_configs: Dict[str, Dict[str, Any]] = {}
        self._provider_metrics: Dict[str, ProviderMetrics] = {}
        self._fallback_configs: Dict[str, FallbackConfig] = {}
        self._provider_states: Dict[str, ProviderState] = {}
        self._cooldown_until: Dict[str, datetime] = {}
        self._current_primary: Optional[str] = None
        self._health_check_interval: int = 60  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        # Provider factory mapping
        self._provider_factory = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "gemini": GeminiProvider,
            "local": LocalModelProvider,
        }
    
    async def add_provider(
        self, 
        provider_id: str, 
        provider_type: str, 
        config: Dict[str, Any],
        fallback_config: Optional[FallbackConfig] = None
    ) -> bool:
        """Add a new provider to the manager."""
        try:
            async with self._lock:
                if provider_id in self._providers:
                    logger.warning(f"Provider {provider_id} already exists")
                    return False
                
                # Create provider instance
                provider_class = self._provider_factory.get(provider_type)
                if not provider_class:
                    logger.error(f"Unknown provider type: {provider_type}")
                    return False
                
                provider = provider_class(provider_id, config)
                
                # Configure the provider
                await provider.configure(config)
                
                # Store provider and configuration
                self._providers[provider_id] = provider
                self._provider_configs[provider_id] = config
                self._provider_metrics[provider_id] = ProviderMetrics(provider_id=provider_id)
                self._provider_states[provider_id] = ProviderState.ACTIVE
                
                # Set fallback configuration
                if fallback_config:
                    self._fallback_configs[provider_id] = fallback_config
                
                # Set as primary if first provider
                if not self._current_primary:
                    self._current_primary = provider_id
                
                logger.info(f"Added provider {provider_id} of type {provider_type}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add provider {provider_id}: {e}")
            return False
    
    async def remove_provider(self, provider_id: str) -> bool:
        """Remove a provider from the manager."""
        try:
            async with self._lock:
                if provider_id not in self._providers:
                    logger.warning(f"Provider {provider_id} not found")
                    return False
                
                del self._providers[provider_id]
                del self._provider_configs[provider_id]
                del self._provider_metrics[provider_id]
                del self._provider_states[provider_id]
                del self._fallback_configs[provider_id]
                
                if provider_id in self._cooldown_until:
                    del self._cooldown_until[provider_id]
                
                # Update primary if necessary
                if self._current_primary == provider_id:
                    self._current_primary = self._get_next_available_provider()
                
                logger.info(f"Removed provider {provider_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to remove provider {provider_id}: {e}")
            return False
    
    async def update_provider_config(
        self, 
        provider_id: str, 
        config: Dict[str, Any]
    ) -> bool:
        """Update provider configuration."""
        try:
            async with self._lock:
                if provider_id not in self._providers:
                    logger.warning(f"Provider {provider_id} not found")
                    return False
                
                provider = self._providers[provider_id]
                await provider.configure(config)
                self._provider_configs[provider_id] = config
                
                logger.info(f"Updated configuration for provider {provider_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update config for provider {provider_id}: {e}")
            return False
    
    async def get_provider(self, provider_id: str) -> Optional[BaseLLMProvider]:
        """Get a specific provider by ID."""
        return self._providers.get(provider_id)
    
    async def get_primary_provider(self) -> Optional[BaseLLMProvider]:
        """Get the current primary provider."""
        if not self._current_primary:
            self._current_primary = self._get_next_available_provider()
        
        if self._current_primary:
            return self._providers.get(self._current_primary)
        return None
    
    async def set_primary_provider(self, provider_id: str) -> bool:
        """Set the primary provider."""
        try:
            async with self._lock:
                if provider_id not in self._providers:
                    logger.warning(f"Provider {provider_id} not found")
                    return False
                
                if self._provider_states[provider_id] != ProviderState.ACTIVE:
                    logger.warning(f"Provider {provider_id} is not active")
                    return False
                
                self._current_primary = provider_id
                logger.info(f"Set primary provider to {provider_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to set primary provider {provider_id}: {e}")
            return False
    
    async def list_providers(self) -> List[Dict[str, Any]]:
        """List all providers with their status and metrics."""
        result = []
        
        for provider_id, provider in self._providers.items():
            metrics = self._provider_metrics.get(provider_id)
            state = self._provider_states.get(provider_id)
            config = self._fallback_configs.get(provider_id)
            
            provider_info = {
                "provider_id": provider_id,
                "provider_type": provider.__class__.__name__,
                "state": state.value if state else "unknown",
                "metrics": {
                    "request_count": metrics.request_count if metrics else 0,
                    "success_count": metrics.success_count if metrics else 0,
                    "error_count": metrics.error_count if metrics else 0,
                    "success_rate": metrics.success_rate if metrics else 1.0,
                    "error_rate": metrics.error_rate if metrics else 0.0,
                    "average_response_time": metrics.average_response_time if metrics else 0.0,
                    "uptime_percentage": metrics.uptime_percentage if metrics else 100.0,
                    "last_request_time": metrics.last_request_time.isoformat() if metrics and metrics.last_request_time else None,
                    "last_error": metrics.last_error if metrics else None,
                    "consecutive_failures": metrics.consecutive_failures if metrics else 0,
                },
                "fallback_config": {
                    "priority": config.priority if config else 0,
                    "enabled": config.enabled if config else True,
                    "max_consecutive_failures": config.max_consecutive_failures if config else 3,
                    "cooldown_minutes": config.cooldown_minutes if config else 5,
                    "retry_after_minutes": config.retry_after_minutes if config else 30,
                } if config else None,
                "is_primary": provider_id == self._current_primary,
                "is_available": self._is_provider_available(provider_id),
            }
            
            result.append(provider_info)
        
        return result
    
    async def execute_with_fallback(
        self, 
        request: AIRequest,
        preferred_provider_id: Optional[str] = None
    ) -> AIResponse:
        """Execute request with automatic fallback to other providers."""
        start_time = time.time()
        
        # Determine provider order
        provider_order = self._get_provider_order(preferred_provider_id)
        
        last_error = None
        
        for provider_id in provider_order:
            try:
                # Check if provider is available
                if not self._is_provider_available(provider_id):
                    logger.info(f"Provider {provider_id} is not available, skipping")
                    continue
                
                provider = self._providers[provider_id]
                logger.info(f"Attempting request with provider: {provider_id}")
                
                # Update metrics
                metrics = self._provider_metrics[provider_id]
                metrics.request_count += 1
                metrics.last_request_time = datetime.utcnow()
                
                # Execute request
                response = await provider.complete(request)
                
                # Update success metrics
                execution_time = time.time() - start_time
                metrics.success_count += 1
                metrics.total_response_time += response.response_time or execution_time
                metrics.consecutive_failures = 0
                metrics.last_error = None
                
                # Update provider state
                self._provider_states[provider_id] = ProviderState.ACTIVE
                
                logger.info(f"Request successful with provider: {provider_id}")
                return response
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Provider {provider_id} failed: {last_error}")
                
                # Update error metrics
                metrics = self._provider_metrics[provider_id]
                metrics.error_count += 1
                metrics.consecutive_failures += 1
                metrics.last_error = last_error
                
                # Update provider state
                fallback_config = self._fallback_configs.get(provider_id)
                if fallback_config and metrics.consecutive_failures >= fallback_config.max_consecutive_failures:
                    self._provider_states[provider_id] = ProviderState.ERROR
                    self._cooldown_until[provider_id] = datetime.utcnow() + timedelta(minutes=fallback_config.cooldown_minutes)
                    logger.warning(f"Provider {provider_id} marked as error, entering cooldown")
                else:
                    self._provider_states[provider_id] = ProviderState.DEGRADED
        
        # All providers failed
        error_msg = f"All providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    async def stream_with_fallback(
        self, 
        request: AIRequest,
        preferred_provider_id: Optional[str] = None
    ) -> AsyncGenerator[AIStreamChunk, None]:
        """Stream request with automatic fallback to other providers."""
        start_time = time.time()
        
        # Determine provider order
        provider_order = self._get_provider_order(preferred_provider_id)
        
        last_error = None
        
        for provider_id in provider_order:
            try:
                # Check if provider is available
                if not self._is_provider_available(provider_id):
                    logger.info(f"Provider {provider_id} is not available for streaming, skipping")
                    continue
                
                provider = self._providers[provider_id]
                logger.info(f"Attempting stream with provider: {provider_id}")
                
                # Update metrics
                metrics = self._provider_metrics[provider_id]
                metrics.request_count += 1
                metrics.last_request_time = datetime.utcnow()
                
                # Stream request
                async for chunk in provider.stream(request):
                    # Update success metrics on first chunk
                    if metrics.consecutive_failures > 0:
                        metrics.consecutive_failures = 0
                        metrics.last_error = None
                        self._provider_states[provider_id] = ProviderState.ACTIVE
                    
                    yield chunk
                
                # Update success metrics
                execution_time = time.time() - start_time
                metrics.success_count += 1
                metrics.total_response_time += execution_time
                metrics.consecutive_failures = 0
                metrics.last_error = None
                
                # Update provider state
                self._provider_states[provider_id] = ProviderState.ACTIVE
                
                logger.info(f"Stream successful with provider: {provider_id}")
                return
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Provider {provider_id} streaming failed: {last_error}")
                
                # Update error metrics
                metrics = self._provider_metrics[provider_id]
                metrics.error_count += 1
                metrics.consecutive_failures += 1
                metrics.last_error = last_error
                
                # Update provider state
                fallback_config = self._fallback_configs.get(provider_id)
                if fallback_config and metrics.consecutive_failures >= fallback_config.max_consecutive_failures:
                    self._provider_states[provider_id] = ProviderState.ERROR
                    self._cooldown_until[provider_id] = datetime.utcnow() + timedelta(minutes=fallback_config.cooldown_minutes)
                    logger.warning(f"Provider {provider_id} marked as error, entering cooldown")
                else:
                    self._provider_states[provider_id] = ProviderState.DEGRADED
        
        # All providers failed
        error_msg = f"All providers failed for streaming. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    async def start_health_monitoring(self) -> None:
        """Start background health monitoring for all providers."""
        if self._health_check_task:
            return
        
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Started provider health monitoring")
    
    async def stop_health_monitoring(self) -> None:
        """Stop background health monitoring."""
        if self._health_check_task:
            self._health_check_task.cancel()
            self._health_check_task = None
            logger.info("Stopped provider health monitoring")
    
    async def _health_check_loop(self) -> None:
        """Background loop for health checks."""
        while True:
            try:
                await asyncio.sleep(self._health_check_interval)
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
    
    async def _perform_health_checks(self) -> None:
        """Perform health checks on all providers."""
        tasks = []
        
        for provider_id, provider in self._providers.items():
            if self._provider_states[provider_id] != ProviderState.INACTIVE:
                tasks.append(self._check_provider_health(provider_id, provider))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_provider_health(self, provider_id: str, provider: BaseLLMProvider) -> None:
        """Check health of a specific provider."""
        try:
            status = await provider.get_status()
            
            # Update provider state based on health check
            if status.is_healthy:
                if self._provider_states[provider_id] == ProviderState.ERROR:
                    # Provider recovered from error
                    self._provider_states[provider_id] = ProviderState.ACTIVE
                    logger.info(f"Provider {provider_id} recovered from error state")
            elif status.is_available:
                self._provider_states[provider_id] = ProviderState.ACTIVE
            else:
                self._provider_states[provider_id] = ProviderState.DEGRADED
            else:
                self._provider_states[provider_id] = ProviderState.ERROR
                
        except Exception as e:
            logger.error(f"Health check failed for provider {provider_id}: {e}")
            self._provider_states[provider_id] = ProviderState.ERROR
    
    def _is_provider_available(self, provider_id: str) -> bool:
        """Check if a provider is available for requests."""
        # Check if provider exists
        if provider_id not in self._providers:
            return False
        
        # Check if provider is active
        state = self._provider_states.get(provider_id)
        if state in [ProviderState.INACTIVE, ProviderState.MAINTENANCE]:
            return False
        
        # Check if provider is in cooldown
        if provider_id in self._cooldown_until:
            if datetime.utcnow() < self._cooldown_until[provider_id]:
                return False
            else:
                del self._cooldown_until[provider_id]
        
        # Check fallback configuration
        fallback_config = self._fallback_configs.get(provider_id)
        if fallback_config and not fallback_config.enabled:
            return False
        
        return True
    
    def _get_provider_order(self, preferred_provider_id: Optional[str] = None) -> List[str]:
        """Get ordered list of providers for fallback."""
        available_providers = []
        
        for provider_id, fallback_config in self._fallback_configs.items():
            if self._is_provider_available(provider_id):
                available_providers.append((provider_id, fallback_config.priority or 0))
        
        # Sort by priority (higher priority first)
        available_providers.sort(key=lambda x: x[1], reverse=True)
        
        # If preferred provider is available, put it first
        if preferred_provider_id and self._is_provider_available(preferred_provider_id):
            provider_order = [preferred_provider_id]
            provider_order.extend([pid for pid, _ in available_providers if pid != preferred_provider_id])
        else:
            provider_order = [pid for pid, _ in available_providers]
        
        return provider_order
    
    def _get_next_available_provider(self) -> Optional[str]:
        """Get the next available provider."""
        provider_order = self._get_provider_order()
        return provider_order[0] if provider_order else None