"""
Agent Monitor Service

This service provides monitoring capabilities for agents, including performance
monitoring, health checks, and metrics collection.
"""

from typing import Dict, List, Any, Optional, Union, Callable
import logging
import time
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import threading
import json

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Enumeration of agent statuses."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class HealthStatus(Enum):
    """Enumeration of health statuses."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class AgentMetrics:
    """Metrics for an agent."""
    agent_id: str
    timestamp: datetime
    status: AgentStatus
    health: HealthStatus
    execution_count: int
    success_count: int
    failure_count: int
    average_execution_time: float
    last_execution_time: Optional[datetime]
    current_memory_usage: float
    max_memory_usage: float
    current_cpu_usage: float
    max_cpu_usage: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentHealthCheck:
    """Health check result for an agent."""
    agent_id: str
    timestamp: datetime
    status: HealthStatus
    checks: Dict[str, bool]
    errors: List[str]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentExecutionRecord:
    """Record of an agent execution."""
    execution_id: str
    agent_id: str
    start_time: datetime
    end_time: Optional[datetime]
    status: AgentStatus
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentMonitor:
    """
    Provides monitoring capabilities for agents.
    
    This class is responsible for:
    - Monitoring agent performance and health
    - Collecting agent metrics
    - Tracking agent executions
    - Providing health checks for agents
    """
    
    def __init__(self, check_interval: float = 60.0):
        self._check_interval = check_interval
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._metrics: Dict[str, List[AgentMetrics]] = {}
        self._health_checks: Dict[str, AgentHealthCheck] = {}
        self._execution_records: Dict[str, AgentExecutionRecord] = {}
        self._max_records_per_agent = 1000
        
        # Health check functions
        self._health_check_functions: Dict[str, Callable] = {}
        
        # Callbacks for monitoring events
        self._on_status_change: Optional[Callable[[str, AgentStatus, AgentStatus], None]] = None
        self._on_health_change: Optional[Callable[[str, HealthStatus, HealthStatus], None]] = None
        self._on_execution_start: Optional[Callable[[str, str], None]] = None
        self._on_execution_complete: Optional[Callable[[str, str, AgentStatus], None]] = None
        
        # Monitoring thread
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()
        self._monitoring_active = False
        
        # Initialize default health checks
        self._initialize_default_health_checks()
    
    def register_agent(self, agent_id: str, agent_info: Dict[str, Any]) -> None:
        """
        Register an agent for monitoring.
        
        Args:
            agent_id: ID of the agent
            agent_info: Information about the agent
        """
        self._agents[agent_id] = agent_info
        self._metrics[agent_id] = []
        logger.info(f"Registered agent for monitoring: {agent_id}")
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from monitoring.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            True if agent was unregistered, False if not found
        """
        if agent_id in self._agents:
            del self._agents[agent_id]
            del self._metrics[agent_id]
            
            if agent_id in self._health_checks:
                del self._health_checks[agent_id]
            
            logger.info(f"Unregistered agent from monitoring: {agent_id}")
            return True
        else:
            logger.warning(f"Attempted to unregister non-existent agent: {agent_id}")
            return False
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a monitored agent."""
        return self._agents.get(agent_id)
    
    def get_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all monitored agents."""
        return self._agents.copy()
    
    def record_execution_start(self, execution_id: str, agent_id: str, input_data: Dict[str, Any]) -> None:
        """
        Record the start of an agent execution.
        
        Args:
            execution_id: ID of the execution
            agent_id: ID of the agent
            input_data: Input data for the execution
        """
        record = AgentExecutionRecord(
            execution_id=execution_id,
            agent_id=agent_id,
            start_time=datetime.now(),
            end_time=None,
            status=AgentStatus.RUNNING,
            input_data=input_data,
            output_data=None,
            error_message=None
        )
        
        self._execution_records[execution_id] = record
        
        # Update agent status
        self._update_agent_status(agent_id, AgentStatus.RUNNING)
        
        # Call execution start callback if set
        if self._on_execution_start:
            self._on_execution_start(agent_id, execution_id)
        
        logger.debug(f"Recorded execution start: {execution_id} for agent {agent_id}")
    
    def record_execution_complete(
        self,
        execution_id: str,
        agent_id: str,
        status: AgentStatus,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Record the completion of an agent execution.
        
        Args:
            execution_id: ID of the execution
            agent_id: ID of the agent
            status: Status of the execution
            output_data: Output data from the execution
            error_message: Error message if execution failed
        """
        record = self._execution_records.get(execution_id)
        if record:
            record.end_time = datetime.now()
            record.status = status
            record.output_data = output_data
            record.error_message = error_message
            
            # Update agent status
            self._update_agent_status(agent_id, status)
            
            # Update metrics
            self._update_agent_metrics(agent_id, record)
            
            # Call execution complete callback if set
            if self._on_execution_complete:
                self._on_execution_complete(agent_id, execution_id, status)
            
            logger.debug(f"Recorded execution complete: {execution_id} for agent {agent_id}")
        else:
            logger.warning(f"Attempted to complete non-existent execution: {execution_id}")
    
    def get_execution_record(self, execution_id: str) -> Optional[AgentExecutionRecord]:
        """Get an execution record by ID."""
        return self._execution_records.get(execution_id)
    
    def get_execution_records_for_agent(self, agent_id: str, limit: int = 100) -> List[AgentExecutionRecord]:
        """Get execution records for an agent."""
        records = [
            record for record in self._execution_records.values()
            if record.agent_id == agent_id
        ]
        
        # Sort by start time (newest first)
        records.sort(key=lambda r: r.start_time, reverse=True)
        
        # Apply limit
        return records[:limit]
    
    def get_agent_metrics(self, agent_id: str, limit: int = 100) -> List[AgentMetrics]:
        """Get metrics for an agent."""
        if agent_id not in self._metrics:
            return []
        
        metrics = self._metrics[agent_id]
        
        # Sort by timestamp (newest first)
        metrics.sort(key=lambda m: m.timestamp, reverse=True)
        
        # Apply limit
        return metrics[:limit]
    
    def get_latest_metrics(self, agent_id: str) -> Optional[AgentMetrics]:
        """Get the latest metrics for an agent."""
        metrics = self.get_agent_metrics(agent_id, 1)
        return metrics[0] if metrics else None
    
    def get_agent_health(self, agent_id: str) -> Optional[AgentHealthCheck]:
        """Get the latest health check result for an agent."""
        return self._health_checks.get(agent_id)
    
    def perform_health_check(self, agent_id: str) -> AgentHealthCheck:
        """
        Perform a health check for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Health check result
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent not registered: {agent_id}")
        
        # Perform health checks
        checks = {}
        errors = []
        
        # Check if agent is running
        metrics = self.get_latest_metrics(agent_id)
        if metrics:
            # Check memory usage
            if metrics.current_memory_usage > 0.9 * metrics.max_memory_usage:
                checks["memory_usage"] = False
                errors.append(f"High memory usage: {metrics.current_memory_usage:.2f} > {metrics.max_memory_usage:.2f}")
            else:
                checks["memory_usage"] = True
            
            # Check CPU usage
            if metrics.current_cpu_usage > 0.9 * metrics.max_cpu_usage:
                checks["cpu_usage"] = False
                errors.append(f"High CPU usage: {metrics.current_cpu_usage:.2f} > {metrics.max_cpu_usage:.2f}")
            else:
                checks["cpu_usage"] = True
            
            # Check success rate
            if metrics.execution_count > 0:
                success_rate = metrics.success_count / metrics.execution_count
                if success_rate < 0.8:
                    checks["success_rate"] = False
                    errors.append(f"Low success rate: {success_rate:.2f} < 0.8")
                else:
                    checks["success_rate"] = True
            else:
                checks["success_rate"] = True
            
            # Check execution time
            if metrics.average_execution_time > 60.0:  # More than 60 seconds
                checks["execution_time"] = False
                errors.append(f"High average execution time: {metrics.average_execution_time:.2f} > 60.0")
            else:
                checks["execution_time"] = True
        else:
            # No metrics available
            checks["metrics_available"] = False
            errors.append("No metrics available")
        
        # Perform custom health checks
        for check_name, check_func in self._health_check_functions.items():
            try:
                result = check_func(agent_id)
                checks[check_name] = result
                if not result:
                    errors.append(f"Custom health check failed: {check_name}")
            except Exception as e:
                checks[check_name] = False
                errors.append(f"Custom health check error: {check_name} - {str(e)}")
        
        # Determine overall health status
        if all(checks.values()):
            health_status = HealthStatus.HEALTHY
        elif any(checks.values()):
            health_status = HealthStatus.DEGRADED
        else:
            health_status = HealthStatus.UNHEALTHY
        
        # Create health check result
        health_check = AgentHealthCheck(
            agent_id=agent_id,
            timestamp=datetime.now(),
            status=health_status,
            checks=checks,
            errors=errors
        )
        
        # Store health check result
        previous_health = self._health_checks.get(agent_id)
        self._health_checks[agent_id] = health_check
        
        # Call health change callback if set
        if previous_health and previous_health.status != health_status and self._on_health_change:
            self._on_health_change(agent_id, previous_health.status, health_status)
        
        logger.info(f"Health check for agent {agent_id}: {health_status.value}")
        return health_check
    
    def register_health_check(self, check_name: str, check_func: Callable[[str], bool]) -> None:
        """
        Register a custom health check function.
        
        Args:
            check_name: Name of the health check
            check_func: Function that performs the health check
        """
        self._health_check_functions[check_name] = check_func
        logger.info(f"Registered health check: {check_name}")
    
    def unregister_health_check(self, check_name: str) -> bool:
        """
        Unregister a custom health check function.
        
        Args:
            check_name: Name of the health check
            
        Returns:
            True if health check was unregistered, False if not found
        """
        if check_name in self._health_check_functions:
            del self._health_check_functions[check_name]
            logger.info(f"Unregistered health check: {check_name}")
            return True
        else:
            logger.warning(f"Attempted to unregister non-existent health check: {check_name}")
            return False
    
    def start_monitoring(self) -> None:
        """Start the monitoring thread."""
        if not self._monitoring_active:
            self._stop_monitoring.clear()
            self._monitoring_thread = threading.Thread(target=self._monitoring_loop)
            self._monitoring_thread.daemon = True
            self._monitoring_thread.start()
            self._monitoring_active = True
            logger.info("Started agent monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring thread."""
        if self._monitoring_active:
            self._stop_monitoring.set()
            if self._monitoring_thread:
                self._monitoring_thread.join(timeout=5.0)
            self._monitoring_active = False
            logger.info("Stopped agent monitoring")
    
    def set_monitoring_callbacks(
        self,
        on_status_change: Optional[Callable[[str, AgentStatus, AgentStatus], None]] = None,
        on_health_change: Optional[Callable[[str, HealthStatus, HealthStatus], None]] = None,
        on_execution_start: Optional[Callable[[str, str], None]] = None,
        on_execution_complete: Optional[Callable[[str, str, AgentStatus], None]] = None
    ) -> None:
        """Set callbacks for monitoring events."""
        self._on_status_change = on_status_change
        self._on_health_change = on_health_change
        self._on_execution_start = on_execution_start
        self._on_execution_complete = on_execution_complete
    
    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about monitoring.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_agents": len(self._agents),
            "total_execution_records": len(self._execution_records),
            "agents_by_status": {},
            "agents_by_health": {},
            "health_check_functions": list(self._health_check_functions.keys()),
            "monitoring_active": self._monitoring_active
        }
        
        # Count agents by status
        for agent_id in self._agents:
            metrics = self.get_latest_metrics(agent_id)
            if metrics:
                status = metrics.status.value
                if status not in stats["agents_by_status"]:
                    stats["agents_by_status"][status] = 0
                stats["agents_by_status"][status] += 1
        
        # Count agents by health
        for agent_id, health_check in self._health_checks.items():
            health = health_check.status.value
            if health not in stats["agents_by_health"]:
                stats["agents_by_health"][health] = 0
            stats["agents_by_health"][health] += 1
        
        return stats
    
    def export_metrics(self, agent_id: str, file_path: str) -> bool:
        """
        Export metrics for an agent to a file.
        
        Args:
            agent_id: ID of the agent
            file_path: Path to the export file
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            metrics = self.get_agent_metrics(agent_id)
            
            # Convert to dictionaries for JSON serialization
            metrics_dicts = []
            for metric in metrics:
                metric_dict = {
                    "agent_id": metric.agent_id,
                    "timestamp": metric.timestamp.isoformat(),
                    "status": metric.status.value,
                    "health": metric.health.value,
                    "execution_count": metric.execution_count,
                    "success_count": metric.success_count,
                    "failure_count": metric.failure_count,
                    "average_execution_time": metric.average_execution_time,
                    "last_execution_time": metric.last_execution_time.isoformat() if metric.last_execution_time else None,
                    "current_memory_usage": metric.current_memory_usage,
                    "max_memory_usage": metric.max_memory_usage,
                    "current_cpu_usage": metric.current_cpu_usage,
                    "max_cpu_usage": metric.max_cpu_usage,
                    "metadata": metric.metadata
                }
                metrics_dicts.append(metric_dict)
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(metrics_dicts, f, indent=2)
            
            logger.info(f"Exported {len(metrics_dicts)} metrics for agent {agent_id} to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export metrics for agent {agent_id}: {str(e)}")
            return False
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while not self._stop_monitoring.is_set():
            try:
                # Perform health checks for all agents
                for agent_id in self._agents:
                    try:
                        self.perform_health_check(agent_id)
                    except Exception as e:
                        logger.error(f"Health check failed for agent {agent_id}: {str(e)}")
                
                # Wait for next check
                self._stop_monitoring.wait(self._check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                self._stop_monitoring.wait(self._check_interval)
    
    def _update_agent_status(self, agent_id: str, status: AgentStatus) -> None:
        """Update the status of an agent."""
        metrics = self.get_latest_metrics(agent_id)
        previous_status = metrics.status if metrics else AgentStatus.UNKNOWN
        
        if previous_status != status:
            # Call status change callback if set
            if self._on_status_change:
                self._on_status_change(agent_id, previous_status, status)
            
            logger.info(f"Agent {agent_id} status changed from {previous_status.value} to {status.value}")
    
    def _update_agent_metrics(self, agent_id: str, record: AgentExecutionRecord) -> None:
        """Update the metrics for an agent."""
        # Get previous metrics
        previous_metrics = self.get_latest_metrics(agent_id)
        
        # Calculate execution time
        execution_time = None
        if record.end_time:
            execution_time = (record.end_time - record.start_time).total_seconds()
        
        # Update metrics
        if previous_metrics:
            execution_count = previous_metrics.execution_count + 1
            success_count = previous_metrics.success_count + (1 if record.status == AgentStatus.COMPLETED else 0)
            failure_count = previous_metrics.failure_count + (1 if record.status in [AgentStatus.FAILED, AgentStatus.TIMEOUT] else 0)
            
            # Update average execution time
            if execution_time is not None:
                if previous_metrics.average_execution_time > 0:
                    average_execution_time = (previous_metrics.average_execution_time * (execution_count - 1) + execution_time) / execution_count
                else:
                    average_execution_time = execution_time
            else:
                average_execution_time = previous_metrics.average_execution_time
            
            # Update memory and CPU usage (in a real implementation, this would come from system monitoring)
            current_memory_usage = previous_metrics.current_memory_usage
            max_memory_usage = max(previous_metrics.max_memory_usage, current_memory_usage)
            current_cpu_usage = previous_metrics.current_cpu_usage
            max_cpu_usage = max(previous_metrics.max_cpu_usage, current_cpu_usage)
            
            # Update health status (in a real implementation, this would come from health checks)
            health = previous_metrics.health
            
            # Create new metrics
            metrics = AgentMetrics(
                agent_id=agent_id,
                timestamp=datetime.now(),
                status=record.status,
                health=health,
                execution_count=execution_count,
                success_count=success_count,
                failure_count=failure_count,
                average_execution_time=average_execution_time,
                last_execution_time=record.end_time,
                current_memory_usage=current_memory_usage,
                max_memory_usage=max_memory_usage,
                current_cpu_usage=current_cpu_usage,
                max_cpu_usage=max_cpu_usage
            )
        else:
            # Create initial metrics
            metrics = AgentMetrics(
                agent_id=agent_id,
                timestamp=datetime.now(),
                status=record.status,
                health=HealthStatus.UNKNOWN,
                execution_count=1,
                success_count=1 if record.status == AgentStatus.COMPLETED else 0,
                failure_count=1 if record.status in [AgentStatus.FAILED, AgentStatus.TIMEOUT] else 0,
                average_execution_time=execution_time or 0.0,
                last_execution_time=record.end_time,
                current_memory_usage=0.0,
                max_memory_usage=0.0,
                current_cpu_usage=0.0,
                max_cpu_usage=0.0
            )
        
        # Add metrics to history
        self._metrics[agent_id].append(metrics)
        
        # Limit the number of metrics stored
        if len(self._metrics[agent_id]) > self._max_records_per_agent:
            self._metrics[agent_id] = self._metrics[agent_id][-self._max_records_per_agent:]
    
    def _initialize_default_health_checks(self) -> None:
        """Initialize default health check functions."""
        # In a real implementation, these would be actual health check functions
        pass