"""
Internal metrics collection for the agents domain.

This module provides metrics collection and reporting functionality for agents.
These are not part of the public API and should not be imported from outside the agents domain.
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from .agent_schemas import AgentType, TaskStatus


class AgentMetrics:
    """Base class for agent metrics."""
    
    def __init__(self, agent_id: UUID):
        """Initialize agent metrics."""
        self.agent_id = agent_id
        self.created_at = datetime.now()
        self.metrics: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "agent_id": str(self.agent_id),
            "created_at": self.created_at.isoformat(),
            "metrics": self.metrics
        }


class AgentPerformanceMetrics(AgentMetrics):
    """Performance metrics for agents."""
    
    def __init__(self, agent_id: UUID):
        """Initialize performance metrics."""
        super().__init__(agent_id)
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_execution_time = 0.0
        self.min_execution_time = float('inf')
        self.max_execution_time = 0.0
        self.avg_execution_time = 0.0
        self.last_execution_time: Optional[datetime] = None
        self.memory_usage: List[float] = []
        self.cpu_usage: List[float] = []
        self.error_count = 0
        self.error_messages: List[str] = []
    
    def record_task_start(self, task_id: UUID) -> None:
        """Record task start."""
        self.task_count += 1
        self.metrics[f"task_{task_id}_start"] = time.time()
    
    def record_task_completion(
        self, 
        task_id: UUID, 
        success: bool, 
        execution_time: float,
        memory_usage: Optional[float] = None,
        cpu_usage: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Record task completion."""
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            self.error_count += 1
            if error_message:
                self.error_messages.append(error_message)
        
        self.total_execution_time += execution_time
        self.min_execution_time = min(self.min_execution_time, execution_time)
        self.max_execution_time = max(self.max_execution_time, execution_time)
        self.avg_execution_time = self.total_execution_time / self.task_count
        self.last_execution_time = datetime.now()
        
        if memory_usage is not None:
            self.memory_usage.append(memory_usage)
        
        if cpu_usage is not None:
            self.cpu_usage.append(cpu_usage)
        
        self.metrics[f"task_{task_id}_completion"] = {
            "success": success,
            "execution_time": execution_time,
            "memory_usage": memory_usage,
            "cpu_usage": cpu_usage,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.task_count == 0:
            return 0.0
        return (self.success_count / self.task_count) * 100
    
    def get_failure_rate(self) -> float:
        """Get failure rate as percentage."""
        if self.task_count == 0:
            return 0.0
        return (self.failure_count / self.task_count) * 100
    
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
        if self.task_count == 0:
            return 0.0
        return (self.error_count / self.task_count) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert performance metrics to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "task_count": self.task_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_execution_time": self.total_execution_time,
            "min_execution_time": self.min_execution_time if self.min_execution_time != float('inf') else 0,
            "max_execution_time": self.max_execution_time,
            "avg_execution_time": self.avg_execution_time,
            "last_execution_time": self.last_execution_time.isoformat() if self.last_execution_time else None,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "error_count": self.error_count,
            "error_messages": self.error_messages,
            "success_rate": self.get_success_rate(),
            "failure_rate": self.get_failure_rate(),
            "avg_memory_usage": self.get_avg_memory_usage(),
            "avg_cpu_usage": self.get_avg_cpu_usage(),
            "error_rate": self.get_error_rate()
        })
        return base_dict


