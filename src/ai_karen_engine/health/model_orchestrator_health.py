"""
Model Orchestrator Health Check Integration.

This module provides health checks for model orchestrator operations,
integrating with existing monitoring endpoints and health check systems.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import json

from ai_karen_engine.monitoring.model_storage_monitor import get_model_storage_monitor
from ai_karen_engine.monitoring.model_orchestrator_metrics import get_model_orchestrator_metrics
from ai_karen_engine.error_tracking.model_orchestrator_errors import get_model_orchestrator_error_tracker

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: str
    message: str
    details: Dict[str, Any]
    timestamp: str
    duration_ms: float


class ModelOrchestratorHealthChecker:
    """
    Health checker for model orchestrator operations.
    
    Provides comprehensive health checks for storage, registry,
    services, and integration points.
    """
    
    def __init__(self, models_root: Path = None):
        self.models_root = models_root or Path("models")
        self.storage_monitor = get_model_storage_monitor(self.models_root)
        self.metrics = get_model_orchestrator_metrics()
        self.error_tracker = get_model_orchestrator_error_tracker()
        
        logger.debug("Model orchestrator health checker initialized")
    
    async def check_storage_health(self) -> HealthCheckResult:
        """Check storage system health."""
        start_time = datetime.utcnow()
        
        try:
            # Get storage information
            disk_info = self.storage_monitor.get_disk_usage()
            model_stats = self.storage_monitor.get_model_storage_stats()
            
            # Determine health status
            status = HealthStatus.HEALTHY
            messages = []
            
            # Check disk usage
            if disk_info.usage_percent > 95:
                status = HealthStatus.CRITICAL
                messages.append(f"Disk usage critical: {disk_info.usage_percent:.1f}%")
            elif disk_info.usage_percent > 85:
                status = HealthStatus.WARNING
                messages.append(f"Disk usage high: {disk_info.usage_percent:.1f}%")
            
            # Check for very old models
            old_model_threshold = datetime.now() - timedelta(days=180)
            for library, stats in model_stats.items():
                if stats.last_accessed and stats.last_accessed < old_model_threshold:
                    if status == HealthStatus.HEALTHY:
                        status = HealthStatus.WARNING
                    messages.append(f"Library {library} has very old models")
            
            # Check registry file
            registry_path = self.models_root / "llm_registry.json"
            if not registry_path.exists():
                status = HealthStatus.WARNING
                messages.append("Registry file not found")
            
            message = "; ".join(messages) if messages else "Storage system healthy"
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return HealthCheckResult(
                name="storage",
                status=status.value,
                message=message,
                details={
                    "disk_usage_percent": disk_info.usage_percent,
                    "free_bytes": disk_info.free_bytes,
                    "total_models": sum(s.model_count for s in model_stats.values()),
                    "libraries": len(model_stats),
                    "registry_exists": registry_path.exists()
                },
                timestamp=datetime.utcnow().isoformat() + "Z",
                duration_ms=duration
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Storage health check failed: {e}")
            
            return HealthCheckResult(
                name="storage",
                status=HealthStatus.CRITICAL.value,
                message=f"Storage health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow().isoformat() + "Z",
                duration_ms=duration
            )
    
    async def check_registry_health(self) -> HealthCheckResult:
        """Check registry system health."""
        start_time = datetime.utcnow()
        
        try:
            registry_path = self.models_root / "llm_registry.json"
            schema_path = self.models_root / "registry.schema.json"
            
            status = HealthStatus.HEALTHY
            messages = []
            details = {}
            
            # Check registry file exists and is readable
            if not registry_path.exists():
                status = HealthStatus.CRITICAL
                messages.append("Registry file missing")
                details["registry_exists"] = False
            else:
                details["registry_exists"] = True
                
                try:
                    with open(registry_path, 'r') as f:
                        registry_data = json.load(f)
                    
                    details["registry_entries"] = len(registry_data)
                    details["registry_size_bytes"] = registry_path.stat().st_size
                    
                    # Check for empty registry
                    if len(registry_data) == 0:
                        status = HealthStatus.WARNING
                        messages.append("Registry is empty")
                    
                except json.JSONDecodeError as e:
                    status = HealthStatus.CRITICAL
                    messages.append(f"Registry JSON invalid: {str(e)}")
                except Exception as e:
                    status = HealthStatus.CRITICAL
                    messages.append(f"Cannot read registry: {str(e)}")
            
            # Check schema file
            if not schema_path.exists():
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
                messages.append("Registry schema missing")
                details["schema_exists"] = False
            else:
                details["schema_exists"] = True
            
            # Check registry backup
            backup_pattern = f"{registry_path.name}.backup*"
            backup_files = list(registry_path.parent.glob(backup_pattern))
            details["backup_count"] = len(backup_files)
            
            if len(backup_files) == 0:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
                messages.append("No registry backups found")
            
            message = "; ".join(messages) if messages else "Registry system healthy"
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return HealthCheckResult(
                name="registry",
                status=status.value,
                message=message,
                details=details,
                timestamp=datetime.utcnow().isoformat() + "Z",
                duration_ms=duration
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Registry health check failed: {e}")
            
            return HealthCheckResult(
                name="registry",
                status=HealthStatus.CRITICAL.value,
                message=f"Registry health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow().isoformat() + "Z",
                duration_ms=duration
            )
    
    async def check_metrics_health(self) -> HealthCheckResult:
        """Check metrics system health."""
        start_time = datetime.utcnow()
        
        try:
            metrics_info = self.metrics.get_metrics_summary()
            
            status = HealthStatus.HEALTHY
            messages = []
            
            # Check if Prometheus is available
            if not metrics_info["metrics_manager_info"]["prometheus_available"]:
                status = HealthStatus.WARNING
                messages.append("Prometheus client not available")
            
            # Check registered metrics count
            registered_count = len(metrics_info["registered_metrics"])
            expected_count = 19  # Expected number of metrics
            
            if registered_count < expected_count:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
                messages.append(f"Only {registered_count}/{expected_count} metrics registered")
            
            message = "; ".join(messages) if messages else "Metrics system healthy"
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return HealthCheckResult(
                name="metrics",
                status=status.value,
                message=message,
                details={
                    "prometheus_available": metrics_info["metrics_manager_info"]["prometheus_available"],
                    "registered_metrics": registered_count,
                    "expected_metrics": expected_count
                },
                timestamp=datetime.utcnow().isoformat() + "Z",
                duration_ms=duration
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Metrics health check failed: {e}")
            
            return HealthCheckResult(
                name="metrics",
                status=HealthStatus.CRITICAL.value,
                message=f"Metrics health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow().isoformat() + "Z",
                duration_ms=duration
            )
    
    async def check_error_tracking_health(self) -> HealthCheckResult:
        """Check error tracking system health."""
        start_time = datetime.utcnow()
        
        try:
            # Get recent error statistics
            error_stats = self.error_tracker.get_error_statistics(hours=24)
            
            status = HealthStatus.HEALTHY
            messages = []
            
            if "error" in error_stats:
                status = HealthStatus.WARNING
                messages.append(f"Error statistics unavailable: {error_stats['error']}")
            else:
                total_errors = error_stats.get("total_errors", 0)
                error_rate = error_stats.get("error_rate_per_hour", 0)
                
                # Check error rate thresholds
                if error_rate > 10:  # More than 10 errors per hour
                    status = HealthStatus.CRITICAL
                    messages.append(f"High error rate: {error_rate:.1f}/hour")
                elif error_rate > 5:  # More than 5 errors per hour
                    status = HealthStatus.WARNING
                    messages.append(f"Elevated error rate: {error_rate:.1f}/hour")
                
                # Check for critical errors
                by_severity = error_stats.get("by_severity", {})
                critical_errors = by_severity.get("critical", 0)
                
                if critical_errors > 0:
                    status = HealthStatus.CRITICAL
                    messages.append(f"{critical_errors} critical errors in last 24h")
            
            message = "; ".join(messages) if messages else "Error tracking healthy"
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return HealthCheckResult(
                name="error_tracking",
                status=status.value,
                message=message,
                details=error_stats,
                timestamp=datetime.utcnow().isoformat() + "Z",
                duration_ms=duration
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Error tracking health check failed: {e}")
            
            return HealthCheckResult(
                name="error_tracking",
                status=HealthStatus.CRITICAL.value,
                message=f"Error tracking health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow().isoformat() + "Z",
                duration_ms=duration
            )
    
    async def check_external_dependencies(self) -> HealthCheckResult:
        """Check external dependencies health."""
        start_time = datetime.utcnow()
        
        try:
            import aiohttp
            
            status = HealthStatus.HEALTHY
            messages = []
            details = {}
            
            # Check HuggingFace Hub connectivity
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.get("https://huggingface.co/api/models?limit=1") as response:
                        if response.status == 200:
                            details["huggingface_hub"] = "accessible"
                        else:
                            status = HealthStatus.WARNING
                            messages.append(f"HuggingFace Hub returned {response.status}")
                            details["huggingface_hub"] = f"error_{response.status}"
            except asyncio.TimeoutError:
                status = HealthStatus.WARNING
                messages.append("HuggingFace Hub timeout")
                details["huggingface_hub"] = "timeout"
            except Exception as e:
                status = HealthStatus.WARNING
                messages.append(f"HuggingFace Hub error: {str(e)}")
                details["huggingface_hub"] = f"error: {str(e)}"
            
            # Check if required Python packages are available
            required_packages = [
                "huggingface_hub",
                "transformers", 
                "torch",
                "numpy"
            ]
            
            missing_packages = []
            for package in required_packages:
                try:
                    __import__(package)
                    details[f"package_{package}"] = "available"
                except ImportError:
                    missing_packages.append(package)
                    details[f"package_{package}"] = "missing"
            
            if missing_packages:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
                messages.append(f"Missing packages: {', '.join(missing_packages)}")
            
            message = "; ".join(messages) if messages else "External dependencies healthy"
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return HealthCheckResult(
                name="external_dependencies",
                status=status.value,
                message=message,
                details=details,
                timestamp=datetime.utcnow().isoformat() + "Z",
                duration_ms=duration
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"External dependencies health check failed: {e}")
            
            return HealthCheckResult(
                name="external_dependencies",
                status=HealthStatus.CRITICAL.value,
                message=f"External dependencies health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow().isoformat() + "Z",
                duration_ms=duration
            )
    
    async def run_all_health_checks(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status."""
        start_time = datetime.utcnow()
        
        try:
            # Run all health checks concurrently
            checks = await asyncio.gather(
                self.check_storage_health(),
                self.check_registry_health(),
                self.check_metrics_health(),
                self.check_error_tracking_health(),
                self.check_external_dependencies(),
                return_exceptions=True
            )
            
            results = {}
            overall_status = HealthStatus.HEALTHY
            
            # Process results
            check_names = ["storage", "registry", "metrics", "error_tracking", "external_dependencies"]
            
            for i, check in enumerate(checks):
                if isinstance(check, Exception):
                    # Handle exceptions from individual checks
                    results[check_names[i]] = HealthCheckResult(
                        name=check_names[i],
                        status=HealthStatus.CRITICAL.value,
                        message=f"Health check failed: {str(check)}",
                        details={"error": str(check)},
                        timestamp=datetime.utcnow().isoformat() + "Z",
                        duration_ms=0
                    )
                    overall_status = HealthStatus.CRITICAL
                else:
                    results[check_names[i]] = check
                    
                    # Determine overall status
                    check_status = HealthStatus(check.status)
                    if check_status == HealthStatus.CRITICAL:
                        overall_status = HealthStatus.CRITICAL
                    elif check_status == HealthStatus.WARNING and overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.WARNING
            
            # Calculate summary statistics
            total_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            healthy_checks = sum(1 for r in results.values() if r.status == HealthStatus.HEALTHY.value)
            warning_checks = sum(1 for r in results.values() if r.status == HealthStatus.WARNING.value)
            critical_checks = sum(1 for r in results.values() if r.status == HealthStatus.CRITICAL.value)
            
            return {
                "overall_status": overall_status.value,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "total_duration_ms": total_duration,
                "summary": {
                    "total_checks": len(results),
                    "healthy": healthy_checks,
                    "warning": warning_checks,
                    "critical": critical_checks
                },
                "checks": {name: asdict(result) for name, result in results.items()}
            }
            
        except Exception as e:
            logger.error(f"Failed to run health checks: {e}")
            return {
                "overall_status": HealthStatus.CRITICAL.value,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": str(e)
            }
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """Get a quick health summary without running full checks."""
        try:
            # Quick checks that don't require external calls
            registry_exists = (self.models_root / "llm_registry.json").exists()
            disk_info = self.storage_monitor.get_disk_usage()
            
            status = HealthStatus.HEALTHY
            if disk_info.usage_percent > 90:
                status = HealthStatus.CRITICAL
            elif disk_info.usage_percent > 80 or not registry_exists:
                status = HealthStatus.WARNING
            
            return {
                "status": status.value,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "quick_checks": {
                    "registry_exists": registry_exists,
                    "disk_usage_percent": disk_info.usage_percent,
                    "free_bytes": disk_info.free_bytes
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get health summary: {e}")
            return {
                "status": HealthStatus.UNKNOWN.value,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": str(e)
            }


# Global health checker instance
_health_checker: Optional[ModelOrchestratorHealthChecker] = None


def get_model_orchestrator_health_checker(models_root: Path = None) -> ModelOrchestratorHealthChecker:
    """Get the global model orchestrator health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = ModelOrchestratorHealthChecker(models_root)
    return _health_checker