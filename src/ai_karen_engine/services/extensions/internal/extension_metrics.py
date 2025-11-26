"""
Internal metrics collection for the extensions domain.

This module provides metrics collection and reporting functionality for extensions.
These are not part of the public API and should not be imported from outside the extensions domain.
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from .extension_schemas import ExtensionType, ExecutionStatus


class ExtensionMetrics:
    """Base class for extension metrics."""
    
    def __init__(self, extension_id: UUID):
        """Initialize extension metrics."""
        self.extension_id = extension_id
        self.created_at = datetime.now()
        self.metrics: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "extension_id": str(self.extension_id),
            "created_at": self.created_at.isoformat(),
            "metrics": self.metrics
        }


class ExtensionPerformanceMetrics(ExtensionMetrics):
    """Performance metrics for extensions."""
    
    def __init__(self, extension_id: UUID):
        """Initialize performance metrics."""
        super().__init__(extension_id)
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.timeout_count = 0
        self.total_execution_time = 0.0
        self.min_execution_time = float('inf')
        self.max_execution_time = 0.0
        self.avg_execution_time = 0.0
        self.last_execution_time: Optional[datetime] = None
        self.memory_usage: List[float] = []
        self.cpu_usage: List[float] = []
        self.error_count = 0
        self.error_messages: List[str] = []
        self.auth_failures = 0
        self.permission_failures = 0
    
    def record_execution_start(self, execution_id: UUID) -> None:
        """Record execution start."""
        self.execution_count += 1
        self.metrics[f"execution_{execution_id}_start"] = time.time()
    
    def record_execution_completion(
        self, 
        execution_id: UUID, 
        status: ExecutionStatus,
        execution_time: float,
        memory_usage: Optional[float] = None,
        cpu_usage: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Record execution completion."""
        if status == ExecutionStatus.COMPLETED:
            self.success_count += 1
        elif status == ExecutionStatus.FAILED:
            self.failure_count += 1
            self.error_count += 1
            if error_message:
                self.error_messages.append(error_message)
        elif status == ExecutionStatus.TIMEOUT:
            self.timeout_count += 1
            self.error_count += 1
            if error_message:
                self.error_messages.append(error_message)
        
        self.total_execution_time += execution_time
        self.min_execution_time = min(self.min_execution_time, execution_time)
        self.max_execution_time = max(self.max_execution_time, execution_time)
        self.avg_execution_time = self.total_execution_time / self.execution_count
        self.last_execution_time = datetime.now()
        
        if memory_usage is not None:
            self.memory_usage.append(memory_usage)
        
        if cpu_usage is not None:
            self.cpu_usage.append(cpu_usage)
        
        self.metrics[f"execution_{execution_id}_completion"] = {
            "status": status.value,
            "execution_time": execution_time,
            "memory_usage": memory_usage,
            "cpu_usage": cpu_usage,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat()
        }
    
    def record_auth_failure(self, error_message: str) -> None:
        """Record authentication failure."""
        self.auth_failures += 1
        self.error_count += 1
        self.error_messages.append(f"Auth failure: {error_message}")
    
    def record_permission_failure(self, error_message: str) -> None:
        """Record permission failure."""
        self.permission_failures += 1
        self.error_count += 1
        self.error_messages.append(f"Permission failure: {error_message}")
    
    def get_success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100
    
    def get_failure_rate(self) -> float:
        """Get failure rate as percentage."""
        if self.execution_count == 0:
            return 0.0
        return (self.failure_count / self.execution_count) * 100
    
    def get_timeout_rate(self) -> float:
        """Get timeout rate as percentage."""
        if self.execution_count == 0:
            return 0.0
        return (self.timeout_count / self.execution_count) * 100
    
    def get_avg_memory_usage(self) -> Optional[float]:
        """Get average memory usage."""
        if not self.memory_usage:
            return None
        return sum(self.memory_usage) / len(self.memory_usage)
    
    def get_avg_cpu_usage(self) -> Optional[float]:
        """Get average CPU usage."""
        if not self.cpu_usage:
            return None
        return sum(self.cpu_usage) / len(self.cpu_usage)
    
    def get_error_rate(self) -> float:
        """Get error rate as percentage."""
        if self.execution_count == 0:
            return 0.0
        return (self.error_count / self.execution_count) * 100
    
    def get_auth_failure_rate(self) -> float:
        """Get authentication failure rate as percentage."""
        if self.execution_count == 0:
            return 0.0
        return (self.auth_failures / self.execution_count) * 100
    
    def get_permission_failure_rate(self) -> float:
        """Get permission failure rate as percentage."""
        if self.execution_count == 0:
            return 0.0
        return (self.permission_failures / self.execution_count) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert performance metrics to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "timeout_count": self.timeout_count,
            "total_execution_time": self.total_execution_time,
            "min_execution_time": self.min_execution_time if self.min_execution_time != float('inf') else 0,
            "max_execution_time": self.max_execution_time,
            "avg_execution_time": self.avg_execution_time,
            "last_execution_time": self.last_execution_time.isoformat() if self.last_execution_time else None,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "error_count": self.error_count,
            "error_messages": self.error_messages,
            "auth_failures": self.auth_failures,
            "permission_failures": self.permission_failures,
            "success_rate": self.get_success_rate(),
            "failure_rate": self.get_failure_rate(),
            "timeout_rate": self.get_timeout_rate(),
            "avg_memory_usage": self.get_avg_memory_usage(),
            "avg_cpu_usage": self.get_avg_cpu_usage(),
            "error_rate": self.get_error_rate(),
            "auth_failure_rate": self.get_auth_failure_rate(),
            "permission_failure_rate": self.get_permission_failure_rate()
        })
        return base_dict


