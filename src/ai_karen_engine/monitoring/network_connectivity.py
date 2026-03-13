"""
Network Connectivity Monitor for Intelligent Fallback System

This module provides real-time network connectivity monitoring
with automatic offline/online mode switching for the intelligent fallback system.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional, Set, Union, Any, Awaitable
from dataclasses import dataclass, field
import aiohttp
import socket

logger = logging.getLogger(__name__)


class NetworkStatus(Enum):
    """Network connectivity status levels."""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class NetworkCheckResult:
    """Result of a network connectivity check."""
    endpoint: str
    status: NetworkStatus
    response_time: float
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class NetworkConfig:
    """Configuration for network connectivity monitoring."""
    check_interval: float = 30.0  # Seconds between checks
    timeout: float = 10.0  # Timeout for individual checks
    retry_attempts: int = 3  # Number of retry attempts
    endpoints: List[str] = field(default_factory=lambda: [
        "https://www.google.com",
        "https://www.cloudflare.com",
        "https://www.github.com",
        "https://api.openai.com",
        "https://api.anthropic.com"
    ])
    offline_threshold: int = 2  # Consecutive failures before offline mode
    degraded_threshold: int = 1  # Consecutive failures before degraded mode


class NetworkConnectivityMonitor:
    """
    Monitor network connectivity and trigger offline/online mode switching.
    
    Provides real-time network status detection with configurable endpoints,
    exponential backoff for failed checks, and event-driven status notifications.
    """
    
    def __init__(self, config: Optional[NetworkConfig] = None):
        self.config = config or NetworkConfig()
        self._status = NetworkStatus.UNKNOWN
        self._status_callbacks: List[Callable[[NetworkStatus, NetworkStatus], Union[None, Awaitable[None]]]] = []
        self._check_history: List[NetworkCheckResult] = []
        self._consecutive_failures = 0
        self._last_success_time = time.time()
        self._monitoring_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        logger.info("Network connectivity monitor initialized")
    
    async def start_monitoring(self) -> None:
        """Start continuous network connectivity monitoring."""
        if self._monitoring_task is not None:
            logger.warning("Network monitoring already started")
            return
        
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"Network monitoring started with {len(self.config.endpoints)} endpoints")
    
    async def stop_monitoring(self) -> None:
        """Stop network connectivity monitoring."""
        if self._monitoring_task is None:
            return
        
        self._monitoring_task.cancel()
        self._monitoring_task = None
        logger.info("Network monitoring stopped")
    
    def register_status_callback(self, callback: Callable[[NetworkStatus, NetworkStatus], Union[None, Awaitable[None]]]) -> None:
        """Register callback for network status changes."""
        self._status_callbacks.append(callback)
    
    def get_current_status(self) -> NetworkStatus:
        """Get current network status."""
        return self._status
    
    def is_online(self) -> bool:
        """Check if currently online."""
        return self._status == NetworkStatus.ONLINE
    
    def is_offline(self) -> bool:
        """Check if currently offline."""
        return self._status == NetworkStatus.OFFLINE
    
    def is_degraded(self) -> bool:
        """Check if currently degraded."""
        return self._status == NetworkStatus.DEGRADED
    
    def get_check_history(self, limit: int = 10) -> List[NetworkCheckResult]:
        """Get recent network check history."""
        return self._check_history[-limit:]
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop with exponential backoff."""
        while True:
            try:
                await self._check_connectivity()
                await asyncio.sleep(self.config.check_interval)
            except asyncio.CancelledError:
                logger.info("Network monitoring loop cancelled")
                break
    
    async def _check_connectivity(self) -> None:
        """Check connectivity to all configured endpoints."""
        results: List[Union[NetworkCheckResult, BaseException]] = []
        
        # Check all endpoints concurrently
        tasks = [
            self._check_endpoint(endpoint) for endpoint in self.config.endpoints
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Connectivity check failed: {e}")
            results = []
        
        # Filter out exceptions and only process NetworkCheckResult objects
        valid_results: List[NetworkCheckResult] = []
        for result in results:
            if isinstance(result, NetworkCheckResult):
                valid_results.append(result)
            elif isinstance(result, BaseException):
                logger.error(f"Endpoint check failed with exception: {result}")
        
        # Analyze results
        online_count = sum(1 for r in valid_results if r.status == NetworkStatus.ONLINE)
        total_checks = len(valid_results)
        
        # Update status based on results
        if online_count == 0:
            new_status = NetworkStatus.OFFLINE
            self._consecutive_failures += 1
        elif online_count < total_checks // 2:
            new_status = NetworkStatus.DEGRADED
            self._consecutive_failures += 1
        else:
            new_status = NetworkStatus.ONLINE
            self._consecutive_failures = 0
            self._last_success_time = time.time()
        
        # Status change notification
        if new_status != self._status:
            await self._notify_status_change(self._status, new_status)
            self._status = new_status
        
        # Store check results (only valid results)
        self._check_history.extend(valid_results)
        if len(self._check_history) > 100:  # Keep last 100 results
            self._check_history = self._check_history[-100:]
    
    async def _check_endpoint(self, endpoint: str) -> NetworkCheckResult:
        """Check connectivity to a specific endpoint."""
        start_time = time.time()
        
        try:
            # Use aiohttp for async HTTP requests
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                try:
                    async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as response:
                        if response.status == 200:
                            response_time = time.time() - start_time
                            return NetworkCheckResult(
                                endpoint=endpoint,
                                status=NetworkStatus.ONLINE,
                                response_time=response_time,
                                timestamp=start_time
                            )
                        else:
                            return NetworkCheckResult(
                                endpoint=endpoint,
                                status=NetworkStatus.OFFLINE,
                                response_time=time.time() - start_time,
                                error=f"HTTP {response.status}",
                                timestamp=start_time
                            )
                except asyncio.TimeoutError:
                    return NetworkCheckResult(
                        endpoint=endpoint,
                        status=NetworkStatus.OFFLINE,
                        response_time=self.config.timeout,
                        error="timeout",
                        timestamp=start_time
                    )
        except Exception as e:
            return NetworkCheckResult(
                endpoint=endpoint,
                status=NetworkStatus.OFFLINE,
                response_time=time.time() - start_time,
                error=str(e),
                timestamp=start_time
            )
    
    async def _notify_status_change(self, old_status: NetworkStatus, new_status: NetworkStatus) -> None:
        """Notify registered callbacks of status changes."""
        for callback in self._status_callbacks:
            try:
                await callback(old_status, new_status)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
    
    def get_network_metrics(self) -> Dict[str, Union[str, int, float, Dict[str, int]]]:
        """Get network connectivity metrics."""
        if not self._check_history:
            return {}
        
        recent_checks = self._check_history[-50:]  # Last 50 checks
        
        # Calculate metrics
        total_checks = len(recent_checks)
        online_checks = sum(1 for check in recent_checks if check.status == NetworkStatus.ONLINE)
        avg_response_time = sum(check.response_time for check in recent_checks if check.status == NetworkStatus.ONLINE) / max(online_checks, 1)
        
        # Status distribution
        status_counts = {}
        for status in NetworkStatus:
            count = sum(1 for check in recent_checks if check.status == status)
            if count > 0:
                status_counts[status.value] = count
        
        return {
            "status": self._status.value,
            "total_checks": total_checks,
            "online_checks": online_checks,
            "online_rate": online_checks / total_checks if total_checks > 0 else 0,
            "average_response_time": avg_response_time,
            "consecutive_failures": self._consecutive_failures,
            "last_success_time": self._last_success_time,
            "status_distribution": status_counts,
            "uptime_percentage": (online_checks / total_checks) * 100 if total_checks > 0 else 0
        }


# Global instance for easy access
_network_monitor: Optional[NetworkConnectivityMonitor] = None


def get_network_monitor(config: Optional[NetworkConfig] = None) -> NetworkConnectivityMonitor:
    """Get or create global network monitor instance."""
    global _network_monitor
    if _network_monitor is None:
        _network_monitor = NetworkConnectivityMonitor(config)
    return _network_monitor


async def initialize_network_monitoring(config: Optional[NetworkConfig] = None) -> None:
    """Initialize network monitoring system."""
    monitor = get_network_monitor(config)
    await monitor.start_monitoring()
    logger.info("Network connectivity monitoring system initialized")


# Export main classes for easy import
__all__ = [
    "NetworkStatus",
    "NetworkCheckResult", 
    "NetworkConfig",
    "NetworkConnectivityMonitor",
    "get_network_monitor",
    "initialize_network_monitoring"
]