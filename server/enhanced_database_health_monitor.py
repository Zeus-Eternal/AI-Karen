"""
Enhanced Database Health Monitor with Extension Service Isolation

This module extends the existing database health monitor to include
service-specific connection pool monitoring for extension services.

Key enhancements:
- Extension service connection pool monitoring
- Service-specific health checks
- Extension authentication connection isolation tracking
- LLM runtime interference detection and mitigation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from .service_isolated_database import ServiceType, ServiceIsolatedDatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class ServiceHealthMetrics:
    """Health metrics for a specific service"""
    service_type: str
    healthy: bool
    response_time_ms: float
    connection_failures: int
    pool_size: int
    checked_out: int
    overflow: int
    checked_in: int
    invalidated: int
    priority: str
    last_check: datetime
    error: Optional[str] = None


@dataclass
class ExtensionServiceHealth:
    """Comprehensive extension service health information"""
    extension_service_healthy: bool
    authentication_service_healthy: bool
    llm_service_healthy: bool
    usage_tracking_healthy: bool
    background_tasks_healthy: bool
    overall_health: str
    service_metrics: Dict[str, ServiceHealthMetrics]
    interference_detected: bool = False
    interference_sources: List[str] = field(default_factory=list)
    mitigation_active: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)


class EnhancedDatabaseHealthMonitor:
    """
    Enhanced database health monitor with extension service isolation support.
    
    This monitor specifically tracks extension service health to prevent
    LLM runtime caching from interfering with extension authentication.
    """
    
    def __init__(self, service_isolated_manager: Optional[ServiceIsolatedDatabaseManager] = None):
        self.service_isolated_manager = service_isolated_manager
        self._monitoring_active = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._health_history: List[ExtensionServiceHealth] = []
        self._max_history = 100
        
        # Interference detection thresholds
        self.interference_thresholds = {
            "response_time_ms": 1000,  # 1 second
            "connection_failures": 3,
            "pool_exhaustion_ratio": 0.8,  # 80% of pool used
        }
        
        # Service priority for interference detection
        self.service_priorities = {
            ServiceType.AUTHENTICATION: 1,  # Highest priority
            ServiceType.EXTENSION: 2,
            ServiceType.BACKGROUND_TASKS: 3,
            ServiceType.USAGE_TRACKING: 4,
            ServiceType.LLM: 5,  # Lowest priority
            ServiceType.DEFAULT: 6
        }
    
    async def start_monitoring(self, check_interval: int = 30):
        """Start enhanced health monitoring with extension service focus"""
        if not self.service_isolated_manager:
            logger.warning("Service-isolated manager not available, enhanced monitoring disabled")
            return
        
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop(check_interval))
        logger.info("Enhanced database health monitoring started with extension service isolation")
    
    async def stop_monitoring(self):
        """Stop enhanced health monitoring"""
        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Enhanced database health monitoring stopped")
    
    async def _monitoring_loop(self, check_interval: int):
        """Main monitoring loop"""
        while self._monitoring_active:
            try:
                health = await self.check_extension_service_health()
                self._add_to_history(health)
                
                # Detect and mitigate interference
                if health.interference_detected:
                    await self._handle_interference(health)
                
                await asyncio.sleep(check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in enhanced health monitoring loop: {e}")
                await asyncio.sleep(check_interval)
    
    async def check_extension_service_health(self) -> ExtensionServiceHealth:
        """Check health of all services with focus on extension service isolation"""
        if not self.service_isolated_manager:
            return ExtensionServiceHealth(
                extension_service_healthy=False,
                authentication_service_healthy=False,
                llm_service_healthy=False,
                usage_tracking_healthy=False,
                background_tasks_healthy=False,
                overall_health="unavailable",
                service_metrics={},
                interference_detected=False
            )
        
        try:
            # Get health for all services
            all_health = await self.service_isolated_manager.health_check_all()
            
            # Extract service-specific health
            services = all_health.get("services", {})
            service_metrics = {}
            
            for service_name, health_data in services.items():
                pool_metrics = health_data.get("pool_metrics", {})
                service_metrics[service_name] = ServiceHealthMetrics(
                    service_type=service_name,
                    healthy=health_data.get("healthy", False),
                    response_time_ms=health_data.get("response_time_ms", 0),
                    connection_failures=health_data.get("connection_failures", 0),
                    pool_size=pool_metrics.get("pool_size", 0),
                    checked_out=pool_metrics.get("checked_out", 0),
                    overflow=pool_metrics.get("overflow", 0),
                    checked_in=pool_metrics.get("checked_in", 0),
                    invalidated=pool_metrics.get("invalidated", 0),
                    priority=pool_metrics.get("priority", "unknown"),
                    last_check=datetime.utcnow(),
                    error=health_data.get("error")
                )
            
            # Detect interference
            interference_detected, interference_sources = self._detect_interference(service_metrics)
            
            # Create comprehensive health report
            extension_health = ExtensionServiceHealth(
                extension_service_healthy=all_health.get("extension_service_healthy", False),
                authentication_service_healthy=all_health.get("authentication_service_healthy", False),
                llm_service_healthy=services.get("llm", {}).get("healthy", False),
                usage_tracking_healthy=services.get("usage_tracking", {}).get("healthy", False),
                background_tasks_healthy=services.get("background_tasks", {}).get("healthy", False),
                overall_health=all_health.get("overall_health", "unknown"),
                service_metrics=service_metrics,
                interference_detected=interference_detected,
                interference_sources=interference_sources,
                mitigation_active=False  # Will be set by mitigation handler
            )
            
            return extension_health
            
        except Exception as e:
            logger.error(f"Failed to check extension service health: {e}")
            return ExtensionServiceHealth(
                extension_service_healthy=False,
                authentication_service_healthy=False,
                llm_service_healthy=False,
                usage_tracking_healthy=False,
                background_tasks_healthy=False,
                overall_health="error",
                service_metrics={},
                interference_detected=False
            )
    
    def _detect_interference(self, service_metrics: Dict[str, ServiceHealthMetrics]) -> tuple[bool, List[str]]:
        """Detect LLM runtime interference with extension services"""
        interference_sources = []
        
        # Check for high response times in critical services
        for service_name in ["extension", "authentication"]:
            if service_name in service_metrics:
                metrics = service_metrics[service_name]
                if metrics.response_time_ms > self.interference_thresholds["response_time_ms"]:
                    interference_sources.append(f"{service_name}_slow_response")
        
        # Check for connection failures in critical services
        for service_name in ["extension", "authentication"]:
            if service_name in service_metrics:
                metrics = service_metrics[service_name]
                if metrics.connection_failures > self.interference_thresholds["connection_failures"]:
                    interference_sources.append(f"{service_name}_connection_failures")
        
        # Check for pool exhaustion
        for service_name, metrics in service_metrics.items():
            if metrics.pool_size > 0:
                utilization = metrics.checked_out / metrics.pool_size
                if utilization > self.interference_thresholds["pool_exhaustion_ratio"]:
                    interference_sources.append(f"{service_name}_pool_exhaustion")
        
        # Check for LLM service monopolizing resources
        if "llm" in service_metrics:
            llm_metrics = service_metrics["llm"]
            if llm_metrics.pool_size > 0:
                llm_utilization = llm_metrics.checked_out / llm_metrics.pool_size
                if llm_utilization > 0.9:  # LLM using >90% of its pool
                    # Check if extension/auth services are suffering
                    for service_name in ["extension", "authentication"]:
                        if service_name in service_metrics:
                            if not service_metrics[service_name].healthy:
                                interference_sources.append("llm_resource_monopolization")
                                break
        
        return len(interference_sources) > 0, interference_sources
    
    async def _handle_interference(self, health: ExtensionServiceHealth):
        """Handle detected interference between LLM runtime and extension services"""
        logger.warning(
            f"LLM runtime interference detected: {health.interference_sources}",
            extra={
                "extension_healthy": health.extension_service_healthy,
                "auth_healthy": health.authentication_service_healthy,
                "interference_sources": health.interference_sources
            }
        )
        
        # Log detailed metrics for debugging
        for service_name, metrics in health.service_metrics.items():
            if not metrics.healthy or metrics.response_time_ms > 500:
                logger.warning(
                    f"Service {service_name} performance issues",
                    extra={
                        "healthy": metrics.healthy,
                        "response_time_ms": metrics.response_time_ms,
                        "connection_failures": metrics.connection_failures,
                        "pool_utilization": metrics.checked_out / max(metrics.pool_size, 1)
                    }
                )
        
        # Implement mitigation strategies
        mitigation_applied = False
        
        # Strategy 1: Increase pool sizes for critical services if needed
        if "extension_pool_exhaustion" in health.interference_sources:
            logger.info("Detected extension pool exhaustion - consider increasing extension pool size")
            mitigation_applied = True
        
        if "authentication_pool_exhaustion" in health.interference_sources:
            logger.info("Detected authentication pool exhaustion - consider increasing auth pool size")
            mitigation_applied = True
        
        # Strategy 2: Log recommendations for configuration changes
        if "llm_resource_monopolization" in health.interference_sources:
            logger.warning(
                "LLM service is monopolizing resources, affecting extension services. "
                "Consider: 1) Reducing LLM pool size, 2) Implementing LLM request throttling, "
                "3) Scheduling LLM warmup during off-peak hours"
            )
            mitigation_applied = True
        
        # Update mitigation status
        health.mitigation_active = mitigation_applied
    
    def _add_to_history(self, health: ExtensionServiceHealth):
        """Add health record to history"""
        self._health_history.append(health)
        if len(self._health_history) > self._max_history:
            self._health_history.pop(0)
    
    def get_health_history(self, minutes: int = 60) -> List[ExtensionServiceHealth]:
        """Get health history for the specified number of minutes"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return [h for h in self._health_history if h.timestamp >= cutoff_time]
    
    def get_interference_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """Get summary of interference incidents in the specified time period"""
        history = self.get_health_history(minutes)
        
        interference_incidents = [h for h in history if h.interference_detected]
        total_incidents = len(interference_incidents)
        
        if total_incidents == 0:
            return {
                "total_incidents": 0,
                "interference_rate": 0.0,
                "common_sources": [],
                "avg_extension_response_time": 0.0,
                "avg_auth_response_time": 0.0
            }
        
        # Count interference sources
        source_counts = {}
        extension_response_times = []
        auth_response_times = []
        
        for incident in interference_incidents:
            for source in incident.interference_sources:
                source_counts[source] = source_counts.get(source, 0) + 1
            
            # Collect response times
            if "extension" in incident.service_metrics:
                extension_response_times.append(incident.service_metrics["extension"].response_time_ms)
            if "authentication" in incident.service_metrics:
                auth_response_times.append(incident.service_metrics["authentication"].response_time_ms)
        
        # Sort sources by frequency
        common_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "total_incidents": total_incidents,
            "interference_rate": total_incidents / len(history) if history else 0.0,
            "common_sources": common_sources[:5],  # Top 5 sources
            "avg_extension_response_time": sum(extension_response_times) / len(extension_response_times) if extension_response_times else 0.0,
            "avg_auth_response_time": sum(auth_response_times) / len(auth_response_times) if auth_response_times else 0.0,
            "time_period_minutes": minutes
        }
    
    async def get_current_health_with_extension_focus(self) -> Dict[str, Any]:
        """Get current health with specific focus on extension service isolation"""
        health = await self.check_extension_service_health()
        interference_summary = self.get_interference_summary(60)  # Last hour
        
        return {
            "timestamp": health.timestamp.isoformat(),
            "extension_service_isolated": self.service_isolated_manager is not None,
            "extension_service_healthy": health.extension_service_healthy,
            "authentication_service_healthy": health.authentication_service_healthy,
            "overall_health": health.overall_health,
            "interference_detected": health.interference_detected,
            "interference_sources": health.interference_sources,
            "mitigation_active": health.mitigation_active,
            "service_metrics": {
                name: {
                    "healthy": metrics.healthy,
                    "response_time_ms": metrics.response_time_ms,
                    "connection_failures": metrics.connection_failures,
                    "pool_utilization": metrics.checked_out / max(metrics.pool_size, 1),
                    "priority": metrics.priority,
                    "error": metrics.error
                }
                for name, metrics in health.service_metrics.items()
            },
            "interference_summary": interference_summary,
            "recommendations": self._generate_recommendations(health, interference_summary)
        }
    
    def _generate_recommendations(self, health: ExtensionServiceHealth, interference_summary: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on current health and interference patterns"""
        recommendations = []
        
        # Extension service recommendations
        if not health.extension_service_healthy:
            recommendations.append("Extension service is unhealthy - check connection pool configuration and database connectivity")
        
        # Authentication service recommendations
        if not health.authentication_service_healthy:
            recommendations.append("Authentication service is unhealthy - this will cause HTTP 403 errors in extension APIs")
        
        # Interference-based recommendations
        if interference_summary["interference_rate"] > 0.1:  # >10% interference rate
            recommendations.append("High interference rate detected - consider increasing connection pool sizes for critical services")
        
        common_sources = interference_summary.get("common_sources", [])
        if common_sources:
            top_source = common_sources[0][0]
            if "pool_exhaustion" in top_source:
                recommendations.append(f"Frequent pool exhaustion in {top_source.split('_')[0]} service - increase pool size")
            elif "slow_response" in top_source:
                recommendations.append(f"Slow responses in {top_source.split('_')[0]} service - check database performance")
            elif "llm_resource_monopolization" in top_source:
                recommendations.append("LLM service is monopolizing resources - implement request throttling or reduce LLM pool size")
        
        # Performance recommendations
        avg_ext_response = interference_summary.get("avg_extension_response_time", 0)
        if avg_ext_response > 500:
            recommendations.append(f"Extension service average response time is {avg_ext_response:.0f}ms - optimize database queries")
        
        avg_auth_response = interference_summary.get("avg_auth_response_time", 0)
        if avg_auth_response > 200:
            recommendations.append(f"Authentication service average response time is {avg_auth_response:.0f}ms - disable query caching for auth")
        
        return recommendations


# Global instance
_enhanced_health_monitor: Optional[EnhancedDatabaseHealthMonitor] = None


def get_enhanced_database_health_monitor() -> Optional[EnhancedDatabaseHealthMonitor]:
    """Get the global enhanced database health monitor"""
    return _enhanced_health_monitor


async def initialize_enhanced_health_monitor(service_isolated_manager: Optional[ServiceIsolatedDatabaseManager] = None) -> EnhancedDatabaseHealthMonitor:
    """Initialize the enhanced database health monitor"""
    global _enhanced_health_monitor
    
    _enhanced_health_monitor = EnhancedDatabaseHealthMonitor(service_isolated_manager)
    await _enhanced_health_monitor.start_monitoring()
    
    logger.info("Enhanced database health monitor initialized")
    return _enhanced_health_monitor


async def shutdown_enhanced_health_monitor():
    """Shutdown the enhanced database health monitor"""
    global _enhanced_health_monitor
    
    if _enhanced_health_monitor:
        await _enhanced_health_monitor.stop_monitoring()
        _enhanced_health_monitor = None
    
    logger.info("Enhanced database health monitor shutdown completed")