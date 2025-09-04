"""
Service Health Monitor

This module provides comprehensive health monitoring for all services
with automatic recovery attempts and integration with the error recovery manager.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass
from enum import Enum
import psutil
import json
from pathlib import Path

from .error_recovery_manager import ErrorRecoveryManager, ServiceStatus


class HealthCheckType(Enum):
    """Types of health checks"""
    PING = "ping"
    HTTP = "http"
    DATABASE = "database"
    MEMORY = "memory"
    CPU = "cpu"
    CUSTOM = "custom"


@dataclass
class HealthCheckConfig:
    """Configuration for a health check"""
    check_type: HealthCheckType
    interval: int = 30  # seconds
    timeout: int = 5    # seconds
    retries: int = 3
    threshold: Optional[float] = None  # For resource checks
    endpoint: Optional[str] = None     # For HTTP checks
    custom_check: Optional[Callable] = None  # For custom checks


@dataclass
class HealthMetrics:
    """Health metrics for a service"""
    service_name: str
    timestamp: datetime
    status: ServiceStatus
    response_time: float
    cpu_usage: float
    memory_usage: int  # MB
    error_rate: float
    uptime: timedelta
    custom_metrics: Dict[str, Any]


class ServiceHealthMonitor:
    """
    Monitors health of all registered services and integrates with
    error recovery manager for automatic recovery attempts.
    """
    
    def __init__(self, error_recovery_manager: Optional[ErrorRecoveryManager] = None):
        self.logger = logging.getLogger(__name__)
        self.error_recovery_manager = error_recovery_manager
        
        # Health check configurations
        self.health_checks: Dict[str, HealthCheckConfig] = {}
        self.service_metrics: Dict[str, List[HealthMetrics]] = {}
        self.service_start_times: Dict[str, datetime] = {}
        
        # Monitoring control
        self.monitoring_active = False
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.global_monitoring_task: Optional[asyncio.Task] = None
        
        # Alerting and reporting
        self.health_report_path = Path("logs/service_health.json")
        self.alert_thresholds = {
            "error_rate": 0.1,      # 10% error rate
            "response_time": 5.0,   # 5 seconds
            "cpu_usage": 80.0,      # 80% CPU
            "memory_usage": 1024    # 1GB memory
        }
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup health monitoring logging"""
        self.health_report_path.parent.mkdir(exist_ok=True)
        
        # Create dedicated logger for health monitoring
        self.health_logger = logging.getLogger("service_health")
        self.health_logger.setLevel(logging.INFO)
        
        # File handler for health logs
        handler = logging.FileHandler("logs/service_health.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.health_logger.addHandler(handler)
    
    def register_service_health_check(self, service_name: str, 
                                    config: HealthCheckConfig):
        """Register a health check for a service"""
        self.health_checks[service_name] = config
        self.service_metrics[service_name] = []
        self.service_start_times[service_name] = datetime.now()
        
        self.logger.info(f"Registered health check for service {service_name}")
        
        # Register with error recovery manager if available
        if self.error_recovery_manager:
            self.error_recovery_manager.register_service(service_name)
    
    def register_http_health_check(self, service_name: str, endpoint: str,
                                 interval: int = 30, timeout: int = 5):
        """Register an HTTP health check for a service"""
        config = HealthCheckConfig(
            check_type=HealthCheckType.HTTP,
            interval=interval,
            timeout=timeout,
            endpoint=endpoint
        )
        self.register_service_health_check(service_name, config)
    
    def register_resource_health_check(self, service_name: str, 
                                     check_type: HealthCheckType,
                                     threshold: float, interval: int = 30):
        """Register a resource-based health check"""
        config = HealthCheckConfig(
            check_type=check_type,
            interval=interval,
            threshold=threshold
        )
        self.register_service_health_check(service_name, config)
    
    def register_custom_health_check(self, service_name: str, 
                                   check_function: Callable,
                                   interval: int = 30):
        """Register a custom health check function"""
        config = HealthCheckConfig(
            check_type=HealthCheckType.CUSTOM,
            interval=interval,
            custom_check=check_function
        )
        self.register_service_health_check(service_name, config)
    
    async def start_monitoring(self):
        """Start health monitoring for all registered services"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # Start individual service monitoring tasks
        for service_name in self.health_checks.keys():
            await self._start_service_monitoring(service_name)
        
        # Start global monitoring task
        self.global_monitoring_task = asyncio.create_task(
            self._global_monitoring_loop()
        )
        
        self.logger.info("Started service health monitoring")
    
    async def stop_monitoring(self):
        """Stop all health monitoring"""
        self.monitoring_active = False
        
        # Cancel individual service monitoring tasks
        for task in self.monitoring_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks.values(), return_exceptions=True)
        
        self.monitoring_tasks.clear()
        
        # Cancel global monitoring task
        if self.global_monitoring_task:
            self.global_monitoring_task.cancel()
            try:
                await self.global_monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Stopped service health monitoring")
    
    async def _start_service_monitoring(self, service_name: str):
        """Start monitoring for a specific service"""
        if service_name in self.monitoring_tasks:
            return
        
        self.monitoring_tasks[service_name] = asyncio.create_task(
            self._service_monitoring_loop(service_name)
        )
    
    async def _service_monitoring_loop(self, service_name: str):
        """Monitoring loop for a specific service"""
        config = self.health_checks[service_name]
        
        while self.monitoring_active:
            try:
                # Perform health check
                metrics = await self._perform_health_check(service_name, config)
                
                # Store metrics
                self.service_metrics[service_name].append(metrics)
                
                # Keep only last 100 metrics per service
                if len(self.service_metrics[service_name]) > 100:
                    self.service_metrics[service_name] = self.service_metrics[service_name][-100:]
                
                # Check for alerts
                await self._check_health_alerts(service_name, metrics)
                
                # Wait for next check
                await asyncio.sleep(config.interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health monitoring for {service_name}: {e}")
                
                # Report failure to error recovery manager
                if self.error_recovery_manager:
                    await self.error_recovery_manager.handle_service_failure(
                        service_name, e
                    )
                
                await asyncio.sleep(5)  # Brief pause before retry
    
    async def _perform_health_check(self, service_name: str, 
                                  config: HealthCheckConfig) -> HealthMetrics:
        """Perform a health check for a service"""
        start_time = datetime.now()
        status = ServiceStatus.HEALTHY
        response_time = 0.0
        error_message = None
        
        try:
            if config.check_type == HealthCheckType.HTTP:
                response_time = await self._http_health_check(config.endpoint, config.timeout)
            elif config.check_type == HealthCheckType.PING:
                response_time = await self._ping_health_check(service_name)
            elif config.check_type == HealthCheckType.CUSTOM:
                response_time = await self._custom_health_check(config.custom_check)
            else:
                response_time = 0.0  # Resource checks don't have response time
            
        except Exception as e:
            status = ServiceStatus.FAILED
            error_message = str(e)
            self.health_logger.error(f"Health check failed for {service_name}: {e}")
        
        # Get resource metrics
        cpu_usage, memory_usage = await self._get_resource_metrics(service_name)
        
        # Calculate uptime
        uptime = datetime.now() - self.service_start_times.get(service_name, datetime.now())
        
        # Calculate error rate
        error_rate = await self._calculate_error_rate(service_name)
        
        # Create metrics object
        metrics = HealthMetrics(
            service_name=service_name,
            timestamp=start_time,
            status=status,
            response_time=response_time,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            error_rate=error_rate,
            uptime=uptime,
            custom_metrics={}
        )
        
        # Report to error recovery manager
        if self.error_recovery_manager:
            if status == ServiceStatus.HEALTHY:
                await self.error_recovery_manager.record_service_success(service_name)
            else:
                await self.error_recovery_manager.handle_service_failure(
                    service_name, Exception(error_message or "Health check failed")
                )
        
        return metrics
    
    async def _http_health_check(self, endpoint: str, timeout: int) -> float:
        """Perform HTTP health check"""
        import aiohttp
        
        start_time = datetime.now()
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(endpoint) as response:
                if response.status >= 400:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
        
        return (datetime.now() - start_time).total_seconds()
    
    async def _ping_health_check(self, service_name: str) -> float:
        """Perform ping-style health check"""
        try:
            # Import here to avoid circular imports
            from .service_registry import ServiceRegistry
            
            registry = ServiceRegistry()
            service = registry.get_service(service_name)
            
            if not service:
                raise Exception(f"Service {service_name} not found in registry")
            
            start_time = datetime.now()
            
            # Try to call a simple method if available
            if hasattr(service, 'ping'):
                await service.ping()
            elif hasattr(service, 'health_check'):
                await service.health_check()
            
            return (datetime.now() - start_time).total_seconds()
            
        except Exception as e:
            raise Exception(f"Ping health check failed: {e}")
    
    async def _custom_health_check(self, check_function: Callable) -> float:
        """Perform custom health check"""
        start_time = datetime.now()
        
        if asyncio.iscoroutinefunction(check_function):
            result = await check_function()
        else:
            result = check_function()
        
        if not result:
            raise Exception("Custom health check returned False")
        
        return (datetime.now() - start_time).total_seconds()
    
    async def _get_resource_metrics(self, service_name: str) -> tuple[float, int]:
        """Get CPU and memory usage for a service"""
        try:
            # Get current process info
            process = psutil.Process()
            cpu_usage = process.cpu_percent()
            memory_usage = process.memory_info().rss // (1024 * 1024)  # MB
            
            return cpu_usage, memory_usage
            
        except Exception as e:
            self.logger.warning(f"Could not get resource metrics for {service_name}: {e}")
            return 0.0, 0
    
    async def _calculate_error_rate(self, service_name: str) -> float:
        """Calculate error rate for a service over the last 10 minutes"""
        if service_name not in self.service_metrics:
            return 0.0
        
        recent_metrics = [
            m for m in self.service_metrics[service_name]
            if datetime.now() - m.timestamp < timedelta(minutes=10)
        ]
        
        if not recent_metrics:
            return 0.0
        
        failed_checks = sum(1 for m in recent_metrics if m.status == ServiceStatus.FAILED)
        return failed_checks / len(recent_metrics)
    
    async def _check_health_alerts(self, service_name: str, metrics: HealthMetrics):
        """Check if health metrics exceed alert thresholds"""
        alerts = []
        
        if metrics.error_rate > self.alert_thresholds["error_rate"]:
            alerts.append(f"High error rate: {metrics.error_rate:.2%}")
        
        if metrics.response_time > self.alert_thresholds["response_time"]:
            alerts.append(f"High response time: {metrics.response_time:.2f}s")
        
        if metrics.cpu_usage > self.alert_thresholds["cpu_usage"]:
            alerts.append(f"High CPU usage: {metrics.cpu_usage:.1f}%")
        
        if metrics.memory_usage > self.alert_thresholds["memory_usage"]:
            alerts.append(f"High memory usage: {metrics.memory_usage}MB")
        
        # Send alerts if any thresholds exceeded
        if alerts and self.error_recovery_manager:
            alert_message = f"Service {service_name} health alerts: {', '.join(alerts)}"
            await self.error_recovery_manager._send_alert(alert_message, "warning")
    
    async def _global_monitoring_loop(self):
        """Global monitoring loop for system-wide health checks"""
        while self.monitoring_active:
            try:
                # Generate and save health report
                await self._generate_health_report()
                
                # Check for system-wide issues
                await self._check_system_health()
                
                # Wait before next global check
                await asyncio.sleep(60)  # Every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in global monitoring loop: {e}")
                await asyncio.sleep(10)
    
    async def _generate_health_report(self):
        """Generate comprehensive health report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "monitoring_active": self.monitoring_active,
            "services": {}
        }
        
        for service_name, metrics_list in self.service_metrics.items():
            if not metrics_list:
                continue
            
            latest_metrics = metrics_list[-1]
            
            # Calculate averages over last 10 metrics
            recent_metrics = metrics_list[-10:]
            avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
            avg_cpu_usage = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
            avg_memory_usage = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
            
            report["services"][service_name] = {
                "status": latest_metrics.status.value,
                "uptime": str(latest_metrics.uptime),
                "error_rate": latest_metrics.error_rate,
                "avg_response_time": avg_response_time,
                "avg_cpu_usage": avg_cpu_usage,
                "avg_memory_usage": avg_memory_usage,
                "last_check": latest_metrics.timestamp.isoformat()
            }
        
        # Save report to file
        with open(self.health_report_path, 'w') as f:
            json.dump(report, f, indent=2)
    
    async def _check_system_health(self):
        """Check overall system health and trigger alerts if needed"""
        total_services = len(self.service_metrics)
        if total_services == 0:
            return
        
        # Count failed services
        failed_services = 0
        degraded_services = 0
        
        for metrics_list in self.service_metrics.values():
            if metrics_list:
                latest = metrics_list[-1]
                if latest.status == ServiceStatus.FAILED:
                    failed_services += 1
                elif latest.status == ServiceStatus.DEGRADED:
                    degraded_services += 1
        
        # Calculate failure rates
        failure_rate = failed_services / total_services
        degradation_rate = (failed_services + degraded_services) / total_services
        
        # Send system-wide alerts
        if failure_rate > 0.3:  # More than 30% of services failed
            if self.error_recovery_manager:
                await self.error_recovery_manager._send_alert(
                    f"System-wide service failures: {failure_rate:.1%} of services failed",
                    "critical"
                )
        elif degradation_rate > 0.5:  # More than 50% of services degraded
            if self.error_recovery_manager:
                await self.error_recovery_manager._send_alert(
                    f"System degradation: {degradation_rate:.1%} of services affected",
                    "warning"
                )
    
    async def get_service_health(self, service_name: str) -> Optional[HealthMetrics]:
        """Get latest health metrics for a service"""
        if service_name in self.service_metrics and self.service_metrics[service_name]:
            return self.service_metrics[service_name][-1]
        return None
    
    async def get_all_service_health(self) -> Dict[str, HealthMetrics]:
        """Get latest health metrics for all services"""
        result = {}
        for service_name, metrics_list in self.service_metrics.items():
            if metrics_list:
                result[service_name] = metrics_list[-1]
        return result
    
    async def get_service_history(self, service_name: str, 
                                hours: int = 24) -> List[HealthMetrics]:
        """Get health history for a service"""
        if service_name not in self.service_metrics:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            m for m in self.service_metrics[service_name]
            if m.timestamp >= cutoff_time
        ]


# Global instance for easy access
_service_health_monitor = None

def get_service_health_monitor() -> ServiceHealthMonitor:
    """Get global service health monitor instance"""
    global _service_health_monitor
    if _service_health_monitor is None:
        from .error_recovery_manager import get_error_recovery_manager
        _service_health_monitor = ServiceHealthMonitor(get_error_recovery_manager())
    return _service_health_monitor