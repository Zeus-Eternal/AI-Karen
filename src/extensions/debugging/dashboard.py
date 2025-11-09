"""
Extension Debug Dashboard

Provides a comprehensive dashboard interface for extension debugging and monitoring
with real-time data visualization and interactive debugging tools.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from .debug_manager import ExtensionDebugManager
from .models import LogLevel, AlertSeverity


class ExtensionDebugDashboard:
    """
    Dashboard interface for extension debugging and monitoring.
    
    Features:
    - Real-time metrics visualization
    - Log streaming and filtering
    - Error analysis and patterns
    - Performance monitoring
    - Alert management
    - Debug session management
    """
    
    def __init__(self, debug_manager: ExtensionDebugManager):
        self.debug_manager = debug_manager
        self.extension_id = debug_manager.extension_id
        self.extension_name = debug_manager.extension_name
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        return {
            'overview': self.get_overview_data(),
            'metrics': self.get_metrics_data(),
            'logs': self.get_logs_data(),
            'errors': self.get_errors_data(),
            'alerts': self.get_alerts_data(),
            'performance': self.get_performance_data(),
            'health': self.get_health_data(),
            'sessions': self.get_sessions_data()
        }
    
    def get_overview_data(self) -> Dict[str, Any]:
        """Get overview dashboard data."""
        summary = self.debug_manager.get_debug_summary()
        
        # Calculate uptime
        uptime_seconds = 0
        if self.debug_manager._running and self.debug_manager.last_health_check:
            uptime_seconds = (datetime.utcnow() - self.debug_manager.last_health_check).total_seconds()
        
        return {
            'extension_id': self.extension_id,
            'extension_name': self.extension_name,
            'status': 'running' if self.debug_manager._running else 'stopped',
            'uptime_seconds': uptime_seconds,
            'enabled_components': summary.get('enabled_components', []),
            'overall_health': summary.get('overall_health', 'unknown'),
            'active_sessions': summary.get('active_sessions', 0),
            'debug_overhead_ms': summary.get('debug_overhead_ms', 0),
            'last_health_check': summary.get('last_health_check')
        }
    
    def get_metrics_data(self, time_window_hours: int = 1) -> Dict[str, Any]:
        """Get metrics dashboard data."""
        if not self.debug_manager.metrics_collector:
            return {'error': 'Metrics collection not enabled'}
        
        since = datetime.utcnow() - timedelta(hours=time_window_hours)
        metrics = self.debug_manager.metrics_collector.get_metrics(since=since)
        
        # Group metrics by name
        metrics_by_name = {}
        for metric in metrics:
            if metric.metric_name not in metrics_by_name:
                metrics_by_name[metric.metric_name] = []
            metrics_by_name[metric.metric_name].append({
                'timestamp': metric.timestamp.isoformat(),
                'value': metric.value,
                'unit': metric.unit
            })
        
        # Get current resource usage
        current_resources = self.debug_manager.metrics_collector.get_current_resource_usage()
        
        # Get performance summary
        performance_summary = self.debug_manager.metrics_collector.get_performance_summary()
        
        return {
            'time_window_hours': time_window_hours,
            'metrics_by_name': metrics_by_name,
            'current_resources': current_resources,
            'performance_summary': performance_summary,
            'total_metrics': len(metrics)
        }
    
    def get_logs_data(
        self,
        limit: int = 100,
        level: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get logs dashboard data."""
        if not self.debug_manager.logger:
            return {'error': 'Logging not enabled'}
        
        # Convert level string to enum
        log_level = None
        if level:
            try:
                log_level = LogLevel(level.lower())
            except ValueError:
                pass
        
        logs = self.debug_manager.logger.get_logs(level=log_level, limit=limit)
        
        # Filter by search term
        if search:
            search_lower = search.lower()
            logs = [
                log for log in logs
                if search_lower in log.message.lower() or search_lower in log.source.lower()
            ]
        
        # Group logs by level
        logs_by_level = {}
        for log in logs:
            level_name = log.level.value
            if level_name not in logs_by_level:
                logs_by_level[level_name] = 0
            logs_by_level[level_name] += 1
        
        # Get recent log sources
        recent_sources = list(set(log.source for log in logs[-50:]))  # Last 50 logs
        
        return {
            'logs': [log.to_dict() for log in logs],
            'total_logs': len(logs),
            'logs_by_level': logs_by_level,
            'recent_sources': recent_sources,
            'filters': {
                'level': level,
                'search': search,
                'limit': limit
            }
        }
    
    def get_errors_data(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get errors dashboard data."""
        if not self.debug_manager.error_tracker:
            return {'error': 'Error tracking not enabled'}
        
        since = datetime.utcnow() - timedelta(hours=time_window_hours)
        errors = self.debug_manager.error_tracker.get_errors(since=since)
        
        # Get error analysis
        error_analysis = self.debug_manager.error_tracker.get_error_analysis(
            time_window=timedelta(hours=time_window_hours)
        )
        
        # Get error patterns
        patterns = self.debug_manager.error_tracker.get_error_patterns()
        
        # Recent unresolved errors
        unresolved_errors = [e for e in errors if not e.resolved]
        
        return {
            'time_window_hours': time_window_hours,
            'total_errors': error_analysis.total_errors,
            'unique_errors': error_analysis.unique_errors,
            'error_rate': error_analysis.error_rate,
            'top_error_types': error_analysis.top_error_types,
            'error_trends': error_analysis.error_trends,
            'patterns': [
                {
                    'pattern_id': p.pattern_id,
                    'error_type': p.error_type,
                    'message_pattern': p.message_pattern,
                    'occurrences': p.occurrences,
                    'first_seen': p.first_seen.isoformat(),
                    'last_seen': p.last_seen.isoformat(),
                    'resolution_suggestions': p.resolution_suggestions
                }
                for p in patterns
            ],
            'recent_errors': [e.to_dict() for e in errors[-20:]],  # Last 20 errors
            'unresolved_count': len(unresolved_errors),
            'recommendations': error_analysis.recommendations
        }
    
    def get_alerts_data(self) -> Dict[str, Any]:
        """Get alerts dashboard data."""
        if not self.debug_manager.alert_manager:
            return {'error': 'Alerting not enabled'}
        
        # Get active alerts
        active_alerts = self.debug_manager.alert_manager.get_active_alerts()
        
        # Get resolved alerts
        resolved_alerts = self.debug_manager.alert_manager.get_resolved_alerts(limit=50)
        
        # Get alert statistics
        alert_stats = self.debug_manager.alert_manager.get_alert_statistics()
        
        # Group alerts by severity
        alerts_by_severity = {}
        for alert in active_alerts:
            severity = alert.severity.value
            if severity not in alerts_by_severity:
                alerts_by_severity[severity] = []
            alerts_by_severity[severity].append(alert.to_dict())
        
        return {
            'active_alerts': [a.to_dict() for a in active_alerts],
            'resolved_alerts': [a.to_dict() for a in resolved_alerts],
            'alerts_by_severity': alerts_by_severity,
            'statistics': alert_stats,
            'critical_count': len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
            'high_count': len([a for a in active_alerts if a.severity == AlertSeverity.HIGH])
        }
    
    def get_performance_data(self) -> Dict[str, Any]:
        """Get performance dashboard data."""
        performance_data = {}
        
        # Profiling data
        if self.debug_manager.profiler:
            performance_summary = self.debug_manager.profiler.get_performance_summary()
            bottlenecks = self.debug_manager.profiler.get_bottlenecks(top_n=10)
            memory_analysis = self.debug_manager.profiler.get_memory_analysis()
            cpu_analysis = self.debug_manager.profiler.get_cpu_analysis()
            
            performance_data['profiling'] = {
                'summary': performance_summary,
                'bottlenecks': bottlenecks,
                'memory_analysis': memory_analysis,
                'cpu_analysis': cpu_analysis
            }
        
        # Tracing data
        if self.debug_manager.tracer:
            trace_stats = self.debug_manager.tracer.get_trace_statistics()
            performance_analysis = self.debug_manager.tracer.analyze_performance()
            
            performance_data['tracing'] = {
                'statistics': trace_stats,
                'performance_analysis': performance_analysis
            }
        
        return performance_data
    
    def get_health_data(self) -> Dict[str, Any]:
        """Get health dashboard data."""
        if not self.debug_manager.health_status:
            return {'error': 'No health data available'}
        
        health_status = self.debug_manager.health_status
        
        return {
            'overall_status': health_status.overall_status,
            'last_check': health_status.last_check.isoformat(),
            'diagnostics': [d.to_dict() for d in health_status.diagnostics],
            'metrics_summary': health_status.metrics_summary,
            'recent_errors_count': len(health_status.recent_errors),
            'active_alerts_count': len(health_status.active_alerts),
            'health_score': self._calculate_health_score(health_status)
        }
    
    def get_sessions_data(self) -> Dict[str, Any]:
        """Get debug sessions data."""
        active_sessions = []
        for session in self.debug_manager.active_sessions.values():
            session_data = session.to_dict()
            session_data['duration_seconds'] = (
                datetime.utcnow() - session.start_time
            ).total_seconds()
            active_sessions.append(session_data)
        
        return {
            'active_sessions': active_sessions,
            'total_active': len(active_sessions)
        }
    
    def get_real_time_metrics(self, metric_names: List[str]) -> Dict[str, Any]:
        """Get real-time metrics for specified metric names."""
        if not self.debug_manager.metrics_collector:
            return {'error': 'Metrics collection not enabled'}
        
        current_time = datetime.utcnow()
        metrics_data = {}
        
        for metric_name in metric_names:
            # Get last 10 minutes of data
            since = current_time - timedelta(minutes=10)
            metrics = self.debug_manager.metrics_collector.get_metrics(
                metric_name=metric_name,
                since=since
            )
            
            if metrics:
                latest_metric = metrics[-1]
                metrics_data[metric_name] = {
                    'current_value': latest_metric.value,
                    'unit': latest_metric.unit,
                    'timestamp': latest_metric.timestamp.isoformat(),
                    'trend': self._calculate_trend(metrics)
                }
            else:
                metrics_data[metric_name] = {
                    'current_value': 0,
                    'unit': '',
                    'timestamp': current_time.isoformat(),
                    'trend': 'stable'
                }
        
        return {
            'timestamp': current_time.isoformat(),
            'metrics': metrics_data
        }
    
    def get_log_stream(self, since: Optional[datetime] = None, limit: int = 50) -> Dict[str, Any]:
        """Get streaming log data."""
        if not self.debug_manager.logger:
            return {'error': 'Logging not enabled'}
        
        if since is None:
            since = datetime.utcnow() - timedelta(minutes=5)
        
        all_logs = self.debug_manager.logger.get_logs(limit=1000)
        recent_logs = [log for log in all_logs if log.timestamp >= since]
        
        # Sort by timestamp and limit
        recent_logs.sort(key=lambda x: x.timestamp, reverse=True)
        recent_logs = recent_logs[:limit]
        
        return {
            'logs': [log.to_dict() for log in recent_logs],
            'total_count': len(recent_logs),
            'since': since.isoformat(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def search_logs(
        self,
        query: str,
        level: Optional[str] = None,
        source: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Search logs with advanced filtering."""
        if not self.debug_manager.logger:
            return {'error': 'Logging not enabled'}
        
        # Get all logs
        all_logs = self.debug_manager.logger.get_logs(limit=10000)
        
        # Apply filters
        filtered_logs = all_logs
        
        if since:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= since]
        
        if level:
            try:
                log_level = LogLevel(level.lower())
                filtered_logs = [log for log in filtered_logs if log.level == log_level]
            except ValueError:
                pass
        
        if source:
            filtered_logs = [log for log in filtered_logs if source.lower() in log.source.lower()]
        
        if query:
            query_lower = query.lower()
            filtered_logs = [
                log for log in filtered_logs
                if (query_lower in log.message.lower() or
                    query_lower in log.source.lower() or
                    any(query_lower in str(v).lower() for v in log.metadata.values()))
            ]
        
        # Sort and limit
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
        filtered_logs = filtered_logs[:limit]
        
        return {
            'logs': [log.to_dict() for log in filtered_logs],
            'total_count': len(filtered_logs),
            'query': query,
            'filters': {
                'level': level,
                'source': source,
                'since': since.isoformat() if since else None
            }
        }
    
    def export_dashboard_data(self, format: str = "json") -> str:
        """Export dashboard data."""
        dashboard_data = self.get_dashboard_data()
        
        if format.lower() == "json":
            return json.dumps(dashboard_data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _calculate_health_score(self, health_status) -> int:
        """Calculate a health score from 0-100."""
        if health_status.overall_status == "healthy":
            base_score = 100
        elif health_status.overall_status == "degraded":
            base_score = 70
        else:  # unhealthy
            base_score = 30
        
        # Adjust based on diagnostics
        error_count = len([d for d in health_status.diagnostics if d.status == "error"])
        warning_count = len([d for d in health_status.diagnostics if d.status == "warning"])
        
        # Deduct points for issues
        score = base_score - (error_count * 15) - (warning_count * 5)
        
        # Ensure score is between 0 and 100
        return max(0, min(100, score))
    
    def _calculate_trend(self, metrics: List) -> str:
        """Calculate trend from metrics data."""
        if len(metrics) < 2:
            return "stable"
        
        # Compare first and last values
        first_value = metrics[0].value
        last_value = metrics[-1].value
        
        change_percent = ((last_value - first_value) / first_value) * 100 if first_value != 0 else 0
        
        if change_percent > 10:
            return "increasing"
        elif change_percent < -10:
            return "decreasing"
        else:
            return "stable"