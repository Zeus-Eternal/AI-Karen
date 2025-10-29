"""
Extension Debug Manager

Central manager for extension debugging and monitoring capabilities.
Coordinates logging, metrics, error tracking, profiling, tracing, and alerting.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import json

from .models import (
    LogEntry, MetricPoint, ErrorRecord, Alert, AlertSeverity,
    DebugSession, ExtensionHealthStatus, DiagnosticResult
)
from .logger import ExtensionLogger
from .metrics_collector import ExtensionMetricsCollector
from .error_tracker import ExtensionErrorTracker
from .profiler import ExtensionProfiler
from .tracer import ExtensionTracer
from .alerting import ExtensionAlertManager, AlertingConfiguration


@dataclass
class DebugConfiguration:
    """Configuration for debugging system."""
    logging_enabled: bool = True
    metrics_enabled: bool = True
    error_tracking_enabled: bool = True
    profiling_enabled: bool = False
    tracing_enabled: bool = False
    alerting_enabled: bool = True
    
    # Collection intervals
    metrics_interval: float = 30.0
    health_check_interval: float = 60.0
    
    # Storage limits
    max_log_entries: int = 10000
    max_metrics: int = 50000
    max_errors: int = 1000
    max_traces: int = 1000
    
    # Performance settings
    sampling_rate: float = 1.0
    profiling_overhead_limit: float = 5.0  # Max 5% overhead


class ExtensionDebugManager:
    """
    Central manager for extension debugging and monitoring.
    
    Features:
    - Unified debugging interface
    - Component coordination
    - Health monitoring
    - Debug session management
    - Performance impact monitoring
    - Diagnostic capabilities
    """
    
    def __init__(
        self,
        extension_id: str,
        extension_name: str,
        configuration: Optional[DebugConfiguration] = None
    ):
        self.extension_id = extension_id
        self.extension_name = extension_name
        self.configuration = configuration or DebugConfiguration()
        
        # Initialize components
        self.logger: Optional[ExtensionLogger] = None
        self.metrics_collector: Optional[ExtensionMetricsCollector] = None
        self.error_tracker: Optional[ExtensionErrorTracker] = None
        self.profiler: Optional[ExtensionProfiler] = None
        self.tracer: Optional[ExtensionTracer] = None
        self.alert_manager: Optional[ExtensionAlertManager] = None
        
        # Debug sessions
        self.active_sessions: Dict[str, DebugSession] = {}
        
        # Health monitoring
        self.last_health_check: Optional[datetime] = None
        self.health_status: Optional[ExtensionHealthStatus] = None
        
        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Performance monitoring
        self.debug_overhead_ms = 0.0
        self.last_overhead_check = datetime.utcnow()
        
        # Initialize components based on configuration
        self._initialize_components()
    
    async def start(self):
        """Start the debug manager and all enabled components."""
        if self._running:
            return
        
        self._running = True
        
        # Start components
        if self.metrics_collector:
            await self.metrics_collector.start_collection()
        
        if self.alert_manager:
            await self.alert_manager.start()
        
        # Start health monitoring
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        # Log startup
        if self.logger:
            self.logger.info("Debug manager started", components=self._get_enabled_components())
    
    async def stop(self):
        """Stop the debug manager and all components."""
        self._running = False
        
        # Stop background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Stop components
        if self.metrics_collector:
            await self.metrics_collector.stop_collection()
        
        if self.alert_manager:
            await self.alert_manager.stop()
        
        # Log shutdown
        if self.logger:
            self.logger.info("Debug manager stopped")
    
    def get_logger(self) -> Optional[ExtensionLogger]:
        """Get the extension logger."""
        return self.logger
    
    def get_metrics_collector(self) -> Optional[ExtensionMetricsCollector]:
        """Get the metrics collector."""
        return self.metrics_collector
    
    def get_error_tracker(self) -> Optional[ExtensionErrorTracker]:
        """Get the error tracker."""
        return self.error_tracker
    
    def get_profiler(self) -> Optional[ExtensionProfiler]:
        """Get the profiler."""
        return self.profiler
    
    def get_tracer(self) -> Optional[ExtensionTracer]:
        """Get the tracer."""
        return self.tracer
    
    def get_alert_manager(self) -> Optional[ExtensionAlertManager]:
        """Get the alert manager."""
        return self.alert_manager
    
    def start_debug_session(
        self,
        session_id: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start a new debug session."""
        if session_id is None:
            session_id = f"debug_{int(datetime.utcnow().timestamp())}"
        
        if session_id in self.active_sessions:
            raise ValueError(f"Debug session {session_id} already active")
        
        session = DebugSession(
            id=session_id,
            extension_id=self.extension_id,
            extension_name=self.extension_name,
            start_time=datetime.utcnow(),
            configuration=configuration or {}
        )
        
        self.active_sessions[session_id] = session
        
        # Start profiling if requested
        if configuration and configuration.get('enable_profiling') and self.profiler:
            self.profiler.start_session(
                session_id=f"profile_{session_id}",
                profile_memory=configuration.get('profile_memory', True),
                profile_cpu=configuration.get('profile_cpu', True),
                enable_cprofile=configuration.get('enable_cprofile', False)
            )
        
        # Start tracing if requested
        if configuration and configuration.get('enable_tracing') and self.tracer:
            self.tracer.start_trace(f"debug_session_{session_id}")
        
        if self.logger:
            self.logger.info(f"Debug session started", session_id=session_id)
        
        return session_id
    
    def stop_debug_session(self, session_id: str) -> Optional[DebugSession]:
        """Stop a debug session and return collected data."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        session.end_time = datetime.utcnow()
        session.status = "completed"
        
        # Collect data from components
        collected_data = {}
        
        # Collect logs
        if self.logger:
            logs = self.logger.get_logs(limit=1000)
            collected_data['logs'] = [log.to_dict() for log in logs]
        
        # Collect metrics
        if self.metrics_collector:
            since = session.start_time
            metrics = self.metrics_collector.get_metrics(since=since)
            collected_data['metrics'] = [m.to_dict() for m in metrics]
        
        # Collect errors
        if self.error_tracker:
            errors = self.error_tracker.get_errors(since=session.start_time)
            collected_data['errors'] = [e.to_dict() for e in errors]
        
        # Collect profiling data
        if self.profiler:
            try:
                profile_session = self.profiler.stop_session(f"profile_{session_id}")
                collected_data['profiling'] = {
                    'function_profiles': {
                        name: {
                            'calls': profile.call_count,
                            'total_time': profile.total_time,
                            'avg_time': profile.average_time,
                            'avg_memory': profile.average_memory
                        }
                        for name, profile in profile_session.function_profiles.items()
                    },
                    'memory_snapshots': profile_session.memory_snapshots,
                    'cpu_samples': profile_session.cpu_samples
                }
            except Exception:
                pass
        
        # Collect tracing data
        if self.tracer:
            trace_stats = self.tracer.get_trace_statistics()
            collected_data['tracing'] = trace_stats
        
        session.collected_data = collected_data
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        if self.logger:
            self.logger.info(f"Debug session completed", session_id=session_id)
        
        return session
    
    def add_log_entry(self, log_entry: LogEntry):
        """Add a log entry (called by logger)."""
        # Check for error patterns
        if self.error_tracker and log_entry.level.value in ['error', 'critical']:
            self.error_tracker.record_error(
                error_type=log_entry.level.value,
                error_message=log_entry.message,
                stack_trace=log_entry.stack_trace or "",
                context=log_entry.metadata,
                correlation_id=log_entry.correlation_id,
                user_id=log_entry.user_id,
                tenant_id=log_entry.tenant_id
            )
    
    def add_error_record(self, error_record: ErrorRecord):
        """Add an error record (called by error tracker)."""
        # Generate alert for critical errors
        if self.alert_manager and error_record.error_type in ['CriticalError', 'SystemError']:
            asyncio.create_task(self.alert_manager.create_alert(
                alert_type="critical_error",
                severity=AlertSeverity.CRITICAL,
                title=f"Critical Error: {error_record.error_type}",
                message=error_record.error_message,
                metadata={
                    'error_id': error_record.id,
                    'stack_trace': error_record.stack_trace[:500]  # Truncate for alert
                }
            ))
    
    def record_error(
        self,
        extension_id: str,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Record an error (convenience method)."""
        if self.error_tracker:
            self.error_tracker.record_error(
                error_type=error_type,
                error_message=error_message,
                stack_trace="",
                context=context
            )
    
    def create_alert(
        self,
        extension_id: str,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        metric_name: Optional[str] = None,
        current_value: Optional[float] = None,
        threshold_value: Optional[float] = None
    ):
        """Create an alert (convenience method)."""
        if self.alert_manager:
            severity_enum = AlertSeverity(severity.lower())
            asyncio.create_task(self.alert_manager.create_alert(
                alert_type=alert_type,
                severity=severity_enum,
                title=title,
                message=message,
                metric_name=metric_name,
                current_value=current_value,
                threshold_value=threshold_value
            ))
    
    async def run_diagnostics(self) -> ExtensionHealthStatus:
        """Run comprehensive diagnostics and return health status."""
        diagnostics = []
        
        # Check component health
        diagnostics.extend(await self._check_component_health())
        
        # Check resource usage
        diagnostics.extend(await self._check_resource_usage())
        
        # Check error rates
        diagnostics.extend(await self._check_error_rates())
        
        # Check performance
        diagnostics.extend(await self._check_performance())
        
        # Determine overall status
        overall_status = "healthy"
        if any(d.status == "error" for d in diagnostics):
            overall_status = "unhealthy"
        elif any(d.status == "warning" for d in diagnostics):
            overall_status = "degraded"
        
        # Get recent errors and alerts
        recent_errors = []
        if self.error_tracker:
            recent_errors = self.error_tracker.get_errors(
                since=datetime.utcnow() - timedelta(hours=1),
                limit=10
            )
        
        active_alerts = []
        if self.alert_manager:
            active_alerts = self.alert_manager.get_active_alerts()
        
        # Get metrics summary
        metrics_summary = {}
        if self.metrics_collector:
            metrics_summary = self.metrics_collector.get_performance_summary()
        
        health_status = ExtensionHealthStatus(
            extension_id=self.extension_id,
            extension_name=self.extension_name,
            overall_status=overall_status,
            last_check=datetime.utcnow(),
            diagnostics=diagnostics,
            metrics_summary=metrics_summary,
            recent_errors=recent_errors,
            active_alerts=active_alerts
        )
        
        self.health_status = health_status
        self.last_health_check = datetime.utcnow()
        
        return health_status
    
    def get_debug_summary(self) -> Dict[str, Any]:
        """Get comprehensive debug summary."""
        summary = {
            'extension_id': self.extension_id,
            'extension_name': self.extension_name,
            'debug_manager_status': 'running' if self._running else 'stopped',
            'enabled_components': self._get_enabled_components(),
            'active_sessions': len(self.active_sessions),
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'overall_health': self.health_status.overall_status if self.health_status else 'unknown',
            'debug_overhead_ms': self.debug_overhead_ms
        }
        
        # Add component summaries
        if self.logger:
            logs = self.logger.get_logs(limit=1)
            summary['logging'] = {
                'total_logs': len(self.logger.handler.log_entries),
                'last_log': logs[0].to_dict() if logs else None
            }
        
        if self.metrics_collector:
            metrics_summary = self.metrics_collector.get_performance_summary()
            summary['metrics'] = metrics_summary
        
        if self.error_tracker:
            error_analysis = self.error_tracker.get_error_analysis()
            summary['errors'] = {
                'total_errors': error_analysis.total_errors,
                'error_rate': error_analysis.error_rate,
                'unique_errors': error_analysis.unique_errors
            }
        
        if self.alert_manager:
            alert_stats = self.alert_manager.get_alert_statistics()
            summary['alerts'] = alert_stats
        
        if self.tracer:
            trace_stats = self.tracer.get_trace_statistics()
            summary['tracing'] = trace_stats
        
        return summary
    
    def export_debug_data(self, format: str = "json") -> str:
        """Export all debug data."""
        data = {
            'extension_id': self.extension_id,
            'extension_name': self.extension_name,
            'export_timestamp': datetime.utcnow().isoformat(),
            'configuration': {
                'logging_enabled': self.configuration.logging_enabled,
                'metrics_enabled': self.configuration.metrics_enabled,
                'error_tracking_enabled': self.configuration.error_tracking_enabled,
                'profiling_enabled': self.configuration.profiling_enabled,
                'tracing_enabled': self.configuration.tracing_enabled,
                'alerting_enabled': self.configuration.alerting_enabled
            }
        }
        
        # Export logs
        if self.logger:
            logs = self.logger.get_logs()
            data['logs'] = [log.to_dict() for log in logs]
        
        # Export metrics
        if self.metrics_collector:
            metrics = self.metrics_collector.get_metrics()
            data['metrics'] = [m.to_dict() for m in metrics]
        
        # Export errors
        if self.error_tracker:
            errors = self.error_tracker.get_errors()
            data['errors'] = [e.to_dict() for e in errors]
        
        # Export alerts
        if self.alert_manager:
            alerts = self.alert_manager.get_active_alerts()
            resolved_alerts = self.alert_manager.get_resolved_alerts()
            data['alerts'] = {
                'active': [a.to_dict() for a in alerts],
                'resolved': [a.to_dict() for a in resolved_alerts]
            }
        
        # Export traces
        if self.tracer:
            traces = self.tracer.get_completed_traces(limit=100)
            data['traces'] = [
                {
                    'trace_id': trace.trace_id,
                    'start_time': trace.start_time.isoformat(),
                    'duration_ms': trace.duration_ms,
                    'span_tree': trace.get_span_tree()
                }
                for trace in traces
            ]
        
        if format.lower() == "json":
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _initialize_components(self):
        """Initialize debugging components based on configuration."""
        if self.configuration.logging_enabled:
            self.logger = ExtensionLogger(
                self.extension_id,
                self.extension_name,
                debug_manager=self
            )
        
        if self.configuration.metrics_enabled:
            self.metrics_collector = ExtensionMetricsCollector(
                self.extension_id,
                self.extension_name,
                collection_interval=self.configuration.metrics_interval,
                buffer_size=self.configuration.max_metrics,
                debug_manager=self
            )
        
        if self.configuration.error_tracking_enabled:
            self.error_tracker = ExtensionErrorTracker(
                self.extension_id,
                self.extension_name,
                max_errors=self.configuration.max_errors,
                debug_manager=self
            )
        
        if self.configuration.profiling_enabled:
            self.profiler = ExtensionProfiler(
                self.extension_id,
                self.extension_name,
                debug_manager=self
            )
        
        if self.configuration.tracing_enabled:
            self.tracer = ExtensionTracer(
                self.extension_id,
                self.extension_name,
                sampling_rate=self.configuration.sampling_rate,
                max_traces=self.configuration.max_traces,
                debug_manager=self
            )
        
        if self.configuration.alerting_enabled:
            alerting_config = AlertingConfiguration()
            self.alert_manager = ExtensionAlertManager(
                self.extension_id,
                self.extension_name,
                configuration=alerting_config,
                debug_manager=self
            )
    
    def _get_enabled_components(self) -> List[str]:
        """Get list of enabled component names."""
        components = []
        if self.logger:
            components.append("logging")
        if self.metrics_collector:
            components.append("metrics")
        if self.error_tracker:
            components.append("error_tracking")
        if self.profiler:
            components.append("profiling")
        if self.tracer:
            components.append("tracing")
        if self.alert_manager:
            components.append("alerting")
        return components
    
    async def _health_check_loop(self):
        """Background health check loop."""
        while self._running:
            try:
                await self.run_diagnostics()
                await asyncio.sleep(self.configuration.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Health check failed: {e}")
                await asyncio.sleep(self.configuration.health_check_interval)
    
    async def _check_component_health(self) -> List[DiagnosticResult]:
        """Check health of debugging components."""
        diagnostics = []
        
        # Check logger
        if self.logger:
            log_count = len(self.logger.handler.log_entries)
            status = "healthy" if log_count < self.configuration.max_log_entries * 0.9 else "warning"
            diagnostics.append(DiagnosticResult(
                check_name="logger_health",
                status=status,
                message=f"Logger has {log_count} entries",
                details={'log_count': log_count, 'max_logs': self.configuration.max_log_entries}
            ))
        
        # Check metrics collector
        if self.metrics_collector:
            buffer_size = len(self.metrics_collector.buffer.buffer)
            status = "healthy" if buffer_size < self.configuration.max_metrics * 0.9 else "warning"
            diagnostics.append(DiagnosticResult(
                check_name="metrics_collector_health",
                status=status,
                message=f"Metrics collector has {buffer_size} metrics",
                details={'buffer_size': buffer_size, 'max_metrics': self.configuration.max_metrics}
            ))
        
        return diagnostics
    
    async def _check_resource_usage(self) -> List[DiagnosticResult]:
        """Check resource usage."""
        diagnostics = []
        
        if self.metrics_collector:
            resource_usage = self.metrics_collector.get_current_resource_usage()
            
            # Check CPU usage
            cpu_percent = resource_usage.get('cpu_percent', 0)
            cpu_status = "healthy" if cpu_percent < 70 else "warning" if cpu_percent < 90 else "error"
            diagnostics.append(DiagnosticResult(
                check_name="cpu_usage",
                status=cpu_status,
                message=f"CPU usage is {cpu_percent:.1f}%",
                details={'cpu_percent': cpu_percent}
            ))
            
            # Check memory usage
            memory_mb = resource_usage.get('memory_mb', 0)
            memory_status = "healthy" if memory_mb < 500 else "warning" if memory_mb < 1000 else "error"
            diagnostics.append(DiagnosticResult(
                check_name="memory_usage",
                status=memory_status,
                message=f"Memory usage is {memory_mb:.1f}MB",
                details={'memory_mb': memory_mb}
            ))
        
        return diagnostics
    
    async def _check_error_rates(self) -> List[DiagnosticResult]:
        """Check error rates."""
        diagnostics = []
        
        if self.error_tracker:
            recent_errors = self.error_tracker.get_errors(
                since=datetime.utcnow() - timedelta(hours=1)
            )
            
            error_count = len(recent_errors)
            error_status = "healthy" if error_count < 5 else "warning" if error_count < 20 else "error"
            
            diagnostics.append(DiagnosticResult(
                check_name="error_rate",
                status=error_status,
                message=f"{error_count} errors in the last hour",
                details={'error_count': error_count, 'time_window': '1 hour'}
            ))
        
        return diagnostics
    
    async def _check_performance(self) -> List[DiagnosticResult]:
        """Check performance metrics."""
        diagnostics = []
        
        # Check debug overhead
        overhead_percent = (self.debug_overhead_ms / 1000) * 100  # Convert to percentage
        overhead_status = "healthy" if overhead_percent < 2 else "warning" if overhead_percent < 5 else "error"
        
        diagnostics.append(DiagnosticResult(
            check_name="debug_overhead",
            status=overhead_status,
            message=f"Debug overhead is {overhead_percent:.2f}%",
            details={'overhead_ms': self.debug_overhead_ms, 'overhead_percent': overhead_percent}
        ))
        
        return diagnostics