class ExtensionTaskMetrics(ExtensionMetrics):
    """Metrics for individual extension tasks."""
    
    def __init__(self, execution_id: UUID, extension_id: UUID):
        """Initialize task metrics."""
        super().__init__(extension_id)
        self.execution_id = execution_id
        self.status: Optional[ExecutionStatus] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.execution_time: Optional[float] = None
        self.memory_usage: Optional[float] = None
        self.cpu_usage: Optional[float] = None
        self.error_message: Optional[str] = None
        self.input_size: Optional[int] = None
        self.output_size: Optional[int] = None
        self.auth_success: bool = False
        self.permission_checks: List[Dict[str, Any]] = []
        self.resource_usage: List[Dict[str, Any]] = []
    
    def record_start(self) -> None:
        """Record task start."""
        self.status = ExecutionStatus.RUNNING
        self.start_time = datetime.now()
        self.metrics["start_time"] = self.start_time.isoformat()
    
    def record_completion(
        self,
        status: ExecutionStatus,
        execution_time: Optional[float] = None,
        memory_usage: Optional[float] = None,
        cpu_usage: Optional[float] = None,
        error_message: Optional[str] = None,
        input_size: Optional[int] = None,
        output_size: Optional[int] = None
    ) -> None:
        """Record task completion."""
        self.status = status
        self.end_time = datetime.now()
        
        if execution_time is None and self.start_time:
            self.execution_time = (self.end_time - self.start_time).total_seconds()
        else:
            self.execution_time = execution_time
        
        self.memory_usage = memory_usage
        self.cpu_usage = cpu_usage
        self.error_message = error_message
        self.input_size = input_size
        self.output_size = output_size
        
        self.metrics.update({
            "end_time": self.end_time.isoformat(),
            "status": self.status.value if self.status else None,
            "execution_time": self.execution_time,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "error_message": self.error_message,
            "input_size": self.input_size,
            "output_size": self.output_size
        })
    
    def record_auth_success(self) -> None:
        """Record authentication success."""
        self.auth_success = True
        self.metrics["auth_success"] = True
    
    def record_auth_failure(self, error_message: str) -> None:
        """Record authentication failure."""
        self.auth_success = False
        self.error_message = error_message
        self.metrics["auth_success"] = False
        self.metrics["auth_error"] = error_message
    
    def record_permission_check(self, resource: str, permission: str, granted: bool) -> None:
        """Record permission check."""
        permission_check = {
            "resource": resource,
            "permission": permission,
            "granted": granted,
            "timestamp": datetime.now().isoformat()
        }
        self.permission_checks.append(permission_check)
        
        if "permission_checks" not in self.metrics:
            self.metrics["permission_checks"] = []
        self.metrics["permission_checks"].append(permission_check)
    
    def record_resource_usage(self, resource_type: str, amount: float, unit: str) -> None:
        """Record resource usage."""
        resource_usage = {
            "resource_type": resource_type,
            "amount": amount,
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        }
        self.resource_usage.append(resource_usage)
        
        if "resource_usage" not in self.metrics:
            self.metrics["resource_usage"] = []
        self.metrics["resource_usage"].append(resource_usage)
    
    def get_total_resource_time(self) -> float:
        """Get total time spent on resource usage."""
        return sum(usage.get("time", 0) for usage in self.resource_usage)
    
    def get_permission_grant_rate(self) -> float:
        """Get permission grant rate as percentage."""
        if not self.permission_checks:
            return 0.0
        granted_count = sum(1 for check in self.permission_checks if check["granted"])
        return (granted_count / len(self.permission_checks)) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task metrics to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "execution_id": str(self.execution_id),
            "status": self.status.value if self.status else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time": self.execution_time,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "error_message": self.error_message,
            "input_size": self.input_size,
            "output_size": self.output_size,
            "auth_success": self.auth_success,
            "permission_checks": self.permission_checks,
            "resource_usage": self.resource_usage,
            "total_resource_time": self.get_total_resource_time(),
            "permission_grant_rate": self.get_permission_grant_rate()
        })
        return base_dict


