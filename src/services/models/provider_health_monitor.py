"""
Provider Health Monitor

This service monitors the health of model providers.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import time


class ProviderHealthStatus(Enum):
    """Provider health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ProviderHealthInfo:
    """Information about provider health."""
    provider_id: str
    status: ProviderHealthStatus
    latency_ms: int = 0
    error_rate: float = 0.0
    last_check: float = 0
    uptime_percent: float = 100.0
    error_message: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)


class ProviderHealthMonitor:
    """
    Provider Health Monitor monitors the health of model providers.
    
    This service provides health checking, metrics collection, and
    status reporting for all model providers.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Provider Health Monitor.
        
        Args:
            config: Configuration for the health monitor
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Provider health tracking
        self.provider_health: Dict[str, ProviderHealthInfo] = {}
        
        # Configuration
        self.check_interval = config.get("check_interval", 60)  # seconds
        self.timeout = config.get("timeout", 10)  # seconds
        self.healthy_threshold = config.get("healthy_threshold", 0.95)  # 95% uptime
        self.degraded_threshold = config.get("degraded_threshold", 0.8)  # 80% uptime
        
        # Start health checker
        self.health_checker_task = asyncio.create_task(self._health_checker_loop())
    
    async def _health_checker_loop(self):
        """Background task to check provider health."""
        while True:
            try:
                await self._check_all_providers()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error in health checker loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_all_providers(self):
        """Check health of all providers."""
        for provider_id in self.provider_health:
            await self._check_provider_health(provider_id)
    
    async def _check_provider_health(self, provider_id: str):
        """Check health of a specific provider."""
        health_info = self.provider_health.get(provider_id)
        if not health_info:
            return
        
        try:
            # Perform health check
            start_time = time.time()
            
            # Implementation would perform actual health check
            # For now, simulate health check
            is_healthy = await self._perform_health_check(provider_id)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            health_info.latency_ms = latency_ms
            
            # Update status based on health check
            if is_healthy:
                # Update uptime
                health_info.uptime_percent = self._calculate_uptime(provider_id)
                
                # Determine status based on uptime
                if health_info.uptime_percent >= self.healthy_threshold:
                    health_info.status = ProviderHealthStatus.HEALTHY
                elif health_info.uptime_percent >= self.degraded_threshold:
                    health_info.status = ProviderHealthStatus.DEGRADED
                else:
                    health_info.status = ProviderHealthStatus.UNHEALTHY
            else:
                health_info.status = ProviderHealthStatus.UNHEALTHY
                health_info.error_message = "Health check failed"
            
            health_info.last_check = time.time()
            
        except Exception as e:
            health_info.status = ProviderHealthStatus.UNHEALTHY
            health_info.error_message = str(e)
            self.logger.error(f"Error checking provider health {provider_id}: {e}")
    
    async def _perform_health_check(self, provider_id: str) -> bool:
        """Perform health check for a provider."""
        # Implementation would perform actual health check
        # For now, return True
        return True
    
    def _calculate_uptime(self, provider_id: str) -> float:
        """Calculate uptime percentage for a provider."""
        # Implementation would calculate actual uptime
        # For now, return mock value
        return 0.99
    
    def register_provider(self, provider_id: str):
        """
        Register a provider for health monitoring.
        
        Args:
            provider_id: The provider ID to register
        """
        if provider_id not in self.provider_health:
            self.provider_health[provider_id] = ProviderHealthInfo(
                provider_id=provider_id,
                status=ProviderHealthStatus.UNKNOWN
            )
            self.logger.info(f"Registered provider for health monitoring: {provider_id}")
    
    def unregister_provider(self, provider_id: str):
        """
        Unregister a provider from health monitoring.
        
        Args:
            provider_id: The provider ID to unregister
        """
        if provider_id in self.provider_health:
            del self.provider_health[provider_id]
            self.logger.info(f"Unregistered provider from health monitoring: {provider_id}")
    
    async def get_provider_health(self, provider_id: str) -> Optional[ProviderHealthInfo]:
        """
        Get health information for a provider.
        
        Args:
            provider_id: The provider ID
            
        Returns:
            Provider health information if found, None otherwise
        """
        return self.provider_health.get(provider_id)
    
    async def get_healthy_providers(self) -> List[str]:
        """
        Get all healthy providers.
        
        Returns:
            List of healthy provider IDs
        """
        return [
            provider_id for provider_id, health_info in self.provider_health.items()
            if health_info.status == ProviderHealthStatus.HEALTHY
        ]
    
    async def get_provider_status_summary(self) -> Dict[str, Any]:
        """
        Get a summary of provider statuses.
        
        Returns:
            Dictionary of status summary
        """
        status_counts = {}
        for status in ProviderHealthStatus:
            status_counts[status.value] = sum(
                1 for health_info in self.provider_health.values()
                if health_info.status == status
            )
        
        avg_latency = 0
        if self.provider_health:
            avg_latency = sum(
                health_info.latency_ms for health_info in self.provider_health.values()
            ) / len(self.provider_health)
        
        return {
            "total_providers": len(self.provider_health),
            "status_counts": status_counts,
            "average_latency_ms": avg_latency,
            "check_interval": self.check_interval
        }
    
    async def force_health_check(self, provider_id: str) -> bool:
        """
        Force a health check for a provider.
        
        Args:
            provider_id: The provider ID to check
            
        Returns:
            True if the check was performed, False otherwise
        """
        if provider_id not in self.provider_health:
            return False
        
        await self._check_provider_health(provider_id)
        return True
    
    async def close(self):
        """Close the health monitor."""
        # Cancel health checker task
        if self.health_checker_task:
            self.health_checker_task.cancel()
            try:
                await self.health_checker_task
            except asyncio.CancelledError:
                pass