class AgentTaskMetrics(AgentMetrics):
    """Metrics for individual agent tasks."""
    
    def __init__(self, task_id: UUID, agent_id: UUID):
        """Initialize task metrics."""
        super().__init__(agent_id)
        self.task_id = task_id
        self.status: Optional[TaskStatus] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.execution_time: Optional[float] = None
        self.memory_usage: Optional[float] = None
        self.cpu_usage: Optional[float] = None
        self.error_message: Optional[str] = None
        self.input_size: Optional[int] = None
        self.output_size: Optional[int] = None
        self.tool_calls: List[Dict[str, Any]] = []
        self.memory_operations: List[Dict[str, Any]] = []
    
    def record_start(self) -> None:
        """Record task start."""
        self.status = TaskStatus.RUNNING
        self.start_time = datetime.now()
        self.metrics["start_time"] = self.start_time.isoformat()
    
    def record_completion(
        self,
        success: bool,
        execution_time: Optional[float] = None,
        memory_usage: Optional[float] = None,
        cpu_usage: Optional[float] = None,
        error_message: Optional[str] = None,
        input_size: Optional[int] = None,
        output_size: Optional[int] = None
    ) -> None:
        """Record task completion."""
        self.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
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
    
    def record_tool_call(self, tool_name: str, execution_time: float, success: bool) -> None:
        """Record a tool call."""
        tool_call = {
            "tool_name": tool_name,
            "execution_time": execution_time,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        self.tool_calls.append(tool_call)
        
        if "tool_calls" not in self.metrics:
            self.metrics["tool_calls"] = []
        self.metrics["tool_calls"].append(tool_call)
    
    def record_memory_operation(self, operation: str, memory_type: str, size: int, execution_time: float) -> None:
        """Record a memory operation."""
        memory_op = {
            "operation": operation,
            "memory_type": memory_type,
            "size": size,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        self.memory_operations.append(memory_op)
        
        if "memory_operations" not in self.metrics:
            self.metrics["memory_operations"] = []
        self.metrics["memory_operations"].append(memory_op)
    
    def get_total_tool_time(self) -> float:
        """Get total time spent on tool calls."""
        return sum(call["execution_time"] for call in self.tool_calls)
    
    def get_total_memory_time(self) -> float:
        """Get total time spent on memory operations."""
        return sum(op["execution_time"] for op in self.memory_operations)
    
    def get_tool_success_rate(self) -> float:
        """Get tool success rate as percentage."""
        if not self.tool_calls:
            return 0.0
        success_count = sum(1 for call in self.tool_calls if call["success"])
        return (success_count / len(self.tool_calls)) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task metrics to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "task_id": str(self.task_id),
            "status": self.status.value if self.status else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time": self.execution_time,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "error_message": self.error_message,
            "input_size": self.input_size,
            "output_size": self.output_size,
            "tool_calls": self.tool_calls,
            "memory_operations": self.memory_operations,
            "total_tool_time": self.get_total_tool_time(),
            "total_memory_time": self.get_total_memory_time(),
            "tool_success_rate": self.get_tool_success_rate()
        })
        return base_dict


class AgentMetricsCollector:
    """Collector for agent metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.agent_metrics: Dict[UUID, AgentPerformanceMetrics] = {}
        self.task_metrics: Dict[UUID, AgentTaskMetrics] = {}
        self.agent_type_metrics: Dict[AgentType, Dict[str, Any]] = {}
    
    def get_or_create_agent_metrics(self, agent_id: UUID) -> AgentPerformanceMetrics:
        """Get or create agent metrics."""
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = AgentPerformanceMetrics(agent_id)
        return self.agent_metrics[agent_id]
    
    def get_or_create_task_metrics(self, task_id: UUID, agent_id: UUID) -> AgentTaskMetrics:
        """Get or create task metrics."""
        if task_id not in self.task_metrics:
            self.task_metrics[task_id] = AgentTaskMetrics(task_id, agent_id)
        return self.task_metrics[task_id]
    
    def record_agent_type_metrics(self, agent_type: AgentType, metrics: Dict[str, Any]) -> None:
        """Record agent type metrics."""
        if agent_type not in self.agent_type_metrics:
            self.agent_type_metrics[agent_type] = {}
        self.agent_type_metrics[agent_type].update(metrics)
    
    def get_agent_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all agent metrics."""
        summary = {
            "total_agents": len(self.agent_metrics),
            "total_tasks": len(self.task_metrics),
            "agent_metrics": {str(agent_id): metrics.to_dict() for agent_id, metrics in self.agent_metrics.items()},
            "task_metrics": {str(task_id): metrics.to_dict() for task_id, metrics in self.task_metrics.items()},
            "agent_type_metrics": {agent_type.value: metrics for agent_type, metrics in self.agent_type_metrics.items()}
        }
        return summary