class ExtensionMetricsCollector:
    """Collector for extension metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.extension_metrics: Dict[UUID, ExtensionPerformanceMetrics] = {}
        self.task_metrics: Dict[UUID, ExtensionTaskMetrics] = {}
        self.extension_type_metrics: Dict[ExtensionType, Dict[str, Any]] = {}
    
    def get_or_create_extension_metrics(self, extension_id: UUID) -> ExtensionPerformanceMetrics:
        """Get or create extension metrics."""
        if extension_id not in self.extension_metrics:
            self.extension_metrics[extension_id] = ExtensionPerformanceMetrics(extension_id)
        return self.extension_metrics[extension_id]
    
    def get_or_create_task_metrics(self, execution_id: UUID, extension_id: UUID) -> ExtensionTaskMetrics:
        """Get or create task metrics."""
        if execution_id not in self.task_metrics:
            self.task_metrics[execution_id] = ExtensionTaskMetrics(execution_id, extension_id)
        return self.task_metrics[execution_id]
    
    def record_extension_type_metrics(self, extension_type: ExtensionType, metrics: Dict[str, Any]) -> None:
        """Record extension type metrics."""
        if extension_type not in self.extension_type_metrics:
            self.extension_type_metrics[extension_type] = {}
        self.extension_type_metrics[extension_type].update(metrics)
    
    def get_extension_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all extension metrics."""
        summary = {
            "total_extensions": len(self.extension_metrics),
            "total_executions": len(self.task_metrics),
            "extension_metrics": {str(ext_id): metrics.to_dict() for ext_id, metrics in self.extension_metrics.items()},
            "task_metrics": {str(exec_id): metrics.to_dict() for exec_id, metrics in self.task_metrics.items()},
            "extension_type_metrics": {ext_type.value: metrics for ext_type, metrics in self.extension_type_metrics.items()}
        }
        return summary